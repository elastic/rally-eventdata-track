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

from datetime import datetime
from unittest import mock

import pytest

from eventdata.parameter_sources.elasticlogs_kibana_source import ElasticlogsKibanaSource, ConfigurationError
from parameter_sources import StaticTrack


@mock.patch("time.time")
def test_create_discover(time):
    time.return_value = 5000

    param_source = ElasticlogsKibanaSource(track=StaticTrack(), params={
        "dashboard": "discover"
    }, utcnow=lambda: datetime(year=2019, month=11, day=11))
    response = param_source.params()

    assert response == {
        "body": [
            {
                "index": "elasticlogs-*",
                "ignore_unavailable": True,
                "preference": 5000000,
                "ignore_throttled": True
            },
            {
                "version": True,
                "size": 500,
                "sort": [
                    {"@timestamp": {"order": "desc", "unmapped_type": "boolean"}}
                ],
                "_source": {"excludes": []},
                "aggs": {
                    "2": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "interval": "30m",
                            "time_zone": "Europe/London",
                            "min_doc_count": 1}
                    }
                },
                "stored_fields": ["*"],
                "script_fields": {},
                "docvalue_fields": [
                    {"field": "@timestamp", "format": "date_time"}
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "query_string": {
                                    "query": "*",
                                    "analyze_wildcard": True,
                                    "default_field": "*"
                                }
                            },
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": 1573344000000,
                                        "lte": 1573430400000,
                                        "format": "epoch_millis"
                                    }
                                }
                            }
                        ],
                        "filter": [],
                        "should": [],
                        "must_not": []
                    }
                },
                "highlight": {
                    "pre_tags": ["@kibana-highlighted-field@"],
                    "post_tags": ["@/kibana-highlighted-field@"],
                    "fields": {"*": {}},
                    "fragment_size": 2147483647
                }
            }
        ],
        "meta_data": {
            "interval": "30m",
            "index_pattern": "elasticlogs-*",
            "query_string": "*",
            "dashboard": "discover",
            "window_length": "1d",
            "ignore_throttled": True,
            "pre_filter_shard_size": 1,
            "debug": False
        }
    }


def test_dashboard_is_mandatory():
    with pytest.raises(KeyError) as ex:
        ElasticlogsKibanaSource(track=StaticTrack(), params={})

    assert "'dashboard'" == str(ex.value)


def test_invalid_dashboard_raises_error():
    with pytest.raises(ConfigurationError) as ex:
        ElasticlogsKibanaSource(track=StaticTrack(), params={"dashboard": "unknown"})

    assert "Unknown dashboard [unknown]. Must be one of ['traffic', 'content_issues', 'discover']." == str(ex.value)

