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


from eventdata.utils import globals as gs
import math
import re
import json
import logging
import os
import os.path
import random
import datetime
import time

logger = logging.getLogger("track.eventdata")

available_dashboards = ["traffic", "content_issues", "discover"]

epoch = datetime.datetime.utcfromtimestamp(0)


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class ConfigurationError(Error):
    """Exception raised for parameter errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class ElasticlogsKibanaSource:
    """
    Simulates a set of sample Kibana dashboards for the elasticlogs data set.

    It expects the parameter hash to contain the following keys:
        "dashboard"             -   String indicating which dashboard to simulate. Options are 'traffic', 'content_issues' and 'discover'.
        "query_string"          -   String indicating file to load or list of strings indicating actual query parameters to randomize during benchmarking. Defaults 
                                    to ["*"], If a list has been specified, a random value will be selected.
        "index_pattern"         -   String or list of strings representing the index pattern to query. If a list has
                                    been specified, a random value will be selected.
        "window_end"            -   Specification of aggregation window end or period within which it should end. If one single value is specified, 
                                    that will be used to anchor the window. If two values are given in a comma separated list, the end of the window
                                    will be randomized within this interval. Values can be either absolute or relative:
                                        'now' - Always evaluated to the current timestamp. This is the default value.
                                        'now-1h' - Offset to the current timestamp. Consists of a number and either m (minutes), h (hours) or d (days).
                                        '2016-12-20 20:12:32' - Exact timestamp.
                                        'START' - If fieldstats has been run for the index pattern and `@timestamp` field, 'START' can be used to reference the start of this interval.
                                        'END' - If fieldstats has been run for the index pattern and `@timestamp` field, 'END' can be used to reference the end of this interval.
                                        'END-40%' - When an interval has been specified based on fieldstats, it is possible to express a volume
                                        relative to the size of the interval as a percentage. If we assume the interval covers 10 hours, 'END-40%'
                                        represents the timestamp 4 hours (40% of the 10 hour interval) before the END timestamp.
        "window_length"         -   String indicating length of the time window to aggregate across. Values can be either absolute 
                                    or relative. Defaults to '1d'.
                                        '4d' - Consists of a number and either m (minutes), h (hours) or d (days). Can not be lower than 1 minute.
                                        '10%' - Length given as percentage of window size. Only available when fieldstats_id have been specified.
        "discover_size"         -   Nunmber of documents to return in Discover. Defaults to 500.
        "ignore_throttled"      -   Boolean indicating whether throttled (frozen) indices should be ignored. Defaults to `true`.
        "pre_filter_shard_size" -   Defines the `pre_filter_shard_size` parameter used with throttled (frozen) indices. Defgaults to 1.
        "debug"                 -   Boolean indicating whether request and response should be logged for debugging. Defaults to `false`.
    """
    def __init__(self, track, params, **kwargs):
        self._params = params
        self._indices = track.indices
        self._index_pattern = params["index_pattern"]
        self._query_string_list = ["*"]
        self._dashboard = params["dashboard"]
        self._discover_size = params.get("discover_size", 500)
        self._ignore_throttled = params.get("ignore_throttled", True)
        self._debug = params.get("debug", False)
        self._pre_filter_shard_size = params.get("pre_filter_shard_size", 1)
        self._window_length = params.get("window_length", "1d")
        self.infinite = True
        self.utcnow = kwargs.get("utcnow", datetime.datetime.utcnow)
        
        random.seed()

        if "query_string" in params.keys():
            if isinstance(params["query_string"], str):    
                if params["query_string"] in gs.global_config.keys():
                    self._query_string_list = gs.global_config[params["query_string"]]
                else:
                    cwd = os.path.dirname(__file__)
                    self._query_string_list = json.loads(open(os.path.join(cwd, "..", params["query_string"]), "rt", encoding="utf-8").read())
                    gs.global_config[params["query_string"]] = self._query_string_list
            else:
                self._query_string_list = params["query_string"]

        if self._dashboard not in available_dashboards:
            raise ConfigurationError("Unknown dashboard [{}]. Must be one of {}.".format(self._dashboard, available_dashboards))

        key = "{}_@timestamp".format(self._index_pattern)
        if key in gs.global_fieldstats.keys():
            stats = gs.global_fieldstats[key]
            self._fieldstats_start_ms = stats["min"]
            self._fieldstats_end_ms = stats["max"]
            self._fieldstats_provided = True
        else:
            self._fieldstats_provided = False

        re1 = re.compile(r"^(\d+\.*\d*)([dhm])$")
        re2 = re.compile(r"^(\d+\.*\d*)%$")

        m1 = re1.match(self._window_length)
        m2 = re2.match(self._window_length)
        if m1:
            val = float(m1.group(1))
            unit = m1.group(2)

            if unit == "m":
                self._window_duration_ms = int(60*val*1000)
            elif unit == "h":
                self._window_duration_ms = int(3600*val*1000)
            else:
                self._window_duration_ms = int(86400*val*1000)
        elif m2:
            if self._fieldstats_provided:
                val = int(math.fabs(float(m2.group(1)) / 100.0) * (self._fieldstats_end_ms - self._fieldstats_start_ms))
                self._window_duration_ms = val
            else:
                raise ConfigurationError("Invalid window_length as a percentage ({}) may only be used when fieldstats have been provided.".format(self._window_length))
        else:
            raise ConfigurationError("Invalid window_length parameter supplied: {}.".format(self._window_length))
                
        # Interpret window specification(s)
        if "window_end" in params.keys():
            self._window_end = self.__parse_window_parameters(params["window_end"])
        else:
            self._window_end = [{"type": "relative", "offset_ms": 0}]

    def partition(self, partition_index, total_partitions):
        seed = partition_index * self._params["seed"] if "seed" in self._params else None
        random.seed(seed)
        return self

    def params(self):
        # Determine window_end boundaries
        if len(self._window_end) == 1:
            ts_max_ms = int(self.__window_boundary_to_ms(self._window_end[0]))
        else:
            t1 = self.__window_boundary_to_ms(self._window_end[0])
            t2 = self.__window_boundary_to_ms(self._window_end[1])
            offset = (int)(random.random() * math.fabs(t2 - t1))

            ts_max_ms = int(offset + min(t1, t2))
        
        ts_min_ms = int(ts_max_ms - self._window_duration_ms)

        window_size_seconds = int(self._window_duration_ms / 1000)

        # Determine histogram interval
        interval = ElasticlogsKibanaSource.determine_interval(window_size_seconds, 50, 100)
        query_string = self.__select_random_item(self._query_string_list)
        index_pattern = self.__select_random_item(self._index_pattern)

        meta_data = {
            "interval": interval,
            "index_pattern": index_pattern,
            "query_string": query_string,
            "dashboard": self._dashboard,
            "window_length": self._window_length,
            "ignore_throttled": self._ignore_throttled,
            "pre_filter_shard_size": self._pre_filter_shard_size,
            "debug": self._debug
        }

        if self._dashboard == "traffic":
            response = {"body": self.__traffic_dashboard(index_pattern, query_string, interval, ts_min_ms, ts_max_ms, self._ignore_throttled)}
        elif self._dashboard == "content_issues":
            response = {"body": self.__content_issues_dashboard(index_pattern, query_string, interval, ts_min_ms, ts_max_ms, self._ignore_throttled)}
        elif self._dashboard == "discover":
            response = {"body": self.__discover(self._discover_size, index_pattern, query_string, interval, ts_min_ms, ts_max_ms, self._ignore_throttled)}

        response["meta_data"] = meta_data

        return response

    def __select_random_item(self, values):
        if isinstance(values, list):
            idx = random.randint(0, len(values)-1)
            return values[idx] 
        else:
            return values

    def __window_boundary_to_ms(self, wb):
        if wb["type"] == "relative":
            ct = self.__current_epoch_ms()
            cta = ct + wb["offset_ms"]
            return cta
        else:
            return wb["ts_ms"]
    
    def __current_epoch_ms(self):
        dt = self.utcnow()
        return (dt-epoch).total_seconds() *1000

    def __parse_window_parameters(self, window_spec):
        items = window_spec.split(",")
        window_end_spec = []

        re1 = re.compile(r"^now([+-]\d+\.*\d*)([dhm])$")
        re2 = re.compile(r"^\d{4}.\d{2}.\d{2}.\d{2}.\d{2}.\d{2}$")
        re3 = re.compile(r"^(START|END)$")
        re4 = re.compile(r"^(START|END)([+-]\d+\.*\d*)%$")

        for i in items:
            m1 = re1.match(i)
            m2 = re2.match(i)
            m3 = re3.match(i)
            m4 = re4.match(i)

            if i == "now":
                window_end_spec.append({"type": "relative", "offset_ms": 0})
            elif m1:
                val = float(m1.group(1))
                unit = m1.group(2)
                if unit == "m":
                    offset_ms = int(60*val*1000)
                elif unit == "h":
                    offset_ms = int(3600*val*1000)
                else:
                    offset_ms = int(86400*val*1000)

                window_end_spec.append({"type": "relative", "offset_ms": offset_ms})
            elif m2:
                c = re.split(r"\D+", i)

                dt = datetime.datetime.strptime("{} {} {} {} {} {} UTC".format(c[0], c[1], c[2], c[3], c[4], c[5]), "%Y %m %d %H %M %S %Z")
                epoch_ms = (int)((dt-epoch).total_seconds() * 1000)
                window_end_spec.append({"type": "absolute", "ts_ms": epoch_ms})
            elif m3:
                if self._fieldstats_provided:
                    if m3.group(1) == "START":
                        window_end_spec.append({"type": "absolute", "ts_ms": self._fieldstats_start_ms})
                    else:
                        window_end_spec.append({"type": "absolute", "ts_ms": self._fieldstats_end_ms})
                else:
                    raise ConfigurationError("Window end definition based on {} requires fieldstats_id has been specified.".format(m3.group(1)))
            elif m4:
                if self._fieldstats_provided:
                    reference = m4.group(1)
                    percentage = float(m4.group(2)) / 100.0
                    
                    if reference == "START":
                        epoch_ms = int(percentage * (self._fieldstats_end_ms - self._fieldstats_start_ms)) + self._fieldstats_start_ms
                    else:
                        epoch_ms = int(percentage * (self._fieldstats_end_ms - self._fieldstats_start_ms)) + self._fieldstats_end_ms
                    
                    window_end_spec.append({"type": "absolute", "ts_ms": epoch_ms})
                else:
                    raise ConfigurationError("fieldstats_id does not correspond to existing file.")

        return window_end_spec

    @staticmethod
    def determine_interval(window_size_seconds, target_bars=50, max_bars=100):
        """
        This is a simplified version of the calculation that is done by Kibana to determine the proper date histogram
        interval for the targeted number of bars in the (discovery) bar chart. It is mostly accurate for window sizes
        between 1000 seconds (16 minutes) and 1.000.000 seconds (~ 11 days). For a starting point into Kibana's
        implementation see https://github.com/elastic/kibana/blob/4f888196b740fddaeb5e71c904bc692ccd83e150/src/legacy/ui/public/time_buckets/time_buckets.js#L225-L265.

        :param window_size_seconds: The time interval in seconds that is being shown.
        :param target_bars: see ``histogram:barTarget`` in Kibana. The default value is 50 matching Kibana's default.
        :param max_bars: see ``histogram:maxBars`` in Kibana. The default value is 100 matching Kibana's default.
        :return: The interval to use in ``fixed_interval`` aggregation.
        """
        available_intervals = [
            {"unit": "1s",   "length_sec": 1},
            {"unit": "5s",   "length_sec": 5},
            {"unit": "10s",  "length_sec": 10},
            {"unit": "30s",  "length_sec": 30},
            {"unit": "1m",   "length_sec": 60},
            {"unit": "5m",   "length_sec": 300},
            {"unit": "10m",  "length_sec": 600},
            {"unit": "30m",  "length_sec": 1800},
            {"unit": "1h",   "length_sec": 3600},
            {"unit": "3h",   "length_sec": 10800},
            {"unit": "12h",  "length_sec": 43200},
            {"unit": "1d",   "length_sec": 86400},
            # week - use 7d for fixed_interval
            {"unit": "7d",   "length_sec": 604800},
            # month - use 30d for fixed_interval
            {"unit": "30d",  "length_sec": 2592000},
            # quarter - use 90d for fixed_interval
            {"unit": "90d",  "length_sec": 7776000},
            # year - use 365d for fixed_interval
            {"unit": "365d", "length_sec": 31536000}
        ]

        min_interval_size = window_size_seconds / max_bars
        target_interval_size = window_size_seconds / target_bars
        i1 = None
        i2 = None

        for interval in available_intervals:
            if interval["length_sec"] < target_interval_size:
                i1 = interval

            if interval["length_sec"] >= target_interval_size:
                i2 = interval
                break

        if i1 is None:
            selected_interval = i2["unit"]
        elif i2 is None:
            selected_interval = i1["unit"]
        elif i1["length_sec"] > min_interval_size:
            selected_interval = i1["unit"]
        else:
            selected_interval = i2["unit"]

        return selected_interval

    def __get_preference(self):
        return int(round(time.time() * 1000))

    def __content_issues_dashboard(self, index_pattern, query_string, interval, ts_min_ms, ts_max_ms, ignore_throttled):
        preference = self.__get_preference()
        header = {
            "index": index_pattern,
            "ignore_unavailable": True,
            "preference": preference,
            "ignore_throttled": ignore_throttled
        }
        return [
                   header,
                   {"size":0,"aggs":{"2":{"cardinality":{"field":"nginx.access.remote_ip"}}},"version":True,"_source":{"excludes":[]},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"match_phrase":{"nginx.access.response_code":{"query":404}}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"terms":{"field":"nginx.access.remote_ip","size":20,"order":{"_count":"desc"}}}},"version":True,"_source":{"excludes":[]},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"match_phrase":{"nginx.access.response_code":{"query":404}}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"terms":{"field":"nginx.access.url","size":20,"order":{"_count":"desc"}}}},"version":True,"_source":{"excludes":[]},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"match_phrase":{"nginx.access.response_code":{"query":404}}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"terms":{"field":"nginx.access.referrer","size":20,"order":{"_count":"desc"}}}},"version":True,"_source":{"excludes":[]},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"match_phrase":{"nginx.access.response_code":{"query":404}}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"date_histogram":{"field":"@timestamp","fixed_interval":interval,"time_zone":"Europe/London","min_doc_count":1}}},"version":True,"_source":{"excludes":[]},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"match_phrase":{"nginx.access.response_code":{"query":404}}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}}
               ]

    def __traffic_dashboard(self, index_pattern, query_string, interval, ts_min_ms, ts_max_ms, ignore_throttled):
        preference = self.__get_preference()
        header = {
            "index": index_pattern,
            "ignore_unavailable": True,
            "preference": preference,
            "ignore_throttled": ignore_throttled

        }
        return [
                   header,
                   {"size":0,"aggs":{"filter_agg":{"filter":{"geo_bounding_box":{"nginx.access.geoip.location":{"top_left":{"lat":90,"lon":-180},"bottom_right":{"lat":-90,"lon":180}}}},"aggs":{"2":{"geohash_grid":{"field":"nginx.access.geoip.location","precision":2},"aggs":{"3":{"geo_centroid":{"field":"nginx.access.geoip.location"}}}}}}},"version":True,"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"date_histogram":{"field":"@timestamp","fixed_interval":interval,"time_zone":"Europe/London","min_doc_count":1},"aggs":{"3":{"filters":{"filters":{"200s":{"query_string":{"query":"nginx.access.response_code: [200 TO 300]","analyze_wildcard":True,"default_field":"*"}},"300s":{"query_string":{"query":"nginx.access.response_code: [300 TO 400]","analyze_wildcard":True,"default_field":"*"}},"400s":{"query_string":{"query":"nginx.access.response_code: [400 TO 500]","analyze_wildcard":True,"default_field":"*"}},"500s":{"query_string":{"query":"nginx.access.response_code: [500 TO 600]","analyze_wildcard":True,"default_field":"*"}}}}}}}},"version":True,"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"terms":{"field":"nginx.access.url","size":10,"order":{"_count":"desc"}}}},"version":True,"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"date_histogram":{"field":"@timestamp","fixed_interval":interval,"time_zone":"Europe/London","min_doc_count":1},"aggs":{"1":{"sum":{"field":"nginx.access.body_sent.bytes"}}}}},"version":True,"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"terms":{"field":"nginx.access.user_agent.name","size":5,"order":{"_count":"desc"}},"aggs":{"3":{"terms":{"field":"nginx.access.user_agent.major","size":5,"order":{"_count":"desc"}}}}}},"version":True,"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"query_string":{"query":"*","analyze_wildcard":True,"default_field":"*"}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"terms":{"field":"nginx.access.user_agent.os_name","size":5,"order":{"_count":"desc"}},"aggs":{"3":{"terms":{"field":"nginx.access.user_agent.os_major","size":5,"order":{"_count":"desc"}}}}}},"version":True,"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"query_string":{"query":"*","analyze_wildcard":True,"default_field":"*"}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}},
                   header,
                   {"size":0,"aggs":{"2":{"date_histogram":{"field":"@timestamp","fixed_interval":interval,"time_zone":"Europe/London","min_doc_count":1},"aggs":{"3":{"terms":{"field":"nginx.access.response_code","size":10,"order":{"_count":"desc"}}}}}},"version":True,"_source":{"excludes":[]},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"match_all":{}},{"query_string":{"query":"nginx.access.response_code: [400 TO 600]","analyze_wildcard":True,"default_field":"*"}},{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}}
               ]

    def __discover(self, discover_size, index_pattern, query_string, interval, ts_min_ms, ts_max_ms, ignore_throttled):
        preference = self.__get_preference()
        header = {
            "index": index_pattern,
            "ignore_unavailable": True,
            "preference": preference,
            "ignore_throttled": ignore_throttled

        }
        return [
                   header,
                   {"version":True,"size":discover_size,"sort":[{"@timestamp":{"order":"desc","unmapped_type":"boolean"}}],"_source":{"excludes":[]},"aggs":{"2":{"date_histogram":{"field":"@timestamp","fixed_interval":interval,"time_zone":"Europe/London","min_doc_count":1}}},"stored_fields":["*"],"script_fields":{},"docvalue_fields":["@timestamp"],"query":{"bool":{"must":[{"query_string":{"query":query_string,"analyze_wildcard":True,"default_field":"*"}},{"range":{"@timestamp":{"gte":ts_min_ms,"lte":ts_max_ms,"format":"epoch_millis"}}}],"filter":[],"should":[],"must_not":[]}},"highlight":{"pre_tags":["@kibana-highlighted-field@"],"post_tags":["@/kibana-highlighted-field@"],"fields":{"*":{}},"fragment_size":2147483647}}
                ]


