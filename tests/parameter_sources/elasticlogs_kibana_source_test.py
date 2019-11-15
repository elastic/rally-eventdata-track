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
import os
from datetime import datetime
from unittest import mock

import pytest

from eventdata.parameter_sources.elasticlogs_kibana_source import ElasticlogsKibanaSource, ConfigurationError
from tests.parameter_sources import StaticTrack


def load(dashboard_name):
    cwd = os.path.dirname(__file__)
    with open(os.path.join(cwd, "resources", "expected-{}.json".format(dashboard_name)), "rt") as f:
        return json.load(f)


@mock.patch("time.time")
def test_create_discover(time):
    time.return_value = 5000

    param_source = ElasticlogsKibanaSource(track=StaticTrack(), params={
        "dashboard": "discover"
    }, utcnow=lambda: datetime(year=2019, month=11, day=11))
    response = param_source.params()

    assert response == load("discover")


@mock.patch("time.time")
def test_create_content_issues_dashboard(time):
    time.return_value = 5000

    param_source = ElasticlogsKibanaSource(track=StaticTrack(), params={
        "dashboard": "content_issues"
    }, utcnow=lambda: datetime(year=2019, month=11, day=11))
    response = param_source.params()

    assert response == load("content_issues")


@mock.patch("time.time")
def test_create_traffic_dashboard(time):
    time.return_value = 5000

    param_source = ElasticlogsKibanaSource(track=StaticTrack(), params={
        "dashboard": "traffic"
    }, utcnow=lambda: datetime(year=2019, month=11, day=11))
    response = param_source.params()

    assert response == load("traffic")


def test_dashboard_is_mandatory():
    with pytest.raises(KeyError) as ex:
        ElasticlogsKibanaSource(track=StaticTrack(), params={})

    assert "'dashboard'" == str(ex.value)


def test_invalid_dashboard_raises_error():
    with pytest.raises(ConfigurationError) as ex:
        ElasticlogsKibanaSource(track=StaticTrack(), params={"dashboard": "unknown"})

    assert "Unknown dashboard [unknown]. Must be one of ['traffic', 'content_issues', 'discover']." == str(ex.value)


def test_determine_interval():
    test_params = [
        # window size, expected interval
        (1,             "1s"),
        (10,            "1s"),
        (100,           "5s"),
        (1000,         "30s"),
        (10000,         "5m"),
        (100000,       "30m"),
        (1000000,       "3h"),
        (10000000,      "7d"),
        (100000000,    "30d"),
    ]
    for window_size, expected_interval in test_params:
        assert ElasticlogsKibanaSource.determine_interval(window_size_seconds=window_size, target_bars=50, max_bars=100) == expected_interval
