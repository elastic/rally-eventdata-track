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

from unittest import mock

from eventdata.runners.kibana_runner import kibana_async

from tests import run_async, as_future


@mock.patch("elasticsearch.Elasticsearch")
@run_async
async def test_msearch_without_hits(es):
    params = {
        "body": [
            {"index": "elasticlogs-*"},
            {"query": {"match_all": {}}, "from": 0, "size": 10},
            {"index": "elasticlogs-*"},
            {"query": {"match_all": {}}, "from": 0, "size": 10}
        ],
        "meta_data": {
            "debug": True
        }
    }
    es.msearch.return_value = as_future({
        "responses": [
            {
                "took": 0,
                "timed_out": False,
                "hits": {
                    "total": 0,
                    "hits": []
                },
                "status": 200
            },
            {
                "took": 0,
                "timed_out": False,
                "hits": {
                    "total": 0,
                    "hits": []
                },
                "status": 200
            }
        ]
    })

    response = await kibana_async(es, params=params)

    assert response == {
        "debug": True,
        "hits": 0,
        "took": 0,
        "weight": 1,
        "unit": "ops",
        "visualisation_count": 2,
    }


@mock.patch("elasticsearch.Elasticsearch")
@run_async
async def test_msearch_with_hits_as_number(es):
    params = {
        "body": [
            {"index": "elasticlogs-*"},
            {"query": {"match_all": {}}, "from": 0, "size": 10},
            {"index": "elasticlogs-*"},
            {"query": {"match_all": {}}, "from": 0, "size": 10}
        ],
        "meta_data": {
            "debug": True
        }
    }
    es.msearch.return_value = as_future({
        "responses": [
            {
                "took": 5,
                "timed_out": False,
                "hits": {
                    "total": 1,
                    "hits": [
                        {
                            "_index": "my-docs",
                            "_type": "_doc",
                            "_id": "1",
                            "_score": 1,
                            "_source": {
                                "title": "Hello"
                            }
                        }
                    ]
                },
                "status": 200
            },
            {
                "took": 7,
                "timed_out": False,
                "hits": {
                    "total": 2,
                    "hits": [
                        {
                            "_index": "my-other-docs",
                            "_type": "_doc",
                            "_id": "1",
                            "_score": 1,
                            "_source": {
                                "title": "Hello"
                            }
                        },
                        {
                            "_index": "my-other-docs",
                            "_type": "_doc",
                            "_id": "2",
                            "_score": 1,
                            "_source": {
                                "title": "World"
                            }
                        }

                    ]
                },
                "status": 200
            }

        ]
    })

    response = await kibana_async(es, params=params)

    assert response == {
        "debug": True,
        "hits": 3,
        "took": 7,
        "weight": 1,
        "unit": "ops",
        "visualisation_count": 2,
    }


@mock.patch("elasticsearch.Elasticsearch")
@run_async
async def test_msearch_with_hits_as_dict(es):
    params = {
        "body": [
            {"index": "elasticlogs-*"},
            {"query": {"match_all": {}}, "from": 0, "size": 10},
            {"index": "elasticlogs-*"},
            {"query": {"match_all": {}}, "from": 0, "size": 10}
        ],
        "meta_data": {
            "debug": True
        }
    }
    es.msearch.return_value = as_future({
        "took": 9,
        "responses": [
            {
                "took": 5,
                "timed_out": False,
                "hits": {
                    "total": {
                        "value": 1,
                        "relation": "eq"
                    },
                    "hits": [
                        {
                            "_index": "my-docs",
                            "_type": "_doc",
                            "_id": "1",
                            "_score": 1,
                            "_source": {
                                "title": "Hello"
                            }
                        }
                    ]
                },
                "status": 200
            },
            {
                "took": 7,
                "timed_out": False,
                "hits": {
                    "total": {
                        "value": 2,
                        "relation": "eq"
                    },
                    "hits": [
                        {
                            "_index": "my-other-docs",
                            "_type": "_doc",
                            "_id": "1",
                            "_score": 1,
                            "_source": {
                                "title": "Hello"
                            }
                        },
                        {
                            "_index": "my-other-docs",
                            "_type": "_doc",
                            "_id": "2",
                            "_score": 1,
                            "_source": {
                                "title": "World"
                            }
                        }

                    ]
                },
                "status": 200
            }

        ]
    })

    response = await kibana_async(es, params=params)

    assert response == {
        "debug": True,
        "hits": 3,
        "took": 9,
        "weight": 1,
        "unit": "ops",
        "visualisation_count": 2,
    }
