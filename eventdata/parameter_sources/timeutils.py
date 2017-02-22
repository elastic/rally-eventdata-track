import random
import math
import datetime
import calendar
import re
import random

epoch = datetime.datetime.utcfromtimestamp(0)

class TimeParsingError(Exception):
    """Exception raised for parameter parsing errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message

class TimestampStructGenerator:
    def __init__(self, starting_point, end_point=None, acceleration_factor=1.0):
        self._start_dt = None
        self._starting_point = self.__parse_point_def(starting_point)
        if(end_point == None):
            self._end_point = None
        else:
            self._end_point = self.__parse_point_def(end_point)
        self._acceleration_factor = acceleration_factor

    @classmethod
    def StartingPoint(cls, starting_point, acceleration_factor=1.0):
        return cls(starting_point, None, acceleration_factor)

    @classmethod
    def Interval(cls, starting_point, end_point):
        return cls(starting_point, end_point)

    def generate_timestamp_struct(self):
        if self._end_point == None:
            if self._starting_point['type'] == 'relative':
                dt = datetime.datetime.utcnow() + self._starting_point['offset']
            else:
                self.__set_start_dt_if_not_set()
                td = (datetime.datetime.utcnow() - self._start_dt) * self._acceleration_factor
                dt = self._starting_point['dt'] + td
        else:
            if self._starting_point['type'] == 'relative':
                dt1 = datetime.datetime.utcnow() + self._starting_point['offset']
            else:
                dt1 = self._starting_point['dt']

            if self._end_point['type'] == 'relative':
                dt2 = datetime.datetime.utcnow() + self._end_point['offset']
            else:
                dt2 = self._end_point['dt']

            interval_length = (dt2 - dt1)
            random_offset = interval_length * random.random()

            dt = dt1 + random_offset

        return self.__generate_timestamp_struct_from_datetime(dt)

    def __generate_timestamp_struct_from_datetime(self, dt):
        ts = {}
        ts['iso'] = "{}Z".format(dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])
        ts['yyyy'] = ts['iso'][:4]
        ts['yy'] = ts['iso'][2:4]
        ts['mm'] = ts['iso'][5:7]
        ts['dd'] = ts['iso'][8:10]
        ts['hh'] = ts['iso'][11:13]

        return ts

    def __set_start_dt_if_not_set(self):
        if self._start_dt == None:
            self._start_dt = datetime.datetime.utcnow()

    def __parse_point_def(self, point):
        if point == "now":
            return { 'type': "relative", 'offset': datetime.timedelta()}

        match = re.match("^now([+-]\d+)([hmd])$", point)
        if match:
            int_offset = int(match.group(1))
            
            if match.group(2) == "m":
                return { 'type': "relative", 'offset': datetime.timedelta(minutes=int_offset)}

            if match.group(2) == "h":
                return { 'type': "relative", 'offset': datetime.timedelta(hours=int_offset)}

            if match.group(2) == "d":
                return { 'type': "relative", 'offset': datetime.timedelta(days=int_offset)}

        else:
            match = re.match("^(\d{4})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})$", point)
            if match:
                dt = datetime.datetime.strptime('{} {} {} {} {} {} UTC'.format(match.group(1), match.group(2), match.group(3), match.group(4), match.group(5), match.group(6)), "%Y %m %d %H %M %S %Z")
                return { 'type': "absolute", 'dt': dt}

            else:
                match = re.match("^(\d{4})\D(\d{2})\D(\d{2})$", point)
                if match:
                    dt = datetime.datetime.strptime('{} {} {} 00 00 00 UTC'.format(match.group(1), match.group(2), match.group(3)), "%Y %m %d %H %M %S %Z")
                    return { 'type': "absolute", 'dt': dt}

        raise TimeParsingError("Invalid time format: {}".format(point))
