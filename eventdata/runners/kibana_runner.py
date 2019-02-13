import elasticsearch
import json
import time

import logging

logger = logging.getLogger("track.eventdata")

def kibana(es, params):
    """
    Simulates Kibana msearch dashboard queries.

    It expects the parameter hash to contain the following keys:
        "body"      - msearch request body representing the Kibana dashboard in the  form of an array of dicts.
        "meta_data" - Dictionary containing meta data information to be carried through into metrics.
    """
    request = params['body']

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

    if "pre_filter_shard_size" in meta_data:
        result = es.msearch(body = request, params = {'pre_filter_shard_size': meta_data['pre_filter_shard_size']})
    else:
        result = es.msearch(body = request)

    if 'debug' in params['meta_data'] and params['meta_data']['debug']:
        logger.info("\n====================\n[kibana_runner] request: {}\n[kibana_runner] result: {}\n====================\n".format(request, result))

    return response
