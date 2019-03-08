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
import sys
from unittest import TestCase

from eventdata.parameter_sources.randomevent import RandomEvent


class RandomEventTest(TestCase):

    logger = logging.getLogger(__name__)
    logger.level = logging.INFO
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)

    def test_random_event_generator_without_pipeline(self):
        params=dict()
        random_event = RandomEvent(params)
        (jsonStr, index, i_type)=random_event.generate_event()
        parsed = json.loads(jsonStr)
        self.logger.debug(json.dumps(parsed, indent=2, sort_keys=False))

        self.assertTrue(True if parsed['@timestamp'] else False)
        self.assertTrue('user_agent' in parsed['nginx']['access'])

    def test_random_event_generator_pipeline(self):
        params = {
            "pipeline": "test"
        }
        random_event = RandomEvent(params)
        (jsonStr, index, i_type) = random_event.generate_event()
        parsed = json.loads(jsonStr)
        self.logger.debug(json.dumps(parsed, indent=2, sort_keys=False))

        self.assertTrue(True if parsed['@timestamp'] else False)
        self.assertFalse("user_agent" in parsed['nginx']['access'])


