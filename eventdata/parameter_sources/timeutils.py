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


import datetime
import re

epoch = datetime.datetime.utcfromtimestamp(0)


class TimeParsingError(Exception):
    """Exception raised for parameter parsing errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


class TimestampStructGenerator:
    def __init__(self, starting_point, offset=None, acceleration_factor=1.0, utcnow=None):
        self._utcnow = utcnow if utcnow else datetime.datetime.utcnow
        # the (actual) time when this generator has started
        self._start = self._utcnow()
        # the logical point in time for which we'll generate timestamps
        self._starting_point = self.__parse_starting_point(starting_point) + self.__parse_offset(offset)
        self._acceleration_factor = acceleration_factor
        # reuse to reduce object churn
        self._ts = {}
        self._simulated_micros = 0.0

    def next_timestamp(self):
        self._simulated_micros = 0.0
        delta = (self._utcnow() - self._start) * self._acceleration_factor
        self.__to_struct(self._starting_point + delta)
        return self.simulate_tick(0)

    def simulate_tick(self, micros):
        """

        Advances the current timestamp by a given number of microseconds but keep all other time components. This can be
        used to avoid retrieving the current timestamp to often but still simulate changes in time.

        :param micros: A positive number of microseconds to add.
        :return: The current (formatted) timestamp structure as a dict.
        """
        self._simulated_micros += micros
        self._ts["iso"] = "%s.%03dZ" % (self._ts["iso_prefix"], self._simulated_micros)
        return self._ts

    def skip(self, delta):
        # advance the generated timestamp by delta
        self._starting_point = self._starting_point + delta
        # also reset the generator start as we want to ensure the same delta in #next_timestamp()
        self._start = self._utcnow()

    def __to_struct(self, dt):
        # string formatting is about 4 times faster than strftime.
        iso_prefix = "%04d-%02d-%02dT%02d:%02d:%02d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        self._ts["iso_prefix"] = iso_prefix
        self._ts["yyyy"] = iso_prefix[:4]
        self._ts["yy"] = iso_prefix[2:4]
        self._ts["mm"] = iso_prefix[5:7]
        self._ts["dd"] = iso_prefix[8:10]
        self._ts["hh"] = iso_prefix[11:13]

    def __parse_starting_point(self, point):
        if point == "now":
            # this is "now" at this point
            return self._start
        else:
            match = re.match(r"^(\d{4})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})$", point)
            if match:
                return datetime.datetime(year=int(match.group(1)),
                                         month=int(match.group(2)),
                                         day=int(match.group(3)),
                                         hour=int(match.group(4)),
                                         minute=int(match.group(5)),
                                         second=int(match.group(6)),
                                         tzinfo=datetime.timezone.utc)
            else:
                match = re.match(r"^(\d{4})\D(\d{2})\D(\d{2})$", point)
                if match:
                    return datetime.datetime(year=int(match.group(1)),
                                             month=int(match.group(2)),
                                             day=int(match.group(3)),
                                             tzinfo=datetime.timezone.utc)

        raise TimeParsingError("Invalid time format: {}".format(point))

    def __parse_offset(self, offset):
        if offset is None:
            return datetime.timedelta()
        match = re.match(r"^([+-]\d+)([hmd])$", offset)
        if match:
            offset_amount = int(match.group(1))
            if match.group(2) == "m":
                return datetime.timedelta(minutes=offset_amount)
            elif match.group(2) == "h":
                return datetime.timedelta(hours=offset_amount)
            elif match.group(2) == "d":
                return datetime.timedelta(days=offset_amount)
            else:
                raise TimeParsingError("Invalid offset: {}".format(offset))
        else:
            raise TimeParsingError("Invalid offset: {}".format(offset))

