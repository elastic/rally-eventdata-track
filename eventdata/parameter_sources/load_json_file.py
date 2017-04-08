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
