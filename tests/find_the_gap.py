import datetime
from tests.conftest import Server
from proto.calendar_pb2 import RepititionRule
import pytest
import httpx


def test_empty(client: Server):
    client.create_user('kek')
    resp = client.find_the_gap(['kek'], datetime.datetime(
        2023, 1, 1), interval=datetime.timedelta(minutes=30))
    assert resp.start_time.ToDatetime() == datetime.datetime(2023, 1, 1)
    assert resp.end_time.ToDatetime() == datetime.datetime(2023, 1, 1, 0, 30)


def test_one_event(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.NONE)
    resp = client.find_the_gap(['kek'], datetime.datetime(
        2023, 1, 1), interval=datetime.timedelta(minutes=30))
    assert resp.start_time.ToDatetime() == datetime.datetime(2023, 1, 1, 1)
    assert resp.end_time.ToDatetime() == datetime.datetime(2023, 1, 1, 1, 30)


def test_gap_in_the_middle(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 5, 23, 30), repitition_rule=RepititionRule.NONE)
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 6), end_time=datetime.datetime(2023, 1, 8), repitition_rule=RepititionRule.NONE)
    resp = client.find_the_gap(['kek'], datetime.datetime(
        2023, 1, 1), interval=datetime.timedelta(minutes=30))
    assert resp.start_time.ToDatetime() == datetime.datetime(2023, 1, 5, 23, 30)
    assert resp.end_time.ToDatetime() == datetime.datetime(2023, 1, 6)


def test_small_gap(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 5, 23, 30), repitition_rule=RepititionRule.NONE)
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 6), end_time=datetime.datetime(2023, 1, 8), repitition_rule=RepititionRule.NONE)
    with pytest.raises(httpx.HTTPStatusError) as e:
        client.find_the_gap(['kek'], datetime.datetime(
            2023, 1, 1), interval=datetime.timedelta(hours=1))
    assert e.value.response.status_code == 404


def test_repeated(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 1, 23, 30), repitition_rule=RepititionRule.DAILY)
    resp = client.find_the_gap(['kek'], datetime.datetime(
        2023, 1, 1), interval=datetime.timedelta(minutes=30))
    assert resp.start_time.ToDatetime() == datetime.datetime(2023, 1, 1, 23, 30)
    assert resp.end_time.ToDatetime() == datetime.datetime(2023, 1, 2, 0, 0)


def test_repeated_and_not_repeated(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 1, 23, 30), repitition_rule=RepititionRule.DAILY)
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 15, 23, 30), end_time=datetime.datetime(
        2023, 1, 16), repitition_rule=RepititionRule.NONE)
    resp = client.find_the_gap(['kek'], datetime.datetime(
        2023, 1, 15), interval=datetime.timedelta(minutes=30))
    assert resp.start_time.ToDatetime() == datetime.datetime(2023, 1, 16, 23, 30)
    assert resp.end_time.ToDatetime() == datetime.datetime(2023, 1, 17, 0, 0)
