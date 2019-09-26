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

import time
import logging
import random
import statistics


class UtilizationBasedScheduler:
    RESPONSE_TIMES = []
    """
    This scheduler schedules events at 100% utilization (unthrottled) if it is in recording mode (enabled by setting 
    ``record-response-times`` to ``True``). Otherwise it runs in measurement mode where median response time and the
     provided target utilization (via the task parameter ``target-utilization``) determine the average waiting time. 
     To prevent clients from coordinating (i.e. executing requests at exactly the same time), we randomize waiting 
     time using a Poisson distribution.
    """
    def __init__(self, params, perf_counter=time.perf_counter):
        self.logger = logging.getLogger(__name__)
        self.perf_counter = perf_counter
        self.recording = params.get("record-response-times", False)
        if self.recording:
            self.logger.info("Running in recording mode.")
            self.last_request_start = None
        else:
            self.logger.info("Running in measurement mode.")
            self.target_utilization = float(params["target-utilization"])
            if self.target_utilization <= 0.0 or self.target_utilization > 1.0:
                raise ValueError("target-utilization must be in the range (0.0, 1.0] but is {}".format(
                    self.target_utilization))
            response_times = UtilizationBasedScheduler.RESPONSE_TIMES
            if len(response_times) == 0:
                raise ValueError("No response times recorded. Please run first with 'record-response-times'.")
            median_response_time_at_full_utilization = statistics.median(response_times)
            self.time_between_requests = median_response_time_at_full_utilization * (1 / self.target_utilization)
            self.logger.info("Time between requests is [%.3f] seconds for a utilization of [%.2f]%% (based on "
                             "[%d] samples with a median response time of [%.3f] seconds).",
                             self.time_between_requests, (self.target_utilization * 100), len(response_times),
                             median_response_time_at_full_utilization)

    def next(self, current):
        if self.recording:
            now = self.perf_counter()
            # skip the very first sample
            if self.last_request_start is not None:
                UtilizationBasedScheduler.RESPONSE_TIMES.append(now - self.last_request_start)
            self.last_request_start = now
            # run unthrottled while determining the target utilization
            return 0

        if self.target_utilization == 1.0:
            return 0
        else:
            # don't let every client send requests at the same time
            return current + random.expovariate(1 / self.time_between_requests)

    # intended for testing
    @classmethod
    def reset_recorded_response_times(cls):
        UtilizationBasedScheduler.RESPONSE_TIMES = []

    def __str__(self):
        if self.recording:
            return "Utilization scheduler in recording mode."
        else:
            return "Utilization scheduler with target utilization of {:.2f}%.".format(self.target_utilization * 100)
