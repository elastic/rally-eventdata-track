import elasticsearch
import json

import logging

logger = logging.getLogger("track.elasticlogs")

BYTES_PER_TB = 1024 * 1024 * 1024 * 1024

def nodestorage(es, params):
    """
    Calculates the total data volume in the cluster as well as average volume per data node.

    It takes no parameters.
    """
    response = {
        "weight": 1,
        "unit": "ops"
    }

    try:
        # get number of data nodes
        node_role_list = es.cat.nodes(h="node.role")

        data_node_count = 0

        for node_role in node_role_list:
            if 'd' in node_role:
                data_node_count += 1

        result = es.indices.stats(index='*', metric='store')
        total_data_size = 0

        if result['_all']:
            if result['_all']['total']['store']['size_in_bytes']:
                total_data_size = result['_all']['total']['store']['size_in_bytes']

        total_data_size_tb = float(total_data_size) / BYTES_PER_TB

        volume_per_data_node = int(total_data_size / data_node_count)
        volume_per_data_node_tb = total_data_size_tb / data_node_count

        response['total_data_volume_bytes'] = total_data_size
        response['total_data_volume_tb'] = total_data_size_tb
        response['average_data_volume_per_node_bytes'] = volume_per_data_node
        response['average_data_volume_per_node_tb'] = volume_per_data_node_tb

    except elasticsearch.TransportError as e:
        logger.info("[nodestorage_runner] Error: {}".format(e))

    return response
