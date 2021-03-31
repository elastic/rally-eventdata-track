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


def extract_error_details(error_details, data):
    error_data = data.get("error", {})
    error_reason = error_data.get("reason") if isinstance(error_data, dict) else str(error_data)
    if error_data:
        error_details.add((data["status"], error_reason))
    else:
        error_details.add((data["status"], None))


def error_description(error_details):
    description = ""
    for status, reason in error_details:
        if reason:
            description += "HTTP status: %s, message: %s" % (str(status), reason)
        else:
            description += "HTTP status: %s" % str(status)
    return description


async def kibana(es, params):
    """
    Simulates Kibana msearch dashboard queries.

    It expects the parameter hash to contain the following keys:
        "body"      - msearch request body representing the Kibana dashboard in the  form of an array of dicts.
        "params"    - msearch request parameters.
        "meta_data" - Dictionary containing meta data information to be carried through into metrics.
    """
    request = params["body"]
    request_params = params["params"]
    meta_data = params["meta_data"]

    if meta_data["debug"]:
        logger.info("Request:\n=====\n{}\n=====".format(json.dumps(request)))

    visualisations = int(len(request) / 2)

    response = {}

    for key in meta_data.keys():
        response[key] = meta_data[key]

    response["request_params"] = request_params
    response["weight"] = 1
    response["unit"] = "ops"
    response["visualisation_count"] = visualisations
    
    result = await es.msearch(body=request, params=request_params)

    sum_hits = 0
    max_took = 0
    error_count = 0
    error_details = set()
    for r in result["responses"]:
        if "error" in r:
            error_count += 1
            extract_error_details(error_details, r)
        else:
            hits = r.get("hits", {}).get("total", 0)
            if isinstance(hits, dict):
                sum_hits += hits["value"]
            else:
                sum_hits += hits
            max_took = max(max_took, r["took"])

    # use the request's took if possible but approximate it using the maximum of all responses
    response["took"] = result.get("took", max_took)
    response["hits"] = sum_hits
    response["success"] = error_count == 0
    response["error-count"] = error_count
    if error_count > 0:
        response["error-type"] = "kibana"
        response["error-description"] = error_description(error_details)

    if meta_data["debug"]:
        for r in result["responses"]:
            # clear hits otherwise we'll spam the log
            if "hits" in r and "hits" in r["hits"]:
                r["hits"]["hits"] = []
            r["aggregations"] = {}
        logger.info("Response (excluding specific hits):\n=====\n{}\n=====".format(json.dumps(result)))

    return response
