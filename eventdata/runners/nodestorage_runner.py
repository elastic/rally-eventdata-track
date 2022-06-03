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


import elasticsearch

import logging

logger = logging.getLogger("track.eventdata")

BYTES_PER_TB = 1024 * 1024 * 1024 * 1024


async def nodestorage(es, params):
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
        node_role_list = await es.cat.nodes(h="node.role")
        #node_role_list = node_role_list.decode("utf-8")

        data_node_count = 0

        for node_role in node_role_list:
            if node_role in ["c", "d", "f", "h", "w", "s"]:
                data_node_count += 1

        result = await es.indices.stats(index='*', metric='store')
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

    except (elasticsearch.ApiError, elasticsearch.TransportError) as e:
        logger.info("[nodestorage_runner] Error: {}".format(e))

    return response
