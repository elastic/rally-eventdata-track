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

import pytest
import statistics

from eventdata.schedulers.utilization_scheduler import UtilizationBasedScheduler


class StaticPerfCounter:
    def __init__(self, start):
        self.now = start

    def __call__(self, *args, **kwargs):
        return self.now


def test_invalid_target_utilization():
    with pytest.raises(ValueError) as ex:
        UtilizationBasedScheduler(params={
            "target-utilization": 200.432,
            "warmup-time-period": 100
        })

    assert "target-utilization must be in the range (0.0, 1.0] but is 200.432" == str(ex.value)

    with pytest.raises(ValueError) as ex:
        UtilizationBasedScheduler(params={
            "target-utilization": 0.0,
            "warmup-time-period": 100
        })

    assert "target-utilization must be in the range (0.0, 1.0] but is 0.0" == str(ex.value)


def test_valid_params():
    s = UtilizationBasedScheduler(params={
        "target-utilization": 0.0000001,
        "warmup-time-period": 100
    })

    assert s is not None

    s = UtilizationBasedScheduler(params={
        "target-utilization": 1.0,
        "warmup-time-period": 100
    })

    assert s is not None


def test_unthrottled_calculation():
    perf_counter = StaticPerfCounter(start=0)

    s = UtilizationBasedScheduler(params={
        "target-utilization": 1.0,
        "warmup-time-period": 100
    }, perf_counter=perf_counter)

    assert s.next(0) == 0
    assert s.in_warmup
    assert s.start_warmup == 0
    assert s.end_warmup == 100

    # simulate end of warmup
    perf_counter.now = 100
    assert s.next(100) == 0
    assert not s.in_warmup

    # normal mode of operation
    assert s.next(200) == 0
    assert s.next(300) == 0


def test_throttled_calculation():
    perf_counter = StaticPerfCounter(start=0)

    s = UtilizationBasedScheduler(params={
        "target-utilization": 0.1,
        "warmup-time-period": 100
    }, perf_counter=perf_counter)

    # warmup phase, response time is always 20 seconds
    for t in range(0, 100, 20):
        perf_counter.now = t
        assert s.next(t) == 0
        assert s.in_warmup
        assert s.start_warmup == 0
        assert s.end_warmup == 100

    # simulate end of warmup
    perf_counter.now = 100
    assert s.next(100) == 0
    assert not s.in_warmup
    # 20 seconds * (1 / target utilization - 1) = 20 seconds * (1 / 0.1 - 1) = 20 seconds * 9 = 180 seconds
    assert s.wait_time == 180

    # normal mode of operation
    t = 101
    waiting_times = []
    while t < 1000000:
        next_request = s.next(t)
        waiting_times.append((next_request - t))
        # 20 seconds is our expected response time
        t = next_request + 20

    # mean response time should approach 180 seconds
    assert 170 <= statistics.mean(waiting_times) <= 190
