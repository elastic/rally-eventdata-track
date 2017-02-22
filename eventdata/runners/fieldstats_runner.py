import datetime
import os
import json
import sys

import logging

logger = logging.getLogger("track.elasticlogs")

epoch = datetime.datetime.utcfromtimestamp(0)

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ParameterError(Error):
    """Exception raised for parameter errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

def __perform_field_stats_lookup(es, index_pattern, field):
    result = es.field_stats(index=index_pattern, fields=field)
    min_ts = sys.maxsize
    max_ts = 0

    for idx in result['indices'].keys():
        if result['indices'][idx]['fields'][field]['min_value'] < min_ts:
            min_ts = result['indices'][idx]['fields'][field]['min_value']

        if result['indices'][idx]['fields'][field]['max_value'] > max_ts:
            max_ts = result['indices'][idx]['fields'][field]['max_value']

    return min_ts, max_ts

def __write_to_file(id, data):
    dir_name = "{}/.rally/temp".format(os.environ['HOME'])
    file_name = "{}/.rally/temp/{}.json".format(os.environ['HOME'], id)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    file = open(file_name, 'w+')

    file.write(data)

def fieldstats(es, params):
    """
    Creates a file with variables in the Rally temporary directory, ~/.rally/temp.
    Populates a set of environment variables with statistics around the data matching an index pattern
    for use with the Kibana parameter source. Window definition and length can be defined relative the
    size of the time period covered by the index pattern.

    It expects the parameter hash to contain the following keys:
        "fieldstats_id" - String prefix representing this set of variables. Defaults to "ELASTICLOGS".
        "index_pattern" - Index pattern statistics are retrieved for. Defaults to "elasticlogs-*".
        "timestamp_field" - Timestamp field to extract field stats for. Defaults to @timestamp.

    Based on this the field stats API is called for the index pattern and the highest and lowest timestamp covered 
    by the index patterns for the @timestamp field is retrieved. A JSON document with the field "index_pattern", 
    "ts_min_ms" and "ts_max_ms" will be written to a file named <id>.json in the Rally temporary directory.
    """
    if 'fieldstats_id' not in params:
        params['fieldstats_id'] = 'ELASTICLOGS'
    
    if 'index_pattern' not in params:
        params['index_pattern'] = 'elasticlogs-*'
    
    if 'timestamp_field' not in params:
        params['timestamp_field'] = '@timestamp'

    min_ts, max_ts = __perform_field_stats_lookup(es, params['index_pattern'], params['timestamp_field'])

    result = {'ts_min_ms': min_ts, 'ts_max_ms': max_ts}

    __write_to_file(params['fieldstats_id'], json.dumps(result))

    return 1, "ops"
