import uuid
import enum

from sqlalchemy import Column, types, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from proto import calendar_pb2
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    login = Column(types.String, primary_key=True)


class RepititionRule(enum.Enum):
    NONE = 0
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    YEARLY = 4

    @staticmethod
    def from_proto(proto: calendar_pb2.RepititionRule) -> 'RepititionRule':
        if proto == calendar_pb2.RepititionRule.NONE:
            return RepititionRule.NONE
        elif proto == calendar_pb2.RepititionRule.DAILY:
            return RepititionRule.DAILY
        elif proto == calendar_pb2.RepititionRule.WEEKLY:
            return RepititionRule.WEEKLY
        elif proto == calendar_pb2.RepititionRule.MONTHLY:
            return RepititionRule.MONTHLY
        elif proto == calendar_pb2.RepititionRule.YEARLY:
            return RepititionRule.YEARLY
        assert False, f'Unknown repitition rule: {proto}'


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author = Column(types.String, ForeignKey('users.login'))

    start_time = Column(types.DateTime)
    end_time = Column(types.DateTime)
    repitition_rule = Column(Enum(RepititionRule), default=RepititionRule.NONE)

    participants = relationship(
        'UserEvent', cascade='all, delete-orphan', back_populates='event')


class UserEvent(Base):
    __tablename__ = "userevents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user = Column(types.String, ForeignKey('users.login'))
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'))
    event = relationship('Event', back_populates='participants')
