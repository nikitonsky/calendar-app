import datetime
from tests.conftest import Server
from proto.calendar_pb2 import RepititionRule
import pytest
import httpx


def test_create_event(client: Server):
    client.create_user('kek')
    client.create_event('kek', start_time=datetime.datetime(
        2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.NONE)


def test_create_event_unknown_user(client: Server):
    with pytest.raises(httpx.HTTPStatusError) as e:
        client.create_event('kek', start_time=datetime.datetime(
            2023, 1, 1), end_time=datetime.datetime(2023, 1, 1, 1), repitition_rule=RepititionRule.NONE)
    assert e.value.response.status_code == 400


def test_create_event_trash_request(client: Server):
    client.create_user('kek')
    with pytest.raises(httpx.HTTPStatusError) as e:
        client.post('/create_event', content=b'kek')
    assert e.value.response.status_code == 400
