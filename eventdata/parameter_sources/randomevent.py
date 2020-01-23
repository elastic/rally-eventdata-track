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
import gzip
import itertools
import json
import os
import random
import re

from eventdata.parameter_sources.timeutils import TimestampStructGenerator
from eventdata.parameter_sources.weightedarray import WeightedArray
from eventdata.utils import elasticlogs_bulk_source as ebs

cwd = os.path.dirname(__file__)


class Agent:
    def __init__(self):
        
        if '_agents' in ebs.global_lookups.keys():
            self._agents = ebs.global_lookups['_agents']
        else:
            self._agents = WeightedArray('%s/data/agents.json.gz' % cwd)
            ebs.global_lookups['_agents'] = self._agents

        if '_agents_name_lookup' in ebs.global_lookups.keys():
            self._agents_name_lookup = ebs.global_lookups['_agents_name_lookup']
        else:
            with gzip.open('%s/data/agents_name_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agents_name_lookup = json.load(data_file)
            ebs.global_lookups['_agents_name_lookup'] = self._agents_name_lookup

        if '_agents_os_lookup' in ebs.global_lookups.keys():
            self._agents_os_lookup = ebs.global_lookups['_agents_os_lookup']
        else:
            with gzip.open('%s/data/agents_os_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agents_os_lookup = json.load(data_file)
            ebs.global_lookups['_agents_os_lookup'] = self._agents_os_lookup

        if '_agents_os_name_lookup' in ebs.global_lookups.keys():
            self._agents_os_name_lookup = ebs.global_lookups['_agents_os_name_lookup']
        else:
            with gzip.open('%s/data/agents_os_name_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agents_os_name_lookup = json.load(data_file)
            ebs.global_lookups['_agents_os_name_lookup'] = self._agents_os_name_lookup

        if '_agents_os_major_lookup' in ebs.global_lookups.keys():
            self._agents_os_major_lookup = ebs.global_lookups['_agents_os_major_lookup']
        else:
            with gzip.open('%s/data/agents_os_major_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agents_os_major_lookup = json.load(data_file)
            ebs.global_lookups['_agents_os_major_lookup'] = self._agents_os_major_lookup

        if '_agents_major_lookup' in ebs.global_lookups.keys():
            self._agents_major_lookup = ebs.global_lookups['_agents_major_lookup']
        else:
            with gzip.open('%s/data/agents_major_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agents_major_lookup = json.load(data_file)
            ebs.global_lookups['_agents_major_lookup'] = self._agents_major_lookup

        if '_agents_device_lookup' in ebs.global_lookups.keys():
            self._agents_device_lookup = ebs.global_lookups['_agents_device_lookup']
        else:
            with gzip.open('%s/data/agents_device_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agents_device_lookup = json.load(data_file)
            ebs.global_lookups['_agents_device_lookup'] = self._agents_device_lookup

        if '_agent_lookup' in ebs.global_lookups.keys():
            self._agent_lookup = ebs.global_lookups['_agent_lookup']
        else:
            with gzip.open('%s/data/agent_lookup.json.gz' % cwd, 'rt') as data_file:
                self._agent_lookup = json.load(data_file)
            ebs.global_lookups['_agent_lookup'] = self._agent_lookup

    def add_fields(self, event):
        agent = self._agents.get_random()

        event['useragent_name'] = self.__get_lookup_value(self._agents_name_lookup, agent[0])
        event['useragent_os'] = self.__get_lookup_value(self._agents_os_lookup, agent[1])
        event['useragent_os_name'] = self.__get_lookup_value(self._agents_os_name_lookup, agent[2])
        event['useragent_device'] = self.__get_lookup_value(self._agents_device_lookup, agent[3])
        event['useragent_os_major'] = self.__get_lookup_value(self._agents_os_major_lookup, agent[4])
        event['useragent_major'] = self.__get_lookup_value(self._agents_major_lookup, agent[5])
        event['agent'] = self.__get_lookup_value(self._agent_lookup, agent[6])

    def __get_lookup_value(self, lookup, key):
        if key == "":
            return key
        else :
            return lookup[key]


class ClientIp:
    def __init__(self):
        self._rare_clientip_probability = 0.269736965199

        if '_clientips' in ebs.global_lookups.keys():
            self._clientips = ebs.global_lookups['_clientips']
        else:
            self._clientips = WeightedArray('%s/data/clientips.json.gz' % cwd)
            ebs.global_lookups['_clientips'] = self._clientips

        if '_rare_clientips' in ebs.global_lookups.keys():
            self._rare_clientips = ebs.global_lookups['_rare_clientips']
        else:
            self._rare_clientips = WeightedArray('%s/data/rare_clientips.json.gz' % cwd)
            ebs.global_lookups['_rare_clientips'] = self._rare_clientips
        
        if '_clientips_country_name_lookup' in ebs.global_lookups.keys():
            self._clientips_country_name_lookup = ebs.global_lookups['_clientips_country_name_lookup']
        else:
            with gzip.open('%s/data/clientips_country_name_lookup.json.gz' % cwd, 'rt') as data_file:
                self._clientips_country_name_lookup = json.load(data_file)
            ebs.global_lookups['_clientips_country_name_lookup'] = self._clientips_country_name_lookup

        if '_clientips_country_iso_code_lookup' in ebs.global_lookups.keys():
            self._clientips_country_iso_code_lookup = ebs.global_lookups['_clientips_country_iso_code_lookup']
        else:
            with gzip.open('%s/data/clientips_country_iso_code_lookup.json.gz' % cwd, 'rt') as data_file:
                self._clientips_country_iso_code_lookup = json.load(data_file)
            ebs.global_lookups['_clientips_country_iso_code_lookup'] = self._clientips_country_iso_code_lookup

        if '_clientips_continent_name_lookup' in ebs.global_lookups.keys():
            self._clientips_continent_name_lookup = ebs.global_lookups['_clientips_continent_name_lookup']
        else:
            with gzip.open('%s/data/clientips_continent_name_lookup.json.gz' % cwd, 'rt') as data_file:
                self._clientips_continent_name_lookup = json.load(data_file)
            ebs.global_lookups['_clientips_continent_name_lookup'] = self._clientips_continent_name_lookup

        if '_clientips_continent_code_lookup' in ebs.global_lookups.keys():
            self._clientips_continent_code_lookup = ebs.global_lookups['_clientips_continent_code_lookup']
        else:
            with gzip.open('%s/data/clientips_continent_code_lookup.json.gz' % cwd, 'rt') as data_file:
                self._clientips_continent_code_lookup = json.load(data_file)
            ebs.global_lookups['_clientips_continent_code_lookup'] = self._clientips_continent_code_lookup

        if '_clientips_city_name_lookup' in ebs.global_lookups.keys():
            self._clientips_city_name_lookup = ebs.global_lookups['_clientips_city_name_lookup']
        else:
            with gzip.open('%s/data/clientips_city_name_lookup.json.gz' % cwd, 'rt') as data_file:
                self._clientips_city_name_lookup = json.load(data_file)
            ebs.global_lookups['_clientips_city_name_lookup'] = self._clientips_city_name_lookup

    def add_fields(self, event):
        p = random.random()
        if p < self._rare_clientip_probability:
            data = self._rare_clientips.get_random()
            event['clientip'] = self.__fill_out_ip_prefix(data[0])
        else:
            data = self._clientips.get_random()
            event['clientip'] = data[0]

        event['geoip_location_lat'] = data[1][0]
        event['geoip_location_lon'] = data[1][1]
        event['geoip_city_name'] = self.__get_lookup_value(self._clientips_city_name_lookup, data[2])
        event['geoip_country_name'] = self.__get_lookup_value(self._clientips_country_name_lookup, data[3])
        event['geoip_country_iso_code'] = self.__get_lookup_value(self._clientips_country_iso_code_lookup, data[4])
        event['geoip_continent_name'] = self.__get_lookup_value(self._clientips_continent_name_lookup, data[5])
        event['geoip_continent_code'] = self.__get_lookup_value(self._clientips_continent_code_lookup, data[5])

    def __fill_out_ip_prefix(self, ip_prefix):
        rnd1 = random.random()
        v1 = rnd1 * (1 - rnd1) * 255 * 4
        k1 = (int)(v1)
        rnd2 = random.random()
        v2 = rnd2 * (1 - rnd2) * 255 * 4
        k2 = (int)(v2)

        return "{}.{}.{}".format(ip_prefix, k1, k2)

    def __get_lookup_value(self, lookup, key):
        if key == "":
            return key
        else :
            return lookup[key]


class Referrer:
    def __init__(self):
        if '_referrers' in ebs.global_lookups.keys():
            self._referrers = ebs.global_lookups['_referrers']
        else:
            self._referrers = WeightedArray('%s/data/referrers.json.gz' % cwd)
            ebs.global_lookups['_referrers'] = self._referrers
        
        if '_referrers_url_base_lookup' in ebs.global_lookups.keys():
            self._referrers_url_base_lookup = ebs.global_lookups['_referrers_url_base_lookup']
        else:
            with gzip.open('%s/data/referrers_url_base_lookup.json.gz' % cwd, 'rt') as data_file:
                self._referrers_url_base_lookup = json.load(data_file)
            ebs.global_lookups['_referrers_url_base_lookup'] = self._referrers_url_base_lookup

    def add_fields(self, event):
        data = self._referrers.get_random()
        event['referrer'] = "%s%s" % (self._referrers_url_base_lookup[data[0]], data[1])


class Request:
    def __init__(self):
        if '_requests' in ebs.global_lookups.keys():
            self._requests = ebs.global_lookups['_requests']
        else:
            self._requests = WeightedArray('%s/data/requests.json.gz' % cwd)
            ebs.global_lookups['_requests'] = self._requests
        
        if '_requests_url_base_lookup' in ebs.global_lookups.keys():
            self._requests_url_base_lookup = ebs.global_lookups['_requests_url_base_lookup']
        else:
            with gzip.open('%s/data/requests_url_base_lookup.json.gz' % cwd, 'rt') as data_file:
                self._requests_url_base_lookup = json.load(data_file)
            ebs.global_lookups['_requests_url_base_lookup'] = self._requests_url_base_lookup

    def add_fields(self, event):
        data = self._requests.get_random()
        event['request'] = "{}{}".format(self._requests_url_base_lookup[data[0]], data[1])
        event['bytes'] = data[2]
        event['verb'] = data[3]
        event['response'] = data[4]
        event['httpversion'] = data[5]


def convert_to_bytes(size):
    matched_size = re.match(r"^(\d+)\s?(kB|MB|GB)?$", size)
    if matched_size:
        value = int(matched_size.group(1))
        unit = matched_size.group(2)
        if unit == "kB":
            return value << 10
        elif unit == "MB":
            return value << 20
        elif unit == "GB":
            return value << 30
        elif unit is None:
            return value
        else:
            # we should only reach this if the regex does not match the code here
            raise ValueError("Unrecognized unit [{}] for byte size value [{}]".format(unit, size))
    else:
        raise ValueError("Invalid byte size value [{}]".format(size))


class RandomEvent:
    def __init__(self, params, agent=Agent, client_ip=ClientIp, referrer=Referrer, request=Request):
        self._agent = agent()
        self._clientip = client_ip()
        self._referrer = referrer()
        self._request = request()
        # We will reuse the event dictionary. This assumes that each field will be present (and thus overwritten) in each event.
        # This reduces object churn and improves peak indexing throughput.
        self._event = {}

        if "index" in params:
            index = re.sub(r"<\s*yyyy\s*>", "{ts[yyyy]}", params["index"], flags=re.IGNORECASE)
            index = re.sub(r"<\s*yy\s*>", "{ts[yy]}", index, flags=re.IGNORECASE)
            index = re.sub(r"<\s*mm\s*>", "{ts[mm]}", index, flags=re.IGNORECASE)
            index = re.sub(r"<\s*dd\s*>", "{ts[dd]}", index, flags=re.IGNORECASE)
            index = re.sub(r"<\s*hh\s*>", "{ts[hh]}", index, flags=re.IGNORECASE)

            self._index = index
            self._index_pattern = True
        else:
            self._index = "elasticlogs"
            self._index_pattern = False

        self._type = "doc"
        self._timestamp_generator = TimestampStructGenerator(
            params.get("starting_point", "now"),
            params.get("offset"),
            float(params.get("acceleration_factor", "1.0")),
            # this is only expected to be used in tests
            params.get("__utc_now")
        )
        if "daily_logging_volume" in params and "client_count" in params:
            # in bytes
            self.daily_logging_volume = convert_to_bytes(params["daily_logging_volume"]) // int(params["client_count"])
        else:
            self.daily_logging_volume = None
        self.current_logging_volume = 0
        self.total_days = params.get("number_of_days")
        self.remaining_days = self.total_days
        self.record_raw_event_size = params.get("record_raw_event_size", False)
        self._offset = 0
        self._web_host = itertools.cycle([1, 2, 3])
        self._timestruct = None
        self._index_name = None
        self._time_interval_current_bulk = 0

    @property
    def percent_completed(self):
        if self.daily_logging_volume is None or self.total_days is None:
            return None
        else:
            full_days = self.total_days - self.remaining_days
            already_generated = self.daily_logging_volume * full_days + self.current_logging_volume
            total = self.total_days * self.daily_logging_volume
            return already_generated / total

    def start_bulk(self, bulk_size):
        self._time_interval_current_bulk = 1 / bulk_size
        self._timestruct = self._timestamp_generator.next_timestamp()
        self._index_name = self.__generate_index_pattern(self._timestruct)

    def generate_event(self):
        if self.remaining_days == 0:
            raise StopIteration()

        # advance time by a few micros
        self._timestruct = self._timestamp_generator.simulate_tick(self._time_interval_current_bulk)
        # index for the current line - we may cross a date boundary later if we're above the daily logging volume
        index = self._index_name
        event = self._event
        event["@timestamp"] = self._timestruct["iso"]

        # assume a typical event size of 263 bytes but limit the file size to 4GB
        event["offset"] = (self._offset + 263) % (4 * 1024 * 1024 * 1024)

        self._agent.add_fields(event)
        self._clientip.add_fields(event)
        self._referrer.add_fields(event)
        self._request.add_fields(event)

        event["hostname"] = "web-%s-%s.elastic.co" % (event["geoip_continent_code"], next(self._web_host))

        if self.record_raw_event_size or self.daily_logging_volume:
            # determine the raw event size (as if this were contained in nginx log file). We do not bother to
            # reformat the timestamp as this is not worth the overhead.
            raw_event = '%s - - [%s] "%s %s HTTP/%s" %s %s "%s" "%s"' % (event["clientip"], event["@timestamp"],
                                                                         event["verb"], event["request"],
                                                                         event["httpversion"], event["response"],
                                                                         event["bytes"], event["referrer"],
                                                                         event["agent"])
            if self.daily_logging_volume:
                self.current_logging_volume += len(raw_event)
                if self.current_logging_volume > self.daily_logging_volume:
                    if self.remaining_days is not None:
                        self.remaining_days -= 1
                    self._timestamp_generator.skip(datetime.timedelta(days=1))
                    # advance time now for real (we usually use #simulate_tick() which will keep everything except for
                    # microseconds constant.
                    self._timestruct = self._timestamp_generator.next_timestamp()
                    self._index_name = self.__generate_index_pattern(self._timestruct)
                    self.current_logging_volume = 0

        if self.record_raw_event_size:
            # we are on the hot code path here and thus we want to avoid conditionally creating strings so we duplicate
            # the event.
            line = '{"@timestamp": "%s", ' \
                   '"_raw_event_size":%d, ' \
                   '"offset":%s, ' \
                   '"source":"/usr/local/var/log/nginx/access.log","fileset":{"module":"nginx","name":"access"},"input":{"type":"log"},' \
                   '"beat":{"version":"6.3.0","hostname":"%s","name":"%s"},' \
                   '"prospector":{"type":"log"},' \
                   '"nginx":{"access":{"user_name": "-",' \
                   '"agent":"%s","user_agent": {"major": "%s","os": "%s","os_major": "%s","name": "%s","os_name": "%s","device": "%s"},' \
                   '"remote_ip": "%s","remote_ip_list":["%s"],' \
                   '"geoip":{"continent_name": "%s","city_name": "%s","country_name": "%s","country_iso_code": "%s","location":{"lat": %s,"lon": %s} },' \
                   '"referrer":"%s",' \
                   '"url": "%s","body_sent":{"bytes": %s},"method":"%s","response_code":%s,"http_version":"%s"} } }' % \
                   (event["@timestamp"],
                    len(raw_event),
                    event["offset"],
                    event["hostname"],event["hostname"],
                    event["agent"], event["useragent_major"], event["useragent_os"], event["useragent_os_major"], event["useragent_name"], event["useragent_os_name"], event["useragent_device"],
                    event["clientip"], event["clientip"],
                    event["geoip_continent_name"], event["geoip_city_name"], event["geoip_country_name"], event["geoip_country_iso_code"], event["geoip_location_lat"], event["geoip_location_lon"],
                    event["referrer"],
                    event["request"], event["bytes"], event["verb"], event["response"], event["httpversion"])
        else:
            line = '{"@timestamp": "%s", ' \
                   '"offset":%s, ' \
                   '"source":"/usr/local/var/log/nginx/access.log","fileset":{"module":"nginx","name":"access"},"input":{"type":"log"},' \
                   '"beat":{"version":"6.3.0","hostname":"%s","name":"%s"},' \
                   '"prospector":{"type":"log"},' \
                   '"nginx":{"access":{"user_name": "-",' \
                   '"agent":"%s","user_agent": {"major": "%s","os": "%s","os_major": "%s","name": "%s","os_name": "%s","device": "%s"},' \
                   '"remote_ip": "%s","remote_ip_list":["%s"],' \
                   '"geoip":{"continent_name": "%s","city_name": "%s","country_name": "%s","country_iso_code": "%s","location":{"lat": %s,"lon": %s} },' \
                   '"referrer":"%s",' \
                   '"url": "%s","body_sent":{"bytes": %s},"method":"%s","response_code":%s,"http_version":"%s"} } }' % \
                   (event["@timestamp"],
                    event["offset"],
                    event["hostname"],event["hostname"],
                    event["agent"], event["useragent_major"], event["useragent_os"], event["useragent_os_major"], event["useragent_name"], event["useragent_os_name"], event["useragent_device"],
                    event["clientip"], event["clientip"],
                    event["geoip_continent_name"], event["geoip_city_name"], event["geoip_country_name"], event["geoip_country_iso_code"], event["geoip_location_lat"], event["geoip_location_lon"],
                    event["referrer"],
                    event["request"], event["bytes"], event["verb"], event["response"], event["httpversion"])

        return line, index, self._type

    def __generate_index_pattern(self, timestruct):
        if self._index_pattern:
            return self._index.format(ts=timestruct)
        else:
            return self._index
