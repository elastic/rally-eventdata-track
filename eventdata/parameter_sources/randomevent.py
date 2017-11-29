import json
import random
import gzip
import re
import os
from eventdata.parameter_sources.weightedarray import WeightedArray
from eventdata.parameter_sources.timeutils import TimestampStructGenerator

cwd = os.path.dirname(__file__)


class Agent:
    def __init__(self):
        self._agents = WeightedArray('%s/data/agents.json.gz' % cwd)

        with gzip.open('%s/data/agents_name_lookup.json.gz' % cwd, 'rt') as data_file:
            self._agents_name_lookup = json.load(data_file)

        with gzip.open('%s/data/agents_os_lookup.json.gz' % cwd, 'rt') as data_file:
            self._agents_os_lookup = json.load(data_file)

        with gzip.open('%s/data/agents_os_name_lookup.json.gz' % cwd, 'rt') as data_file:
            self._agents_os_name_lookup = json.load(data_file)

    def add_fields(self, event):
        agent = self._agents.get_random()

        event['agent'] = agent[0]
        event['useragent_os'] = self._agents_os_lookup[agent[1]]
        event['useragent_os_name'] = self._agents_os_name_lookup[agent[2]]
        event['useragent_name'] = self._agents_name_lookup[agent[3]]


class ClientIp:
    def __init__(self):
        self._rare_clientip_probability = 0.269736965199
        self._clientips = WeightedArray('%s/data/clientips.json.gz' % cwd)
        self._rare_clientips = WeightedArray('%s/data/rare_clientips.json.gz' % cwd)

        with gzip.open('%s/data/clientips_country_lookup.json.gz' % cwd, 'rt') as data_file:
            self._clientips_country_lookup = json.load(data_file)

        with gzip.open('%s/data/clientips_location_lookup.json.gz' % cwd, 'rt') as data_file:
            self._clientips_location_lookup = json.load(data_file)

    def add_fields(self, event):
        p = random.random()
        if p < self._rare_clientip_probability:
            data = self._rare_clientips.get_random()
            event['clientip'] = self.__fill_out_ip_prefix(data[0])
        else:
            data = self._clientips.get_random()
            event['clientip'] = data[0]

        event['country_name'] = self._clientips_country_lookup[data[1]]
        event['location'] = self._clientips_location_lookup[data[2]]

    def __fill_out_ip_prefix(self, ip_prefix):
        rnd1 = random.random()
        v1 = rnd1 * (1 - rnd1) * 255 * 4
        k1 = (int)(v1)
        rnd2 = random.random()
        v2 = rnd2 * (1 - rnd2) * 255 * 4
        k2 = (int)(v2)

        return "{}.{}.{}".format(ip_prefix, k1, k2)


class Referrer:
    def __init__(self):
        self._referrers = WeightedArray('%s/data/referrers.json.gz' % cwd)

        with gzip.open('%s/data/referrers_url_base_lookup.json.gz' % cwd, 'rt') as data_file:
            self._referrers_url_base_lookup = json.load(data_file)

    def add_fields(self, event):
        data = self._referrers.get_random()
        event['referrer'] = "%s%s" % (self._referrers_url_base_lookup[data[0]], data[1])


class Request:
    def __init__(self):
        self._requests = WeightedArray('%s/data/requests.json.gz' % cwd)

        with gzip.open('%s/data/requests_url_base_lookup.json.gz' % cwd, 'rt') as data_file:
            self._requests_url_base_lookup = json.load(data_file)

    def add_fields(self, event):
        data = self._requests.get_random()
        event['request'] = "{}{}".format(self._requests_url_base_lookup[data[0]], data[1])
        event['bytes'] = data[2]
        event['verb'] = data[3]
        event['response'] = data[4]
        event['httpversion'] = data[5]


class RandomEvent:
    def __init__(self, params):
        self._agent = Agent()
        self._clientip = ClientIp()
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

        self._type = 'logs'
        if 'type' in params.keys():
            self._type = params['type']

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

        self._agent.add_fields(event)
        self._clientip.add_fields(event)
        self._referrer.add_fields(event)
        self._request.add_fields(event)

        if 'message' not in self._delete_fields:
            # note the leading comma!
            message = ',"message":"%s"' % self.__generate_message_field(event)
        else:
            message = ''

        line = '{"@timestamp": "%s", ' \
               '"agent":"%s","useragent":{"os":"%s","os_name":"%s","name":"%s"},' \
               '"clientip":"%s","geoip":{"country_name":"%s","location":%s},' \
               '"referrer":"%s",' \
               '"request": "%s","bytes":%s,"verb":"%s","response":%s,"httpversion":"%s"' \
               '%s}' % \
               (event["@timestamp"],
                event["agent"], event["useragent_os"], event["useragent_os_name"], event["useragent_name"],
                event["clientip"], event["country_name"], event["location"],
                event["referrer"],
                event["request"], event["bytes"], event["verb"], event["response"], event["httpversion"],
                message)

        return line, index_name, self._type

    def __generate_index_pattern(self, timestruct):
        if self._index_pattern:
            return self._index.format(ts=timestruct)
        else:
            return self._index

    def __generate_message_field(self, event):
        return '{} - - [{}] \\"{} {} HTTP/{}\\" {} {} \\"-\\" {} {}'.format(event['clientip'], event['@timestamp'], event['verb'],
                                                                            event['request'], event['httpversion'], event['response'],
                                                                            event['bytes'], event['referrer'], event['agent'])
