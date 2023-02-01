import pytest
import typing as tp
import os
from starlette.testclient import TestClient
from testcontainers.postgres import PostgresContainer
from src.main import app
from proto import calendar_pb2
import datetime
from google.protobuf import timestamp_pb2


@pytest.fixture
def postgres():
    container = PostgresContainer('postgres:15')
    with container as postgres:
        os.environ['DATABASE_URL'] = postgres.get_connection_url().replace(
            'psycopg2', 'asyncpg')
        yield postgres.get_connection_url()


@pytest.fixture
def client(postgres):
    with Server() as server:
        yield server


class Server(TestClient):
    def __init__(self):
        super(Server, self).__init__(app)

    def get(self, *args, **kwargs):
        resp = super(Server, self).get(*args, **kwargs)
        resp.raise_for_status()
        return resp

    def post(self, *args, **kwargs):
        resp = super(Server, self).post(*args, **kwargs)
        resp.raise_for_status()
        return resp

    def ping(self):
        self.get('/ping')

    def create_user(self, user: str):
        req = calendar_pb2.User(username=user)
        self.post('/create_user', content=req.SerializeToString())

    def create_event(self, user: str, start_time: datetime.datetime, end_time: datetime.datetime, repitition_rule: calendar_pb2.RepititionRule, users: tp.Optional[tp.List[str]] = None):
        start_time_proto = timestamp_pb2.Timestamp()
        start_time_proto.FromDatetime(start_time)
        end_time_proto = timestamp_pb2.Timestamp()
        end_time_proto.FromDatetime(end_time)
        if users is None:
            users = []
        req = calendar_pb2.Event(user=user, description='kek', start_time=start_time_proto,
                                 end_time=end_time_proto, repitition_rule=repitition_rule, participants=users)
        self.post('/create_event', content=req.SerializeToString())

    def list_events(self, user: str, since: datetime.datetime, till: datetime.datetime) -> calendar_pb2.ListEventsResp:
        resp = calendar_pb2.ListEventsResp()
        resp.ParseFromString(self.get(
            '/list_events', params={'user': user, 'since': since, 'till': till}).content)
        return resp

    def find_the_gap(self, users: tp.List[str], start: datetime.datetime, interval: datetime.timedelta) -> calendar_pb2.FindTheGapResponse:
        req = calendar_pb2.FindTheGapRequest()
        req.users.extend(users)
        req.since.FromDatetime(start)
        req.interval.FromTimedelta(interval)

        resp = calendar_pb2.FindTheGapResponse()
        resp.ParseFromString(
            self.post('/find_the_gap', content=req.SerializeToString()).content)
        return resp
