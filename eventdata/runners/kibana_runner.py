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


import json

import logging

logger = logging.getLogger("track.eventdata")


def kibana(es, params):
    """
    Simulates Kibana msearch dashboard queries.

    It expects the parameter hash to contain the following keys:
        "body"      - msearch request body representing the Kibana dashboard in the  form of an array of dicts.
        "meta_data" - Dictionary containing meta data information to be carried through into metrics.
    """
    request = params["body"]
    meta_data = params["meta_data"]

    if meta_data["debug"]:
        logger.info("Request:\n=====\n{}\n=====".format(json.dumps(request)))

    visualisations = int(len(request) / 2)

    response = {}

    for key in meta_data.keys():
        response[key] = meta_data[key]

    response["weight"] = 1
    response["unit"] = "ops"
    response["visualisation_count"] = visualisations

    if "pre_filter_shard_size" in meta_data:
        result = es.msearch(body=request, params={"pre_filter_shard_size": meta_data["pre_filter_shard_size"]})
    else:
        result = es.msearch(body=request)

    sum_hits = 0
    max_took = 0
    for r in result["responses"]:
        hits = r["hits"]["total"]
        if isinstance(hits, dict):
            sum_hits += hits["value"]
        else:
            sum_hits += hits
        max_took = max(max_took, r["took"])

    response["took"] = max_took
    response["hits"] = sum_hits

    if meta_data["debug"]:
        for r in result["responses"]:
            # clear hits otherwise we'll spam the log
            r["hits"]["hits"] = []
            r["aggregations"] = {}
        logger.info("Response (excluding specific hits):\n=====\n{}\n=====".format(json.dumps(result)))

    return response
