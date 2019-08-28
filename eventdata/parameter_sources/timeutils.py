import datetime
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
    def __init__(self, starting_point, end_point=None, acceleration_factor=1.0, utcnow=datetime.datetime.utcnow):
        self._start_dt = None
        self._starting_point = self.__parse_point_def(starting_point)
        if end_point is None:
            self._end_point = None
        else:
            self._end_point = self.__parse_point_def(end_point)
        self._acceleration_factor = acceleration_factor
        self._utcnow = utcnow
        # reuse to reduce object churn
        self._ts = {}

    def generate_timestamp_struct(self):
        if self._end_point is None:
            if self._starting_point["type"] == "relative":
                dt = self._utcnow() + self._starting_point["offset"]
            else:
                self.__set_start_dt_if_not_set()
                td = (self._utcnow() - self._start_dt) * self._acceleration_factor
                dt = self._starting_point["dt"] + td
        else:
            if self._starting_point["type"] == "relative":
                dt1 = self._utcnow() + self._starting_point["offset"]
            else:
                dt1 = self._starting_point["dt"]

            if self._end_point["type"] == "relative":
                dt2 = self._utcnow() + self._end_point["offset"]
            else:
                dt2 = self._end_point["dt"]

            interval_length = (dt2 - dt1)
            random_offset = interval_length * random.random()

            dt = dt1 + random_offset

        return self.__generate_timestamp_struct_from_datetime(dt)

    def __generate_timestamp_struct_from_datetime(self, dt):
        # string formatting is about 4 times faster than strftime.
        iso = "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
        self._ts["iso"] = iso
        self._ts["yyyy"] = iso[:4]
        self._ts["yy"] = iso[2:4]
        self._ts["mm"] = iso[5:7]
        self._ts["dd"] = iso[8:10]
        self._ts["hh"] = iso[11:13]
        return self._ts

    def __set_start_dt_if_not_set(self):
        if self._start_dt is None:
            self._start_dt = self._utcnow()

    def __parse_point_def(self, point):
        if point == "now":
            return {"type": "relative", "offset": datetime.timedelta()}

        match = re.match(r"^now([+-]\d+)([hmd])$", point)
        if match:
            offset = int(match.group(1))

            if match.group(2) == "m":
                return {'type': "relative", "offset": datetime.timedelta(minutes=offset)}

            if match.group(2) == "h":
                return {'type': "relative", "offset": datetime.timedelta(hours=offset)}

            if match.group(2) == "d":
                return {'type': "relative", "offset": datetime.timedelta(days=offset)}

        else:
            match = re.match(r"^(\d{4})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})$", point)
            if match:
                dt = datetime.datetime(year=int(match.group(1)),
                                       month=int(match.group(2)),
                                       day=int(match.group(3)),
                                       hour=int(match.group(4)),
                                       minute=int(match.group(5)),
                                       second=int(match.group(6)),
                                       tzinfo=datetime.timezone.utc)
                return {"type": "absolute", "dt": dt}

            else:
                match = re.match(r"^(\d{4})\D(\d{2})\D(\d{2})$", point)
                if match:
                    dt = datetime.datetime(year=int(match.group(1)),
                                           month=int(match.group(2)),
                                           day=int(match.group(3)),
                                           tzinfo=datetime.timezone.utc)
                    return {"type": "absolute", "dt": dt}

        raise TimeParsingError("Invalid time format: {}".format(point))
