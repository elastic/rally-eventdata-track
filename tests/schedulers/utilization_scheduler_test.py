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


@pytest.fixture()
def reset_recorded_times():
    UtilizationBasedScheduler.reset_recorded_response_times()


class StaticPerfCounter:
    def __init__(self, start):
        self.now = start

    def __call__(self, *args, **kwargs):
        return self.now


@pytest.mark.usefixtures("reset_recorded_times")
def test_invalid_target_utilization():
    with pytest.raises(ValueError) as ex:
        UtilizationBasedScheduler(params={
            "target-utilization": 200.432,
            "record-response-times": False
        })

    assert "target-utilization must be in the range (0.0, 1.0] but is 200.432" == str(ex.value)

    with pytest.raises(ValueError) as ex:
        UtilizationBasedScheduler(params={
            "target-utilization": 0.0,
            "record-response-times": False
        })

    assert "target-utilization must be in the range (0.0, 1.0] but is 0.0" == str(ex.value)


@pytest.mark.usefixtures("reset_recorded_times")
def test_no_response_times_recorded():
    with pytest.raises(ValueError) as ex:
        UtilizationBasedScheduler(params={
            "target-utilization": 0.5,
            "record-response-times": False
        })

    assert "No response times recorded. Please run first with 'record-response-times'." == str(ex.value)


@pytest.mark.usefixtures("reset_recorded_times")
def test_valid_params():
    # simulate that response times have been recorded previously...
    UtilizationBasedScheduler.RESPONSE_TIMES.append(1)

    s = UtilizationBasedScheduler(params={
        "target-utilization": 0.0000001,
        "record-response-times": False
    })

    assert s is not None

    s = UtilizationBasedScheduler(params={
        "target-utilization": 1.0,
        "warmup-time-period": 100
    })

    assert s is not None


@pytest.mark.usefixtures("reset_recorded_times")
def test_unthrottled_calculation():
    perf_counter = StaticPerfCounter(start=0)

    s = UtilizationBasedScheduler(params={
        "record-response-times": True
    }, perf_counter=perf_counter)

    # simulate two requests 10 seconds apart
    assert s.next(0) == 0
    perf_counter.now = 10
    assert s.next(0) == 0

    s = UtilizationBasedScheduler(params={
        "target-utilization": 1.0,
        "record-response-times": False
    }, perf_counter=perf_counter)

    # normal mode of operation (unthrottled)
    assert s.next(200) == 0
    assert s.next(300) == 0


@pytest.mark.usefixtures("reset_recorded_times")
def test_throttled_calculation():
    perf_counter = StaticPerfCounter(start=0)

    s = UtilizationBasedScheduler(params={
        "record-response-times": True
    }, perf_counter=perf_counter)

    # recording phase, response time is always 20 seconds
    next_scheduled = 0
    for t in range(0, 100, 20):
        perf_counter.now = t
        next_scheduled = s.next(next_scheduled)
        assert next_scheduled == 0

    # now we're in throttled mode
    s = UtilizationBasedScheduler(params={
        "target-utilization": 0.1,
        "record-response-times": False
    }, perf_counter=perf_counter)
    # 20 seconds * (1 / target utilization) = 20 seconds * (1 / 0.1) = 20 seconds * 10 = 200 seconds
    assert s.time_between_requests == 200

    # normal mode of operation
    waiting_times = []
    next_scheduled = 0
    while next_scheduled < 1000000:
        next_request = s.next(next_scheduled)
        waiting_times.append((next_request - next_scheduled))
        # 20 seconds is our expected response time
        next_scheduled = next_request

    # mean response time should approach 200 seconds
    assert 190 <= statistics.mean(waiting_times) <= 210
