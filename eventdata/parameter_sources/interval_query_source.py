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
import json
import logging
import random
import copy

logger = logging.getLogger("track.eventdata")

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

class ParameterSourceError(Error):
    """Exception raised for runtime errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class IntervalQuerySource:
    """
    Adds range filter based on input from fieldstats_runner.

    It expects the parameter hash to contain the following keys:


        "body"                   -   Query body the range filter shouyld be added to. [Mandatory]
        "index_pattern"          -   String representing the index pattern to query. This is used to look up correct field statistics. Defaults to 'filebeat-*'.
        "type"                   -   Type to query within the index. Defaults to '*'.  
        "fieldname"              -   Name of the field to filter on. Defaults to '@timestamp'.
        "min_interval_size_pct"  -   Minimal percentage of the range to filter on. Parameter must be in the range 0 < min_interval_size_pct < 100. [Mandatory]
        "max_interval_size_pct"  -   Maximum percentage of the range to filter on. Parameter must be in the range min_interval_size_pct < min_interval_size_pct <= 100. [Mandatory]
        "cache"                  -   Boolean indicating whether request cache is to be used. Defaults to 'False'.

    This parameter source will take the query supplied through the 'body' parameter and add a range filter to it. This will be based on the field specified
    through the 'fieldname' parameter. The upper end of the range (range_max) will be set to the maximum value (fieldname_max) detected for the field through the fieldstats_runner.
    The lower end of the range (range_min) will be set based on the following calculation:

      range = fieldname_max - fieldname_min
      interval_size_pct = min_interval_size_pct + random(max_interval_size_pct - min_interval_size_pct)
      range_min = range_max - (range * interval_size_pct / 100)

    """
    def __init__(self, track, params, **kwargs):
        self._index_pattern = "filebeat-*";
        self._fieldname = "@timestamp";
        self._type = "*";
        self._cache = False;

        random.seed();
        if 'cache' in params.keys():
            self._cache = params['cache']

        if 'index_pattern' in params.keys():
            self._index_pattern = params['index_pattern']

        if 'type' in params.keys():
            self._type = params['type']
        
        if 'fieldname' in params.keys():
            self._fieldname = params['fieldname']

        if 'body' in params.keys():
            self._body = params['body']

            # Verify that body contains `query.bool.must` key.
            if not params['body'] or not params['body']['query'] or not params['body']['query']['bool'] or ('must' not in params['body']['query']['bool'].keys()):
                raise ConfigurationError("Parameter 'body' must contain `query.bool.must` key.");
        else:
            raise ConfigurationError("Parameter 'body' must be specified.");

        if 'min_interval_size_pct' in params.keys():
            self._min_interval_size_pct = float(params['min_interval_size_pct']);
            if self._min_interval_size_pct <= 0:
                raise ConfigurationError("Parameter 'min_interval_size_pct' must be > 0.");
            if self._min_interval_size_pct >= 100:
                raise ConfigurationError("Parameter 'min_interval_size_pct' must be < 100.");
        else:
            raise ConfigurationError("Parameter 'min_interval_size_pct' must be specified.");

        if 'max_interval_size_pct' in params.keys():
            self._max_interval_size_pct = float(params['max_interval_size_pct']);
            if self._max_interval_size_pct <= self._min_interval_size_pct:
                raise ConfigurationError("Parameter 'max_interval_size_pct' must be > 'min_interval_size_pct'.");
            if self._max_interval_size_pct > 100:
                raise ConfigurationError("Parameter 'max_interval_size_pct' must be <= 100.");
        else:
            raise ConfigurationError("Parameter 'max_interval_size_pct' must be specified.");

    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1

    def params(self):
        key = "{}_{}".format(self._index_pattern, self._fieldname);
        if key in gs.global_fieldstats.keys():
            stats = gs.global_fieldstats[key];
        else:
            raise ParameterSourceError("No statistics found for field `{}` in index pattern `{}`.".format(self._fieldname, self._index_pattern));

        range_max = stats['max'];
        range_min_upper = int(stats['max'] - ((stats['max'] - stats['min']) * self._min_interval_size_pct / 100.0));
        delta = (stats['max'] - stats['min']) * ((self._max_interval_size_pct - self._min_interval_size_pct) / 100.0);
        range_min = range_min_upper - int(delta * random.random());
        body = copy.deepcopy(self._body);

        # Rewrite query to include new range filter based on range_min and range_max.
        # This assumes that the body contains `query.bool.must` key.
        if not isinstance(body['query']['bool']['must'], list):
            body['query']['bool']['must'] = [ body['query']['bool']['must'] ];

        range_clause = {}
        range_clause['range'] = {}
        range_clause['range'][self._fieldname] = { 'gte': range_min, 'lte': range_max, 'format': 'epoch_millis'}
        body['query']['bool']['must'].append(range_clause);        

        logger.info("[interval_query] Interval generated for field `{}`: Min: {} [{}, {}], Max: {}".format(self._fieldname, range_min, stats['min'], range_min_upper, range_max));
 
        request = { 'index': self._index_pattern, 'type': self._type, 'body': body, 'cache': self._cache};

        return request;
