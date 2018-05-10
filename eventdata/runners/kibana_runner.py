import elasticsearch
import json
import time

import logging

logger = logging.getLogger("track.eventdata")

def __find_time_interval(query):
    interval_found = False
    ts_min = 0
    ts_max = 0
    ts_format = ""
    field = ""

    if 'query' in query and 'bool' in query['query'] and 'must' in query['query']['bool']:
        query_clauses = query['query']['bool']['must']
        for clause in query_clauses:
            if 'range' in clause.keys():
                range_clause = clause['range']
                for key in range_clause.keys():
                    keys = range_clause[key].keys()
                    if 'lte' in keys and 'gte' in keys and 'format' in keys:
                        field = key
                        ts_min = range_clause[key]['gte']
                        ts_max = range_clause[key]['lte']
                        ts_format = range_clause[key]['format']
                        interval_found = True

    return interval_found, field, ts_min, ts_max, ts_format

def __index_wildcard(index_spec):
    if isinstance(index_spec['index'], str):
        if '*' in index_spec['index']:
            return True, index_spec['index']
        else:
            return False, ""
    elif isinstance(index_spec['index'], list) and len(index_spec['index']) == 1:
        if '*' in index_spec['index'][0]:
            return True, index_spec['index'][0]
        else:
            return False, ""

def __perform_field_stats_lookup(es, index_pattern, field, min_val, max_val, fmt):
    req_body = { 'fields': [field], 'index_constraints': {}}
    req_body['index_constraints'][field] = {'max_value': {'gte': min_val, 'format': fmt}, 'min_value': {'lte': max_val, 'format': fmt}}
    result = es.field_stats(index=index_pattern, level='indices', body=req_body)
    indices_list = list(result['indices'].keys())

    if indices_list == None:
        return [index_pattern]
    else:
        return indices_list

def __get_ms_timestamp():
    return int(round(time.time() * 1000))

def kibana(es, params):
    """
    Simulates Kibana msearch dashboard queries.

    It expects the parameter hash to contain the following keys:
        "body"      - msearch request body representing the Kibana dashboard in the  form of an array of dicts.
        "meta_data" - Dictionary containing meta data information to be carried through into metrics.
    """
    request = params['body']
    tout = 0

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("[kibana_runner] Received request: {}".format(json.dumps(request)))

    visualisations = int(len(request) / 2)

    response = {}

    if 'meta_data' in params:
        meta_data = params['meta_data']
        for key in meta_data.keys():
            response[key] = meta_data[key]

    response['weight'] = 1
    response['unit'] = "ops"
    response['visualisation_count'] = visualisations
    
    try:
        field_stat_start = __get_ms_timestamp()

        # Loops through visualisations and calls field stats API for each one without caching, which is what 
        # Kibana currently does
        cache = {}

        for i in range(0,len(request),2):
            pattern_found, pattern = __index_wildcard(request[i])

            if pattern_found:
                interval_found, field, ts_min, ts_max, ts_fmt = __find_time_interval(request[i + 1])
                key = "{}-{}-{}".format(pattern, ts_min, ts_max)

                if key in list(cache.keys()):
                    request[i]['index'] = cache[key]
                else:
                    request[i]['index'] = __perform_field_stats_lookup(es, pattern, field, ts_min, ts_max, ts_fmt)
                    cache[key] = request[i]['index']

        field_stat_duration = int(__get_ms_timestamp() - field_stat_start)
        response['field_stats_duration_ms'] = field_stat_duration

    except elasticsearch.TransportError as e:
        logger.info("[kibana_runner] Error looking up field stats: {}".format(e))

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("[kibana_runner] Updated request: {}".format(request))

    result = es.msearch(body = request)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("[kibana_runner] response: {}".format(response))

    return response
