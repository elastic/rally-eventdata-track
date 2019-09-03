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
    """
    This scheduler schedules events at 100% utilization (unthrottled) during the warmup time-period. It tracks this
    period itself (i.e. independently of Rally) using the task parameter ``warmup-time-period``. During this period
    it gathers response time metrics. The median response time and the provided target utilization (via the task
    parameter ``target-utilization``) determine the average waiting time during the actual measurement phase of the
    benchmark. In order to avoid that clients coordinate, we randomize waiting time using a Poisson distribution.
    """
    def __init__(self, params, perf_counter=time.perf_counter):
        self.logger = logging.getLogger(__name__)
        self.perf_counter = perf_counter
        self.target_utilization = float(params["target-utilization"])
        if self.target_utilization <= 0.0 or self.target_utilization > 1.0:
            raise ValueError("target-utilization must be in the range (0.0, 1.0] but is {}".format(
                self.target_utilization))
        self.warmup_time_period = int(params["warmup-time-period"])
        # to determine the target utilization
        self.response_times = []
        self.start_warmup = None
        self.end_warmup = None
        self.in_warmup = None
        self.last_request_start = None
        # determined by the utilization calculation
        self.wait_time = None

    def next(self, current):
        if self.in_warmup is None:
            self.in_warmup = True
            self.start_warmup = self.perf_counter()
            self.end_warmup = self.start_warmup + self.warmup_time_period
            self.last_request_start = self.start_warmup
            return 0
        elif self.in_warmup:
            now = self.perf_counter()
            self.response_times.append(now - self.last_request_start)
            self.last_request_start = now
            if now >= self.end_warmup:
                self.in_warmup = False
                median_response_time_at_full_utilization = statistics.median(self.response_times)
                # To determine the waiting time we need to subtract the (expected) response time from the total expected
                # response time.
                self.wait_time = median_response_time_at_full_utilization * ((1 / self.target_utilization) - 1)
                self.logger.info("Waiting time is [%.2f] seconds for a utilization of [%.2f]%% (based on [%d] samples).",
                                 self.wait_time, (self.target_utilization * 100), len(self.response_times))
            # run unthrottled while determining the target utilization
            return 0

        if self.target_utilization == 1.0:
            return 0
        else:
            # don't let every client send requests at the same time
            return current + random.expovariate(1 / self.wait_time)

    def __str__(self):
        return "Utilization scheduler with target utilization of {:.2f}%.".format(self.target_utilization * 100)
