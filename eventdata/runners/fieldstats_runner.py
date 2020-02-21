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


from eventdata.utils import globals as gs
import logging


async def fieldstats_async(es, params):
    """
    Looks up minimum and maximum values for a specified field for an index pattern and stores
    this information in a global variable that can be accessed by other components of the track.

    It expects a parameter dictionary with the following keys:

    * index_pattern (mandatory): Index pattern statistics are retrieved for.
    * fieldname (optional): Field to extract statistics for. Defaults to "@timestamp".

    """
    index_pattern = params["index_pattern"]
    field_name = params.get("fieldname", "@timestamp")
    ignore_throttled = params.get("ignore_throttled", True)

    if ignore_throttled:
        query_params = {}
    else:
        query_params = {"ignore_throttled": "false"}

    result = await es.search(index=index_pattern,
                             body={
                                 "query": {
                                     "match_all": {}
                                 },
                                 "size": 0,
                                 "aggs": {
                                     "maxval": {
                                         "max": {
                                             "field": field_name
                                         }
                                     },
                                     "minval": {
                                         "min": {
                                             "field": field_name
                                         }
                                     }
                                 }
                             },
                             params=query_params)

    hits = result["hits"]["total"]
    # ES 7.0+
    if isinstance(hits, dict):
        total_hits = hits["value"]
    else:
        total_hits = hits

    if total_hits > 0:
        key = "{}_{}".format(index_pattern, field_name)
        min_field_value = int(result["aggregations"]["minval"]["value"])
        max_field_value = int(result["aggregations"]["maxval"]["value"])
        gs.global_fieldstats[key] = {
            "max": max_field_value,
            "min": min_field_value
        }
        logger = logging.getLogger("track.eventdata.fieldstats")
        logger.info("Identified statistics for field '%s' in '%s'. Min: %d, Max: %d",
                    field_name, index_pattern, min_field_value, max_field_value)
    else:
        raise AssertionError("No matching data found for field '{}' in pattern '{}'.".format(field_name, index_pattern))


def fieldstats(es, params):
    """
    Looks up minimum and maximum values for a specified field for an index pattern and stores
    this information in a global variable that can be accessed by other components of the track.

    It expects a parameter dictionary with the following keys:

    * index_pattern (mandatory): Index pattern statistics are retrieved for.
    * fieldname (optional): Field to extract statistics for. Defaults to "@timestamp".

    """
    index_pattern = params["index_pattern"]
    field_name = params.get("fieldname", "@timestamp")
    ignore_throttled = params.get("ignore_throttled", True)

    if ignore_throttled:
        query_params = {}
    else:
        query_params = {"ignore_throttled": "false"}

    result = es.search(index=index_pattern,
                       body={
                           "query": {
                               "match_all": {}
                           },
                           "size": 0,
                           "aggs": {
                               "maxval": {
                                   "max": {
                                       "field": field_name
                                   }
                               },
                               "minval": {
                                   "min": {
                                       "field": field_name
                                   }
                               }
                           }
                       },
                       params=query_params)

    hits = result["hits"]["total"]
    # ES 7.0+
    if isinstance(hits, dict):
        total_hits = hits["value"]
    else:
        total_hits = hits

    if total_hits > 0:
        key = "{}_{}".format(index_pattern, field_name)
        min_field_value = int(result["aggregations"]["minval"]["value"])
        max_field_value = int(result["aggregations"]["maxval"]["value"])
        gs.global_fieldstats[key] = {
            "max": max_field_value,
            "min": min_field_value
        }
        logger = logging.getLogger("track.eventdata.fieldstats")
        logger.info("Identified statistics for field '%s' in '%s'. Min: %d, Max: %d",
                    field_name, index_pattern, min_field_value, max_field_value)
    else:
        raise AssertionError("No matching data found for field '{}' in pattern '{}'.".format(field_name, index_pattern))
