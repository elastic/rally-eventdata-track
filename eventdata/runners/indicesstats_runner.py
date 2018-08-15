import elasticsearch
import json

import logging

logger = logging.getLogger("track.eventdata")

def indicesstats(es, params):
    """
    Retrieves index stats for an index or index pattern.

    It expects the parameter hash to contain the following keys:
        "index_pattern" - Index pattern that storage statistics are retrieved for. Defaults to "elasticlogs-*".
    """
    if 'index_pattern' not in params:
        index_pattern = 'elasticlogs-*'
    else:
        index_pattern = params['index_pattern']

    response = {
        "weight": 1,
        "unit": "ops",
        "index_pattern": index_pattern
    }

    try:
        result = es.indices.stats(index=index_pattern, metric='store,docs,segments')

        if result['_all']:
            a = result['_all']

            if a['primaries']['docs']['count']:
                response['primary_doc_count'] = a['primaries']['docs']['count']

            if a['total']['docs']['count']:
                response['total_doc_count'] = a['total']['docs']['count']

            if a['primaries']['store']['size_in_bytes']:
                response['primary_size_bytes'] = a['primaries']['store']['size_in_bytes']

            if a['total']['store']['size_in_bytes']:
                response['total_size_bytes'] = a['total']['store']['size_in_bytes']

            if a['primaries']['segments']['count']:
                response['primary_segment_count'] = a['primaries']['segments']['count']

            if a['total']['segments']['count']:
                response['total_segment_count'] = a['total']['segments']['count']

            if a['primaries']['segments']['memory_in_bytes']:
                response['primary_segments_memory_in_bytes'] = a['primaries']['segments']['memory_in_bytes']

            if a['total']['segments']['memory_in_bytes']:
                response['total_segment_memory_in_bytes'] = a['total']['segments']['memory_in_bytes']

            if a['primaries']['segments']['terms_memory_in_bytes']:
                response['primary_segment_terms_memory_in_bytes'] = a['primaries']['segments']['terms_memory_in_bytes']

            if a['total']['segments']['terms_memory_in_bytes']:
                response['total_segment_terms_memory_in_bytes'] = a['total']['segments']['terms_memory_in_bytes']

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Indices stats for {} => {}".format(index_pattern, json.dumps(result)))
    except elasticsearch.TransportError as e:
        logger.info("[indicesstats_runner] Error: {}".format(e))

    return response
