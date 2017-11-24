import logging
from eventdata.parameter_sources.randomevent import RandomEvent

logger = logging.getLogger("track.elasticlogs")


class ElasticlogsBulkSource:
    """
    Generates a bulk indexing request for elasticlogs data.

    It expects the parameter hash to contain the following keys:
        "bulk-size"            -    Integer indicating events generated per bulk request. Defaults to 1000.
        "index"                -    Name of index, index prefix or alias documents should be indexed into. The index name
                                    can be made to generate time based indices by including date formatting in the name.
                                    'test-<yyyy>-<mm>-<dd>-<hh>' will generate an hourly index. (mandatory)
        "type"                 -    String specifyting the event type. Defaults to type of index specification or if this 
                                    is not present 'logs'.
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
    """
    def __init__(self, indices, params):
        self._indices = indices
        self._params = params
        self._randomevent = RandomEvent(params)

        self._bulk_size = 1000
        if 'bulk-size' in params.keys():
            self._bulk_size = params['bulk-size']

        self._default_index = False
        if 'index' not in params.keys():
            if len(indices) > 1:
                logger.debug("[bulk] More than one index specified in track configuration. Will use the first one ({})".format(indices[0].name))
            else:
                logger.debug("[bulk] Using index specified in track configuration ({})".format(indices[0].name))

            self._params['index'] = indices[0].name
            self._default_index = True

        else:
            logger.debug("[bulk] Index pattern specified in parameters ({}) will be used".format(params['index']))

        if 'type' not in params.keys():
            self._params['type'] = indices[0].types[0].name

    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1

    def params(self):
        # Build bulk array
        bulk_array = []
        for x in range(0, self._bulk_size):
            evt, idx, typ = self._randomevent.generate_event()
            bulk_array.append('{"index": {"_index": "%s", "_type": "%s"}}"' % (idx, typ))
            bulk_array.append(evt)

        response = { "body": "\n".join(bulk_array), "action_metadata_present": True, "bulk-size": self._bulk_size }

        if "pipeline" in self._params.keys():
            response["pipeline"] = self._params["pipeline"]

        return response
