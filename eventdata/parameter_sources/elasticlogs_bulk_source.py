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
import uuid
import random
import time
import hashlib
import base64
from eventdata.parameter_sources.randomevent import RandomEvent

logger = logging.getLogger("track.eventdata")


class ElasticlogsBulkSource:
    """
    Generates a bulk indexing request for elasticlogs data.

    It expects the parameter hash to contain the following keys:
        "bulk-size"                -    Integer indicating events generated per bulk request. Defaults to 1000.
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
                                            uuid         - Assign a UUID4 id to each document.
                                            epoch_uuid   - Assign a UUIO4 identifier prefixed with the hex representation of the current
                                                           timestamp.
                                            epoch_md5    - Assign a base64 encoded MD5 hash of a UUID prefixed with the hex representation
                                                           of the current timestamp. (Note: Generating this type of id can be CPU intensive)
                                            md5          - MD5 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                            sha1         - SHA1 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                            sha256       - SHA256 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                            sha384       - SHA384 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                            sha512       - SHA512 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
        "id_seq_probability"       -    If set, the probability an existing id will be used to simulate an update.
                                            Applied only when `id_type` is seq.
                                            Defaults to 0.0 which brings no updates. Must be in range [0.0, 1.0].
        "id_seq_low_id_bias"       -    If set, favor low ids with a very high bias. Must be True/False. Default is False.
        "id_delay_probability"     -    If id_type is set to `epoch_uuid` this parameter determnines the probability will be set in the
                                        past. This can be used to simulate a portion of the events arriving delayed. Must be in range [0.0, 1.0].
                                        Defaults to 0.0.
        "id_delay_secs"            -    If an event is delayed, this number of seconds will be deducted from the current timestamp.
    """
    def __init__(self, track, params, **kwargs):
        self.orig_args = [track, params, kwargs]
        self._indices = track.indices
        self._params = params
        self._randomevent = RandomEvent(params)

        self._bulk_size = 1000
        if 'bulk-size' in params.keys():
            self._bulk_size = params['bulk-size']

        self._id_type = "auto"
        self.seq_id = 0

        if 'id_type' in params.keys():
            if params['id_type'] in ['auto', "seq", 'uuid', 'epoch_uuid', 'epoch_md5', 'md5', 'sha1', 'sha256', 'sha384', 'sha512']:
                self._id_type = params['id_type']
            else:
                logger.warning("[bulk] Invalid id_type ({}) specified. Will use default.".format(params['id_type']))

        if self._id_type in ["epoch_uuid", "epoch_md5"]:
            if 'id_delay_probability' in params.keys():
                self._id_delay_probability = float(params['id_delay_probability'])
            else:
                self._id_delay_probability = 0.0

            if 'id_delay_secs' in params.keys():
                self._id_delay_secs = int(params['id_delay_secs'])
            else:
                self._id_delay_secs = 0

        if self._id_type == "seq":
            self._id_seq_probability = float(params['id_seq_probability']) if 'id_seq_probability' in params else 0.0
            self._low_id_bias = str(params.get('id_seq_low_id_bias', False)).lower() == "true"
            if self._low_id_bias:
                logger.info("Will use low id bias for updates")
            else:
                logger.info("Will use uniform distribution for updates")

        self._default_index = False
        if 'index' not in params.keys():
            if len(self._indices) > 1:
                logger.debug("[bulk] More than one index specified in track configuration. Will use the first one ({})".format(self._indices[0].name))
            else:
                logger.debug("[bulk] Using index specified in track configuration ({})".format(self._indices[0].name))

            self._params['index'] = self._indices[0].name
            self._default_index = True

        else:
            logger.debug("[bulk] Index pattern specified in parameters ({}) will be used".format(params['index']))

    def partition(self, partition_index, total_partitions):
        if self._params.get("id_type") != "seq":
            seed = partition_index * self._params["seed"] if "seed" in self._params else None
            random.seed(seed)
        new_params = copy.deepcopy(self.orig_args[1])
        new_params["client_id"] = partition_index
        new_params["client_count"] = total_partitions
        return ElasticlogsBulkSource(self.orig_args[0], new_params, **self.orig_args[2])

    def size(self):
        return 1

    def params(self):
        # Build bulk array
        bulk_array = []
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

            if self._id_type == 'auto':
                bulk_array.append('{"index": {"_index": "%s", "_type": "doc"}}"' % (idx))
            else:
                if self._id_type == 'uuid':
                    docid = self.__get_uuid()
                elif self._id_type == "seq":
                    docid = "%s-%d" % (self.__get_seq_id(), self._params["client_id"])
                elif self._id_type == 'sha1':
                    docid = hashlib.sha1(self.__get_uuid().encode('utf8')).hexdigest()
                elif self._id_type == 'sha256':
                    docid = hashlib.sha256(self.__get_uuid().encode('utf8')).hexdigest()
                elif self._id_type == 'sha384':
                    docid = hashlib.sha384(self.__get_uuid().encode('utf8')).hexdigest()
                elif self._id_type == 'sha512':
                    docid = hashlib.sha512(self.__get_uuid().encode('utf8')).hexdigest()
                elif self._id_type == 'md5':
                    docid = hashlib.md5(self.__get_uuid().encode('utf8')).hexdigest()
                elif self._id_type == 'epoch_md5':
                    docid = self.__get_epoch_md5()
                else:
                    docid = self.__get_epoch_uuid()

                bulk_array.append('{"index": {"_index": "%s", "_type": "doc", "_id": "%s"}}"' % (idx, docid))

            bulk_array.append(evt)

        response = {
            "body": "\n".join(bulk_array),
            "action-metadata-present": True,
            "bulk-size": len(bulk_array)
        }

        if "pipeline" in self._params.keys():
            response["pipeline"] = self._params["pipeline"]

        return response

    def __get_uuid(self):
        return str(uuid.uuid4()).replace('-', '')

    def __get_epoch_uuid(self):
        u = self.__get_uuid()
        ts = int(time.time())

        if 0 < self._id_delay_probability < random.random():
            ts = ts - self._id_delay_secs

        return '{:x}{}'.format(ts, u)

    def __get_epoch_md5(self):
        u = self.__get_uuid()
        md5_str = str(base64.urlsafe_b64encode(hashlib.md5(u.encode('utf8')).digest()))[2:24]
        ts = int(time.time())

        if 0 < self._id_delay_probability < random.random():
            ts = ts - self._id_delay_secs

        return hex(ts)[2:10] + md5_str

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
