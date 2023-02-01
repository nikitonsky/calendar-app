from tests.conftest import Server
import pytest
import httpx


def test_create_user(client: Server):
    client.create_user('kek')


def test_create_user_exists(client: Server):
    client.create_user('kek')
    with pytest.raises(httpx.HTTPStatusError) as e:
        client.create_user('kek')
    assert e.value.response.status_code == 409


def test_create_user_trash_request(client: Server):
    with pytest.raises(httpx.HTTPStatusError) as e:
        client.post('/create_user', content=b'kek')
    assert e.value.response.status_code == 400
