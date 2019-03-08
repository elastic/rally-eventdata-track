import gzip
import json
import logging
import os
import random
import re
from eventdata.utils import elasticlogs_bulk_source as ebs
from eventdata.parameter_sources.weightedarray import WeightedArray
from eventdata.parameter_sources.timeutils import TimestampStructGenerator

cwd = os.path.dirname(__file__)
logger = logging.getLogger("track.eventdata.randomevent")


class Agent:
    def __init__(self, params):
        self._has_pipeline = True if 'pipeline' in params.keys() else False
        
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
        event['agent'] = self.__get_lookup_value(self._agent_lookup, agent[6])

        if self._has_pipeline is False :
            event['useragent_name'] = self.__get_lookup_value(self._agents_name_lookup, agent[0])
            event['useragent_os'] = self.__get_lookup_value(self._agents_os_lookup, agent[1])
            event['useragent_os_name'] = self.__get_lookup_value(self._agents_os_name_lookup, agent[2])
            event['useragent_device'] = self.__get_lookup_value(self._agents_device_lookup, agent[3])
            event['useragent_os_major'] = self.__get_lookup_value(self._agents_os_major_lookup, agent[4])
            event['useragent_major'] = self.__get_lookup_value(self._agents_major_lookup, agent[5])

            
    def __get_lookup_value(self, lookup, key):
        if key == "":
            return key
        else :
            return lookup[key]


class ClientIp:
    def __init__(self, params):
        self._has_pipeline = True if 'pipeline' in params.keys() else False
        
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

        if self._has_pipeline is False :
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


class RandomEvent:
    def __init__(self, params):
        self._has_pipeline = True if "pipeline" in params.keys() else False
        self._agent = Agent(params)
        self._clientip = ClientIp(params)
        self._referrer = Referrer()
        self._request = Request()
        # We will reuse the event dictionary. This assumes that each field will be present (and thus overwritten) in each event.
        # This reduces object churn and improves peak indexing throughput.
        self._event = {}

        self._index = 'elasticlogs'
        self._index_pattern = False
        if 'index' in params.keys():
            index = re.sub(r'<\s*yyyy\s*>', '{ts[yyyy]}', params['index'], flags=re.IGNORECASE)
            index = re.sub(r'<\s*yy\s*>', '{ts[yy]}', index, flags=re.IGNORECASE)
            index = re.sub(r'<\s*mm\s*>', '{ts[mm]}', index, flags=re.IGNORECASE)
            index = re.sub(r'<\s*dd\s*>', '{ts[dd]}', index, flags=re.IGNORECASE)
            index = re.sub(r'<\s*hh\s*>', '{ts[hh]}', index, flags=re.IGNORECASE)

            self._index = index
            self._index_pattern = True

        self._type = 'doc'

        if 'starting_point' in params.keys():
            sp = params['starting_point']
        else:
            sp = "now"

        if 'end_point' in params.keys():
            ep = params['end_point']
            self._timestamp_generator = TimestampStructGenerator.Interval(sp, ep)
        else:
            if 'acceleration_factor' in params.keys():
                af = float(params['acceleration_factor'])
                self._timestamp_generator = TimestampStructGenerator.StartingPoint(sp, af)
            else:
                self._timestamp_generator = TimestampStructGenerator.StartingPoint(sp)

        self._delete_fields = []
        if 'delete_fields' in params.keys():
            for d in params['delete_fields']:
                self._delete_fields.append(d.split('.'))

    def generate_event(self):
        timestruct = self._timestamp_generator.generate_timestamp_struct()
        index_name = self.__generate_index_pattern(timestruct)

        event = self._event
        event["@timestamp"] = timestruct["iso"]

        # set random offset
        event["offset"] = random.randrange(0,10000000)

        self._agent.add_fields(event)
        self._clientip.add_fields(event)
        self._referrer.add_fields(event)
        self._request.add_fields(event)

        # set host name
        event["hostname"] = "web-{}-{}.elastic.co".format("global",random.randrange(1,3))

        line = {
            "@timestamp": event['@timestamp'],
            "offset": event['offset'],
            "source": "/usr/local/var/log/nginx/access.log",
            "fileset": {"module": "nginx", "name": "access"},
            "input": {"type": "log"},
            "beat": {"version": "6.3.0", "hostname": event['hostname'], "name": event['hostname']},
            "prospector": {"type": "log"},
            "nginx": {
                "access": {
                    "user_name": "-",
                    "agent": event['agent'],
                    "remote_ip": event['clientip'],
                    "remote_ip_list": [event['clientip']],
                    "referrer": event['referrer'],
                    "url": event['request'],
                    "body_sent": {"bytes": event['bytes']},
                    "method": event['verb'],
                    "response_code": event['response'],
                    "http_version": event['httpversion']
                }
            }
        }
        if self._has_pipeline is False:
            line['beat']['hostname']= "web-{}-{}.elastic.co".format(event['geoip_continent_name'],random.randrange(1,3))
            line['nginx']['access']['user_agent'] = {
                "name": event['useragent_name'],
                "original": event['agent'],
                "os": {
                    "name": event['useragent_os_name'],
                    "version": event['useragent_os_major'],
                    "full": event['useragent_os']
                },
                "device": {
                    "name": event['useragent_device']
                },
                "version": ""

            }
            line['nginx']['access']['geoip'] = {
                "continent_name": event['geoip_continent_name'],
                "city_name": event['geoip_city_name'],
                "country_name": event['geoip_country_name'],
                "country_iso_code": event['geoip_country_iso_code'],
                "location": {
                    "lat": event['geoip_location_lat'],
                    "lon": event['geoip_location_lon']
                }
            }
        return json.dumps(line), index_name, self._type

    def __generate_index_pattern(self, timestruct):
        if self._index_pattern:
            return self._index.format(ts=timestruct)
        else:
            return self._index
