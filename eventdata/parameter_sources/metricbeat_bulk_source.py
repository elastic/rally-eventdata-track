import logging
import random
import uuid
import time
import hashlib
from eventdata.parameter_sources.randomevent import RandomEvent

logger = logging.getLogger("track.eventdata")


class MetricbeatBulkSource:
    """
    Generates a bulk indexing request for Metyricbeat data.

    It expects the parameter hash to contain the following keys:
        "bulk-size"            -    Integer indicating events generated per bulk request. Defaults to 1000.
        "index"                -    Name of index, index prefix or alias documents should be indexed into. The index name
                                    can be made to generate time based indices by including date formatting in the name.
                                    'test-<yyyy>-<mm>-<dd>-<hh>' will generate an hourly index. (mandatory)
        "starting_point"       -    String specifying the starting point for event time generation. It supports absolute or
                                    relative values as follows:
                                        'now'                 - Always evaluated to the current timestamp at time of generation
                                        'now-1h'              - Offset to the current timestamp. Consists of a number and 
                                                                either m (minutes), h (hours) or d (days).
                                        '2017-02-20 20:12:32' - Exact timestamp.
                                        '2017-02-20'          - Date. Time will be assumed to be 00:00:00.
                                    If a relative starting point (based on now) is provided, this will be used for generation.
                                    In the case an exact timestamp is provided as starting point, the difference to now will
                                    be calculated when the generation starts and this will be used as an offset for all events. 
                                    If an interval is provided by also specifying an end_point, the range will be calculated for 
                                    each bulk request and each event will be assigned a random timestamp withion this range.
                                    starting point. Defaults to 'now'.
        "end_point"            -    String specifying the end point for event time generation. It supports absolute or
                                    relative values as follows:
                                        'now'                 - Always evaluated to the current timestamp at time of generation
                                        'now-1h'              - Offset to the current timestamp. Consists of a number and 
                                                                either m (minutes), h (hours) or d (days).
                                        '2017-02-20 20:12:32' - Exact timestamp.
                                        '2017-02-20'          - Date. Time will be assumed to be 00:00:00.
                                    When specified, the event timestamp will be generated randomly with in the interval defined 
                                    by the starting_point and end_point parameters. If end_poiunt < starting_point, they will be 
                                    swapped. 
        "acceleration_factor"  -    This factor only applies when an exact timestamp or date has been provided as starting point 
                                    and no end_point has been defined. It allows the time progression in the timestamp calculation 
                                    to be altered. A value larger than 1 will accelerate generation and a value lower than 1 will 
                                    slow it down. If a task is set up to run indexing for one hour with a fixed starting point of 
                                    '2016-12-20 20:12:32' and an acceleration factor of 2.0, events will be generated in timestamp 
                                    sequence covering a 2-hour window, '2017-02-20 20:12:32' to '2017-02-20 22:12:32' (approximately).
        "id_type"              -    Type of document id to use for generated documents. Defaults to `auto`.
                                        auto         - Do not explicitly set id and let Elasticsearch assign automatically.
                                        uuid         - Assign a UUID4 id to each document.
                                        epoch_uuid   - Assign a UUIO4 identifier prefixed with the hex representation of the current 
                                                       timestamp.
                                        sha1         - SHA1 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                        sha256       - SHA256 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                        sha384       - SHA384 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
                                        sha512       - SHA512 hash of UUID in hex representation. (Note: Generating this type of id can be CPU intensive)
        "id_delay_probability" -    If id_type is set to `epoch_uuid` this parameter determnines the probability will be set in the 
                                    past. This can be used to simulate a portion of the events arriving delayed. Must be in range [0.0, 1.0].
                                    Defaults to 0.0.
        "id_delay_secs".       -    If an event is delayed, this number of seconds will be deducted from the current timestamp.
    """
    def __init__(self, track, params, **kwargs):
        self._indices = track.indices
        self._params = params
        self._params = params
        self._randomevent = RandomEvent(params)

        self._bulk_size = 1000
        if 'bulk-size' in params.keys():
            self._bulk_size = params['bulk-size']

        self._id_type = "auto"
        if 'id_type' in params.keys():
            if params['id_type'] in ['auto', 'uuid', 'epoch_uuid', 'sha1', 'sha256', 'sha384', 'sha512']:
                self._id_type = params['id_type']
            else:
                logger.warning("[bulk] Invalid id_type ({}) specified. Will use default.".format(params['id_type']))

        if self._id_type == "epoch_uuid":
            if 'id_delay_probability' in params.keys():
                self._id_delay_probability = float(params['id_delay_probability'])
            else:
                self._id_delay_probability = 0.0

            if 'id_delay_secs' in params.keys():
                self._id_delay_secs = int(params['id_delay_secs'])
            else:
                self._id_delay_secs = 0

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
        seed = partition_index * self._params["seed"] if "seed" in self._params else None
        random.seed(seed)   
        return self

    def size(self):
        return 1

    def params(self):
        # Build bulk array
        bulk_array = []
        for x in range(0, self._bulk_size):
            evt, idx, typ = self._randomevent.generate_event()

            if self._id_type == 'auto':
                bulk_array.append('{"index": {"_index": "%s", "_type": "doc"}}"' % (idx))
            else:
                if self._id_type == 'uuid':
                    docid = self.__get_uuid()
                elif self._id_type == 'sha1':
                    docid = hashlib.sha1(self.__get_uuid().encode()).hexdigest()
                elif self._id_type == 'sha256':
                    docid = hashlib.sha256(self.__get_uuid().encode()).hexdigest()
                elif self._id_type == 'sha384':
                    docid = hashlib.sha384(self.__get_uuid().encode()).hexdigest()
                elif self._id_type == 'sha512':
                    docid = hashlib.sha512(self.__get_uuid().encode()).hexdigest()
                else:
                    docid = self.__get_epoch_uuid()
                
                bulk_array.append('{"index": {"_index": "%s", "_type": "doc", "_id": "%s"}}"' % (idx, docid))

            bulk_array.append(evt)

        response = { "body": "\n".join(bulk_array), "action-metadata-present": True, "bulk-size": self._bulk_size }

        if "pipeline" in self._params.keys():
            response["pipeline"] = self._params["pipeline"]

        return response

    def __get_uuid(self):
        u = str(uuid.uuid4())
        return u[0:8] + u[9:13] + u[14:18] + u[19:23] + u[24:36]

    def __get_epoch_uuid(self):
        u = self.__get_uuid()
        ts = int(time.time())

        if(self._id_delay_probability > 0 and self._id_delay_probability < random.random()):
            ts = ts - self._id_delay_secs

        return hex(ts)[2:10] + u

