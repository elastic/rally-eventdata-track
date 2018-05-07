import json
import random
import datetime
import calendar
import gzip
import copy
import re
import os
import eventdata.parameter_sources.load_json_file as load_json_file
from eventdata.parameter_sources.timeutils import TimestampStructGenerator

import logging

logger = logging.getLogger("track.elasticlogs")

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ConfigurationError(Error):
    """Exception raised for parameter errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class SampleBasedBulkSource:
    """
    Generates a bulk indexing request based on records in a sample file.

    It expects the parameter hash to contain the following keys:
        "bulk-size"            -    Integer indicating events generated per bulk request. Defaults to 1000.
        "index"                -    Name of index, index prefix or alias documents should be indexed into. (mandatory)
        "daily_index".         -    Boolean indicating if daily indices should be created. If set to true, daily indices 
                                    based on the prefix defined in the index parameter will be created. Defaults to false.
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
        "sample_file"          -    String or list of strings specifying the foll paths of the files to read and use as samples for
                                    when generating data. Files can contain either a serialized JSON array of documents or multiple
                                    full JSON documents on individual lines. Files that are gzipped can also be read as long as they
                                    end with a .gz extension. If specified in the event, fields '_index' and '_type' will be extracted
                                    and used to determine index name and document type. The file path may contain environment variables.
        "timestamp_field"      -    String or list of string specifying which existing vbase level fields (nested fields are currently
                                    not supported) are to be replaced by the event timestamp. If no timestamp is to be added or modified,
                                    this parameter can be left out.
    """
    def __init__(self, track, params, **kwargs):
        self._indices = track.indices
        self._params = params
        self._samples = []
        self._next_index = 0

        self._bulk_size = 1000
        if 'bulk-size' in params.keys():
            self._bulk_size = params['bulk-size']

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

        if 'type' not in params.keys():
            t = self._indices[0].types[0]
            self._params['type'] = t if isinstance(t, str) else t.name

        if 'timestamp_field' not in params.keys():
            self._params['timestamp_field'] = []
        else:
            if isinstance(params['timestamp_field'], list):
                self._timestamp_field = params['timestamp_field']
            else:
                self._timestamp_field = [params['timestamp_field']]

        if 'sample_file' not in params.keys():
            raise ConfigurationError('Sample file(s) not supplied through the sample_file configuration parameter.')
        else:
            if isinstance(params['sample_file'], list):
                self._params['sample_file'] = params['sample_file']
            else:
                self._params['sample_file'] = [params['sample_file']]

        records = load_json_file.load_data_files(self._params['sample_file'])

        logger.info("[sample_based_bulk] {} samples loaded.".format(len(records)))

        for rec in records:
            sample = {}

            if '_type' in rec.keys():
                sample['type'] = rec['_type']
                rec.pop('_type', None)

            if '_index' in rec.keys():
                sample['index'] = rec['_index']
                rec.pop('_index', None)

            sample['record'] = rec
            self._samples.append(sample)

        self._index = 'logs'
        self._index_pattern = False
        if 'index' in params.keys():
            index = re.sub(r'{{\s*yyyy\s*}}', '{ts[yyyy]}', params['index'], flags=re.IGNORECASE)
            index = re.sub(r'{{\s*yy\s*}}', '{ts[yy]}', index, flags=re.IGNORECASE)
            index = re.sub(r'{{\s*mm\s*}}', '{ts[mm]}', index, flags=re.IGNORECASE)
            index = re.sub(r'{{\s*dd\s*}}', '{ts[dd]}', index, flags=re.IGNORECASE)
            index = re.sub(r'{{\s*hh\s*}}', '{ts[hh]}', index, flags=re.IGNORECASE)
            self._index = index
            self._index_pattern = True

        self._type = 'logs'
        if 'type'  in params.keys():
            self._type = params['type']

        if 'starting_point' in params.keys():
            sp = params['starting_point']
        else:
            sp ="now"

        if 'end_point' in params.keys():
            ep = params['end_point']
            self._timestamp_generator = TimestampStructGenerator.Interval(sp, ep)
        else:
            if 'acceleration_factor' in params.keys():
                af = float(params['acceleration_factor'])
                self._timestamp_generator = TimestampStructGenerator.StartingPoint(sp, af)
            else:
                self._timestamp_generator = TimestampStructGenerator.StartingPoint(sp)

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
            evt, idx, typ = self.__generate_event()
            bulk_array.append({'index': {'_index': idx, '_type': typ}})
            bulk_array.append(evt)

        response = { "body": bulk_array, "action_metadata_present": True, "bulk-size": self._bulk_size }

        if "pipeline" in self._params.keys():
            response["pipeline"] = params["pipeline"]

        return response
    
    def __generate_event(self):
        evt = copy.copy(self._samples[self._next_index]['record'])
        
        if 'index' in self._samples[self._next_index].keys() or len(self._timestamp_field) > 0:
            timestruct = self._timestamp_generator.generate_timestamp_struct()

        if 'index' in self._samples[self._next_index].keys():
            idx = self._samples[self._next_index]['index']
        else:
            idx = self.__generate_index_pattern(timestruct)

        if 'type' in self._samples[self._next_index].keys():
            typ = self._samples[self._next_index]['type']
        else:
            typ = self._type

        for field in self._timestamp_field:
            if field in evt.keys():
                evt[field] = timestruct['iso']

        self._next_index += 1
        
        self._next_index = self._next_index % len(self._samples)

        return evt, idx, typ

    def __generate_index_pattern(self, timestruct):
        if self._index_pattern:
            return self._index.format(ts=timestruct)
        else:
            return self._index
