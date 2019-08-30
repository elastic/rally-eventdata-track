import json
from datetime import datetime

import pytest

from eventdata.parameter_sources.randomevent import RandomEvent, convert_to_bytes


# Adds all relevant fields for an event
class StaticAgent:
    def add_fields(self, event):
        event["useragent_name"] = "Chrome"
        event["useragent_os"] = "MacOS"
        event["useragent_os_name"] = "MacOS"
        event["useragent_device"] = "Intel Mac"
        event["useragent_os_major"] = "10"
        event["useragent_major"] = "60"
        event[
            "agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.66 Safari/537.36"


class StaticClientIp:
    def add_fields(self, event):
        event["clientip"] = "127.0.0.1"
        event["geoip_location_lat"] = "0"
        event["geoip_location_lon"] = "0"
        event["geoip_city_name"] = "Munich"
        event["geoip_country_name"] = "Germany"
        event["geoip_country_iso_code"] = "DE"
        event["geoip_continent_name"] = "Europe"
        event["geoip_continent_code"] = "1"


class StaticReferrer:
    def add_fields(self, event):
        event["referrer"] = "https://www.google.com"


class StaticRequest:
    def add_fields(self, event):
        event["request"] = "current/doc-values.html"
        event["bytes"] = "3204"
        event["verb"] = "GET"
        event["response"] = "200"
        event["httpversion"] = "1.1"


def test_random_event_no_event_size_by_default():
    e = RandomEvent(params={
        "index": "logs",
        "starting_point": "2019-01-05 15:00:00",
    },
        agent=StaticAgent,
        client_ip=StaticClientIp,
        referrer=StaticReferrer,
        request=StaticRequest)

    raw_doc, index, doc_type = e.generate_event()

    doc = json.loads(raw_doc)
    assert "_raw_event_size" not in doc
    assert index == "logs"
    assert doc_type == "doc"


def test_random_event_with_event_size():
    e = RandomEvent(params={
        "index": "logs",
        "starting_point": "2019-01-05 15:00:00",
        "record_raw_event_size": True,
        # we need a constant point in time to ensure a stable event size
        "__utc_now": lambda: datetime(year=2019, month=6, day=17)
    },
        agent=StaticAgent,
        client_ip=StaticClientIp,
        referrer=StaticReferrer,
        request=StaticRequest)

    raw_doc, index, doc_type = e.generate_event()

    doc = json.loads(raw_doc)
    assert doc["_raw_event_size"] == 236
    assert index == "logs"
    assert doc_type == "doc"


def test_random_events_with_daily_logging_volume():
    e = RandomEvent(params={
        "index": "logs-<yyyy><mm><dd>",
        "starting_point": "2019-01-05 15:00:00",
        # 1kB of data per client before we will rollover to the next day
        "daily_logging_volume": "8kB",
        "client_count": 8,
        # we need a constant point in time to ensure a stable event size
        "__utc_now": lambda: datetime(year=2019, month=6, day=17)
    },
        agent=StaticAgent,
        client_ip=StaticClientIp,
        referrer=StaticReferrer,
        request=StaticRequest)

    # 5 events fit into one kilobyte
    for i in range(5):
        doc, index, _ = e.generate_event()
        assert index == "logs-20190105"
    for i in range(5):
        doc, index, _ = e.generate_event()
        assert index == "logs-20190106"
    for i in range(5):
        doc, index, _ = e.generate_event()
        assert index == "logs-20190107"


def test_random_events_with_daily_logging_volume_and_maximum_days():
    e = RandomEvent(params={
        "index": "logs-<yyyy><mm><dd>",
        "starting_point": "2019-01-05 15:00:00",
        # 1kB of data per client before we will rollover to the next day
        "daily_logging_volume": "8192",
        "number_of_days": 2,
        "client_count": 8,
        # we need a constant point in time to ensure a stable event size
        "__utc_now": lambda: datetime(year=2019, month=6, day=17)
    },
        agent=StaticAgent,
        client_ip=StaticClientIp,
        referrer=StaticReferrer,
        request=StaticRequest)

    # 5 events fit into one kilobyte
    for i in range(5):
        doc, index, _ = e.generate_event()
        assert index == "logs-20190105"
    for i in range(5):
        doc, index, _ = e.generate_event()
        assert index == "logs-20190106"
    # no more events allowed on the next day
    with pytest.raises(StopIteration):
        doc, index, _ = e.generate_event()
        print(index)



def test_convert_bytes_to_bytes():
    assert convert_to_bytes("3") == 3
    assert convert_to_bytes("3786234876") == 3786234876


def test_convert_kb_to_bytes():
    assert convert_to_bytes("3 kB") == 3 * 1024
    assert convert_to_bytes("3972 kB") == 3972 * 1024


def test_convert_mb_to_bytes():
    assert convert_to_bytes("100 MB") == 100 * 1024 * 1024
    assert convert_to_bytes("10MB") == 10 * 1024 * 1024


def test_convert_gb_to_bytes():
    assert convert_to_bytes("3 GB") == 3 * 1024 * 1024 * 1024


def test_convert_invalid_to_bytes():
    with pytest.raises(ValueError) as ex:
        convert_to_bytes("3.4")

    assert "Invalid byte size value [3.4]" == str(ex.value)

    with pytest.raises(ValueError) as ex:
        convert_to_bytes("3gb")

    assert "Invalid byte size value [3gb]" == str(ex.value)


