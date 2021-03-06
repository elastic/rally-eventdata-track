# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


import copy
import logging
import random
from eventdata.parameter_sources.randomevent import RandomEvent

logger = logging.getLogger("track.eventdata")


class ElasticlogsBulkSource:
    """
    Generates a bulk indexing request for elasticlogs data.

    It expects the parameter hash to contain the following keys:
        "bulk-size"                -    Integer indicating events generated per bulk request.
        "index"                    -    Name of index, index prefix or alias documents should be indexed into. The index name
                                        can be made to generate time based indices by including date formatting in the name.
                                        'test-<yyyy>-<mm>-<dd>-<hh>' will generate an hourly index. (mandatory)
        "starting_point"           -    String specifying the starting point for event time generation. It supports absolute or
                                        relative values as follows:
                                            'now'                 - Always evaluated to the current timestamp at time of generation
                                            'now-1h'              - Offset to the current timestamp. Consists of a number and
                                                                    either m (minutes), h (hours) or d (days).
                                            '2017-02-20 20:12:32' - Exact timestamp.
                                            '2017-02-20'          - Date. Time will be assumed to be 00:00:00.
                                        If a relative starting point (based on now) is provided, this will be used for generation.
                                        In the case an exact timestamp is provided as starting point, the difference to now will
                                        be calculated when the generation starts and this will be used as an offset for all events.
                                        Defaults to 'now'.
        "acceleration_factor"  -    This factor allows the time progression in the timestamp calculation to be altered.
                                    A value larger than 1 will accelerate generation and a value lower than 1 will slow
                                    it down. If a task is set up to run indexing for one hour with a fixed starting
                                    point of '2016-12-20 20:12:32' and an acceleration factor of 2.0, events will be
                                    generated in timestamp sequence covering a 2-hour window, '2017-02-20 20:12:32'
                                    to '2017-02-20 22:12:32' (approximately).
        "id_type"                  -    Type of document id to use for generated documents. Defaults to `auto`.
                                            auto         - Do not explicitly set id and let Elasticsearch assign automatically.
                                            seq          - Assign sequentialy incrementing integer ids to each document.
        "id_seq_probability"       -    If set, the probability an existing id will be used to simulate an update.
                                            Applied only when `id_type` is seq.
                                            Defaults to 0.0 which brings no updates. Must be in range [0.0, 1.0].
        "id_seq_low_id_bias"       -    If set, favor low ids with a very high bias. Must be True/False. Default is False.
    """
    def __init__(self, track, params, **kwargs):
        self.infinite = False
        self.orig_args = [track, params, kwargs]
        self._indices = track.indices
        self._params = params
        # we could also do `kwargs.get("random_event", RandomEvent(params))` but that would call the constructor eagerly
        # which we want to avoid because this can cause significant overhead.
        if "random_event" in kwargs:
            self._randomevent = kwargs["random_event"]
        else:
            self._randomevent = RandomEvent(params)

        self._bulk_size = params["bulk-size"]
        self.seq_id = 0

        self._id_type = params.get("id_type", "auto")
        if self._id_type not in ["auto", "seq"]:
            raise AssertionError("The value [{}] is invalid for the parameter [id_type]".format(self._id_type))

        if self._id_type == "seq":
            self._id_seq_probability = float(params.get("id_seq_probability", 0.0))
            self._low_id_bias = str(params.get('id_seq_low_id_bias', False)).lower() == "true"
            if self._low_id_bias:
                logger.info("Will use low id bias for updates")
            else:
                logger.info("Will use uniform distribution for updates")

        self._default_index = False
        if "index" not in params.keys():
            index_name = self._indices[0].name
            if len(self._indices) > 1:
                logger.debug("[bulk] More than one index specified in track configuration. Will use the first one ({})".format(index_name))
            else:
                logger.debug("[bulk] Using index specified in track configuration ({})".format(index_name))

            self._params["index"] = index_name
            self._default_index = True
        else:
            logger.debug("[bulk] Index pattern specified in parameters ({}) will be used".format(params["index"]))

    def partition(self, partition_index, total_partitions):
        if self._params.get("id_type") != "seq":
            seed = partition_index * self._params["seed"] if "seed" in self._params else None
            random.seed(seed)
        new_params = copy.deepcopy(self.orig_args[1])
        new_params["client_id"] = partition_index
        new_params["client_count"] = total_partitions
        return ElasticlogsBulkSource(self.orig_args[0], new_params, **self.orig_args[2])

    @property
    def percent_completed(self):
        # progress is determined either by:
        #
        # * the `time-period` or `iteration` property specified on the corresponding task
        # * `#params()` raising `StopIteration` when `RandomEvent` is exhausted
        return self._randomevent.percent_completed

    def params(self):
        # Build bulk array
        bulk_array = []
        self._randomevent.start_bulk(self._bulk_size)
        for x in range(0, self._bulk_size):
            try:
                evt, idx, typ = self._randomevent.generate_event()
            except StopIteration:
                if len(bulk_array) > 0:
                    # return any remaining items if there are any (otherwise we'd lose the last bulk request)
                    break
                else:
                    # otherwise stop immediately
                    raise

            if self._id_type == "auto":
                bulk_array.append('{"index": {"_index": "%s"}}' % idx)
            else:
                docid = "%s-%d" % (self.__get_seq_id(), self._params["client_id"])
                bulk_array.append('{"index": {"_index": "%s", "_id": "%s"}}' % (idx, docid))

            bulk_array.append(evt)

        response = {
            "body": "\n".join(bulk_array),
            "action-metadata-present": True,
            # the bulk array contains the action-and-metadata line and the actual document
            "bulk-size": len(bulk_array) // 2,
            "unit": "docs"
        }

        if "pipeline" in self._params.keys():
            response["pipeline"] = self._params["pipeline"]

        return response

    def __get_seq_id(self):
        _id = self.seq_id
        if random.uniform(0, 1) < self._id_seq_probability:
            # conflict
            if self._low_id_bias:
                # update; heavily bias towards older ids
                _p = 10
                _min = 0
                _max = _id
                # _p ~> 0: results closer to min, _p >> 0: results closer to max
                _id = _min + (_max - _min) * pow(random.random(), _p)
            else:
                # update; pick id from pure uniform distribution
                _id = random.randint(0, _id-1 if _id > 0 else 0)
        else:
            # new document
            self.__incr_seq_id()

        return "%012d" % _id

    def __incr_seq_id(self):
        self.seq_id += 1
