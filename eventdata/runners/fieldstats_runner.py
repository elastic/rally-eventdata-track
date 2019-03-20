from eventdata.utils import globals as gs
import logging

logger = logging.getLogger("track.eventdata")

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

def fieldstats(es, params):
    """
    Looks up minimum and maximum values for a specified field for an index pattern and stores
    this inform ation in a globval variable that can be accessed by other componenets of the track.
    It expects the parameter hash to contain the following keys:
        "index_pattern" - Index pattern statistics are retrieved for. Defaults to "filebeat-*".
        "fieldname" - Field to extract statistics for. Defaults to "@timestamp".
    """
    if 'index_pattern' not in params:
        params['index_pattern'] = 'elasticlogs-*'
    
    if 'fieldname' not in params:
        params['fieldname'] = '@timestamp'

    ignore_throttled = params.get('ignore_throttled', True)

    if ignore_throttled:
        result = es.search(index=params['index_pattern'], body={"query": {"match_all": {}},"aggs" : {"maxval" : { "max" : { "field" : params['fieldname'] } },"minval" : { "min" : { "field" : params['fieldname'] } }},"size":0})
    else:
        result = es.search(index=params['index_pattern'], body={"query": {"match_all": {}},"aggs" : {"maxval" : { "max" : { "field" : params['fieldname'] } },"minval" : { "min" : { "field" : params['fieldname'] } }},"size":0}, params={'ignore_throttled': 'false'})

    hits = result['hits']['total']
    # ES 7.0+
    if isinstance(hits, dict):
        total_hits = hits["value"]
    else:
        total_hits = hits

    if total_hits > 0:
        key = "{}_{}".format(params['index_pattern'], params['fieldname']);
        gs.global_fieldstats[key] = {'max': int(result['aggregations']['maxval']['value']), 'min': int(result['aggregations']['minval']['value'])};

        logger.info("[fieldstats] Identified statistics for field '{}' in '{}'. Min: {}, Max: {}".format(params['fieldname'], params['index_pattern'], int(result['aggregations']['minval']['value']), int(result['aggregations']['maxval']['value'])))
    else:
        raise ParameterError("No matching data found for field '{}' in pattern '{}'.".format(params['fieldname'], params['index_pattern']));
