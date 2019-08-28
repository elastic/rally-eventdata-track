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


import gzip
import json
import re
import os

import logging

logger = logging.getLogger("track.elasticlogs")

regex = re.compile('\.gz$')

def load_data_files(files):
    if isinstance(files, list):
        file_list = files
    elif isinstance(files, str):
        file_list = [files]

    logger.info("[load_data_files] Files to load: {}".format(file_list))

    records = []

    for file in file_list:
        file_path = os.path.expandvars(file)

        logger.info("[load_data_files] Process file: {}".format(file_path))

        if regex.match(file_path):
            data = gzip.open(file_path, 'rt').read()
        else:
            data = open(file_path, 'rt').read()

        try:
            json_array = json.loads(data)
            logger.info("[load_data_files] {} records read from JSON array".format(len(json_array)))
        except ValueError:
            json_array = __process_json_lines(data)
            logger.info("[load_data_files] {} records read from JSON lines".format(len(json_array)))

        records.extend(json_array)

    return records

def __process_json_lines(data):
    lines = data.split('\n')

    recs = []

    for line in lines:
        json_object = json.loads(line)
        recs.append(json_object)

    return recs
