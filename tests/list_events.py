from tests.conftest import Server
from proto.calendar_pb2 import RepititionRule
import datetime
import httpx
import pytest


def test_not_repeated(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.NONE)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 1, 10))
    assert len(resp.events) == 1
    event = resp.events[0]
    assert event.user == 'kek'
    assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 1)
    assert event.end_time.ToDatetime() == datetime.datetime(2023, 1, 1, 1)
    assert event.participants == ['kek']


def test_repeated_daily(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.DAILY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 1, 10))
    assert len(resp.events) == 9
    for i, event in enumerate(resp.events):
        assert event.user == 'kek'
        assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 1) + \
            datetime.timedelta(days=i)
        assert event.end_time.ToDatetime() == datetime.datetime(
            2023, 1, 1, 1) + datetime.timedelta(days=i)
        assert event.participants == ['kek']


def test_repeated_daily_not_found(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.DAILY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1, 2), till=datetime.datetime(2023, 1, 1, 3))
    assert len(resp.events) == 0


def test_repeated_daily_interval_on_border(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1, 5), end_time=datetime.datetime(2023, 1, 1, 6), repitition_rule=RepititionRule.DAILY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1, 1), till=datetime.datetime(2023, 1, 2, 4))
    assert len(resp.events) == 1
    event = resp.events[0]
    assert event.user == 'kek'
    assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 1, 5)
    assert event.end_time.ToDatetime() == datetime.datetime(2023, 1, 1, 6)
    assert event.participants == ['kek']


def test_repeated_weekly(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.WEEKLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 1, 10))
    assert len(resp.events) == 2
    for i, event in enumerate(resp.events):
        assert event.user == 'kek'
        assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 1) + \
            datetime.timedelta(days=i*7)
        assert event.end_time.ToDatetime() == datetime.datetime(
            2023, 1, 1, 1) + datetime.timedelta(days=i*7)
        assert event.participants == ['kek']


def test_repeated_weekly_on_border(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.WEEKLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 1, 6))
    assert len(resp.events) == 1
    event = resp.events[0]
    assert event.user == 'kek'
    assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 1)
    assert event.end_time.ToDatetime() == datetime.datetime(2023, 1, 1, 1)
    assert event.participants == ['kek']


def test_repeated_monthly(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 1, 1), repitition_rule=RepititionRule.MONTHLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 2, 10))
    assert len(resp.events) == 2
    for event in resp.events:
        assert event.user == 'kek'
        assert event.start_time.ToDatetime().day == 1
        assert event.end_time.ToDatetime().day == 1
        assert event.end_time.ToDatetime(
        ) - event.start_time.ToDatetime() == datetime.timedelta(hours=1)
        assert event.participants == ['kek']


def test_repeated_monthly_wrong_date(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 31), end_time=datetime.datetime(
        2023, 1, 31, 1), repitition_rule=RepititionRule.MONTHLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 31), till=datetime.datetime(2023, 4, 1))
    assert len(resp.events) == 2
    for i, event in enumerate(resp.events):
        assert event.user == 'kek'
        assert event.start_time.ToDatetime().day == 31
        assert event.end_time.ToDatetime().day == 31
        assert event.end_time.ToDatetime(
        ) - event.start_time.ToDatetime() == datetime.timedelta(hours=1)
        assert event.participants == ['kek']


def test_repeated_monthly_on_border(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 25), end_time=datetime.datetime(
        2023, 1, 25, 1), repitition_rule=RepititionRule.MONTHLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 1, 24), till=datetime.datetime(2023, 2, 24))
    assert len(resp.events) == 1
    event = resp.events[0]
    assert event.user == 'kek'
    assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 25)
    assert event.end_time.ToDatetime() == datetime.datetime(2023, 1, 25, 1)
    assert event.participants == ['kek']


def test_repeated_in_the_future(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 25), end_time=datetime.datetime(
        2023, 1, 25, 1), repitition_rule=RepititionRule.MONTHLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2024, 1, 24), till=datetime.datetime(2024, 2, 24))
    assert len(resp.events) == 0


def test_list_events_wrong_args(client: Server):
    with pytest.raises(httpx.HTTPStatusError) as e:
        client.list_events('kek', till=datetime.datetime(
            2024, 1, 24), since=datetime.datetime(2024, 2, 24))
    assert e.value.response.status_code == 400


def test_multiuser(client: Server):
    client.create_user('kek')
    client.create_user('lol')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 1, 1), repitition_rule=RepititionRule.NONE, users=['lol'])
    resp_kek = client.list_events('kek', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 1, 10))
    resp_lol = client.list_events('lol', since=datetime.datetime(
        2023, 1, 1), till=datetime.datetime(2023, 1, 10))
    assert resp_kek == resp_lol
    assert len(resp_kek.events) == 1
    event = resp_lol.events[0]
    assert event.user == 'kek'
    assert event.start_time.ToDatetime() == datetime.datetime(2023, 1, 1)
    assert event.end_time.ToDatetime() == datetime.datetime(2023, 1, 1, 1)
    assert sorted(event.participants) == sorted(['kek', 'lol'])


def test_yearly(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(2023, 1, 1), end_time=datetime.datetime(
        2023, 1, 1, 1), repitition_rule=RepititionRule.YEARLY)
    resp = client.list_events('kek', since=datetime.datetime(
        2023, 12, 30), till=datetime.datetime(2024, 1, 10))
    assert len(resp.events) == 1
    event = resp.events[0]
    assert event.user == 'kek'
    assert event.start_time.ToDatetime() == datetime.datetime(2024, 1, 1)
    assert event.end_time.ToDatetime() == datetime.datetime(2024, 1, 1, 1)
    assert event.participants == ['kek']
