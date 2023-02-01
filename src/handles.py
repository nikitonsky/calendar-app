import datetime
from src.routing import route
from starlette.requests import Request
from starlette.responses import Response
from proto import calendar_pb2
from src import datamodel
from sqlalchemy import select, and_, or_, func
import sqlalchemy
from sqlalchemy.orm import selectinload
from dateutil.relativedelta import relativedelta
from google.protobuf.message import DecodeError
import typing as tp
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass


@route('/ping')
async def ping(request: Request):
    return Response(status_code=200)


@route('/create_user', 'POST')
async def create_user(request: Request):
    db = request.app.state.db

    req = calendar_pb2.User()
    try:
        req.ParseFromString(await request.body())
    except DecodeError:
        return Response(status_code=400, content='Broken post payload')

    try:
        async with db() as session:
            async with session.begin():
                user = datamodel.User(login=req.username)
                session.add(user)
            await session.commit()
    except sqlalchemy.exc.IntegrityError:
        return Response(status_code=409, content=f'Username {req.username} already exists')
    return Response(status_code=200)


@route('/create_event', 'POST')
async def create_event(request: Request):
    db = request.app.state.db

    req = calendar_pb2.Event()
    try:
        req.ParseFromString(await request.body())
    except DecodeError:
        return Response(status_code=400, content='Broken post payload')

    try:
        async with db() as session:
            async with session.begin():
                event = datamodel.Event(
                    author=req.user,
                    start_time=req.start_time.ToDatetime(),
                    end_time=req.end_time.ToDatetime(),
                    repitition_rule=datamodel.RepititionRule.from_proto(
                        req.repitition_rule)
                )
                session.add(event)

                event.participants.append(datamodel.UserEvent(
                    user=req.user, event_id=event.id))
                for user in req.participants:
                    event.participants.append(
                        datamodel.UserEvent(user=user, event_id=event.id))
            await session.commit()
    except sqlalchemy.exc.IntegrityError:
        return Response(status_code=400, content=f'Wrong username {req.user}')

    return Response(status_code=200)


@dataclass
class Event:
    author: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    participants: tp.List[str]


async def list_events_for_users(users: tp.List[str], db: AsyncSession, time_since: datetime.datetime, time_till: datetime.datetime) -> tp.AsyncGenerator[Event, None]:
    daily_repition_query = (
        datamodel.Event.repitition_rule == datamodel.RepititionRule.DAILY)
    if time_till - time_since >= datetime.timedelta(weeks=1):
        weekly_repitition_query = (
            datamodel.Event.repitition_rule == datamodel.RepititionRule.WEEKLY)
    else:
        if time_since.weekday() <= time_till.weekday():
            weekly_repitition_query = and_(
                datamodel.Event.repitition_rule == datamodel.RepititionRule.WEEKLY,
                func.extract(
                    'dow', datamodel.Event.start_time) >= time_since.weekday(),
                func.extract(
                    'dow', datamodel.Event.start_time) <= time_till.weekday(),
            )
        else:
            weekly_repitition_query = and_(
                datamodel.Event.repitition_rule == datamodel.RepititionRule.WEEKLY,
                or_(
                    func.extract(
                        'dow', datamodel.Event.start_time) >= time_since.weekday(),
                    func.extract(
                        'dow', datamodel.Event.start_time) <= time_till.weekday(),
                )
            )
    if relativedelta(time_till, time_since).months > 0:
        monthly_repitition_query = (
            datamodel.Event.repitition_rule == datamodel.RepititionRule.MONTHLY)
    else:
        if time_since.day <= time_till.day:
            monthly_repitition_query = and_(
                datamodel.Event.repitition_rule == datamodel.RepititionRule.MONTHLY,
                func.extract(
                    'day', datamodel.Event.start_time) >= time_since.day,
                func.extract(
                    'day', datamodel.Event.start_time) <= time_till.day,
            )
        else:
            monthly_repitition_query = and_(
                datamodel.Event.repitition_rule == datamodel.RepititionRule.MONTHLY,
                or_(
                    func.extract(
                        'day', datamodel.Event.start_time) >= time_since.day,
                    func.extract(
                        'day', datamodel.Event.start_time) <= time_till.day,
                )
            )

    if relativedelta(time_till, time_since).years > 0:
        yearly_repitition_query = (
            datamodel.Event.repitition_rule == datamodel.RepititionRule.YEARLY
        )
    else:
        if time_since.timetuple().tm_yday < time_since.timetuple().tm_yday:
            yearly_repitition_query = and_(
                datamodel.Event.repitition_rule == datamodel.RepititionRule.YEARLY,
                func.extract(
                    'doy', datamodel.Event.start_time) >= time_since.timetuple().tm_yday,
                func.extract(
                    'doy', datamodel.Event.end_time) <= time_till.timetuple().tm_yday
            )
        else:
            yearly_repitition_query = and_(
                datamodel.Event.repitition_rule == datamodel.RepititionRule.YEARLY,
                or_(
                    func.extract(
                        'doy', datamodel.Event.start_time) >= time_since.timetuple().tm_yday,
                    func.extract(
                        'doy', datamodel.Event.end_time) <= time_till.timetuple().tm_yday
                )
            )

    query = (select(datamodel.Event).where(
        and_(
            (datamodel.UserEvent.user == users[0]) if len(
                users) == 0 else (datamodel.UserEvent.user.in_(users)),
            datamodel.Event.start_time <= time_till,
            or_(
                and_(
                    datamodel.Event.repitition_rule == datamodel.RepititionRule.NONE,
                    datamodel.Event.start_time >= time_since,
                ),
                daily_repition_query,
                weekly_repitition_query,
                monthly_repitition_query,
                yearly_repitition_query
            )
        )
    )
        .join(datamodel.UserEvent, datamodel.Event.id == datamodel.UserEvent.event_id)
        .options(selectinload(datamodel.Event.participants))
    )

    result = await db.stream_scalars(query)
    async for row in result:
        participants = [participant.user for participant in row.participants]
        event_duration = row.end_time - row.start_time
        if row.repitition_rule == datamodel.RepititionRule.NONE:
            yield Event(
                author=row.author,
                start_time=row.start_time,
                end_time=row.end_time,
                participants=participants
            )
        elif row.repitition_rule == datamodel.RepititionRule.DAILY:
            for i in range((time_till - time_since).days):
                yield Event(
                    author=row.author,
                    start_time=datetime.datetime.combine(
                        time_since.date() + datetime.timedelta(days=i), row.start_time.time()),
                    end_time=datetime.datetime.combine(time_since.date(
                    ) + datetime.timedelta(days=i), row.start_time.time()) + event_duration,
                    participants=participants
                )
        elif row.repitition_rule == datamodel.RepititionRule.WEEKLY:
            this_event_start_time = row.start_time.replace(
                year=time_since.year, month=time_since.month, day=time_since.day)
            this_event_start_time += datetime.timedelta(
                days=(row.start_time.weekday() - time_since.weekday() + 7) % 7)
            if this_event_start_time < time_since:
                continue
            while this_event_start_time <= time_till:
                yield Event(
                    author=row.author,
                    start_time=this_event_start_time,
                    end_time=this_event_start_time + event_duration,
                    participants=participants
                )
                this_event_start_time += datetime.timedelta(days=7)
        elif row.repitition_rule == datamodel.RepititionRule.MONTHLY:
            for i in range(relativedelta(time_since, row.start_time.date()).months, relativedelta(time_till, row.start_time.date()).months + 1):
                this_event_start_time = row.start_time + \
                    relativedelta(months=i)
                if this_event_start_time.day != row.start_time.day:
                    continue
                if this_event_start_time < time_since:
                    continue
                if this_event_start_time > time_till:
                    continue
                yield Event(
                    author=row.author,
                    start_time=this_event_start_time,
                    end_time=this_event_start_time + event_duration,
                    participants=participants
                )
        elif row.repitition_rule == datamodel.RepititionRule.YEARLY:
            for i in range(relativedelta(time_since, row.start_time.date()).years, relativedelta(time_till, row.start_time.date()).years + 1):
                this_event_start_time = row.start_time + \
                    relativedelta(years=i)
                if this_event_start_time.day != row.start_time.day and this_event_start_time.month != row.start_time.month:
                    continue
                if this_event_start_time < time_since:
                    continue
                if this_event_start_time > time_till:
                    continue
                yield Event(
                    author=row.author,
                    start_time=this_event_start_time,
                    end_time=this_event_start_time + event_duration,
                    participants=participants
                )


@route('/list_events', 'GET')
async def list_events(request: Request):
    username = request.query_params['user']

    db = request.app.state.db

    time_since = datetime.datetime.fromisoformat(request.query_params['since'])
    time_till = datetime.datetime.fromisoformat(request.query_params['till'])

    if time_till <= time_since:
        return Response(status_code=400, content='time_till <= time_since')

    resp = calendar_pb2.ListEventsResp()

    async with db() as session:
        async with session.begin():
            async for event in list_events_for_users([username], session, time_since, time_till):
                elem: calendar_pb2.Event = resp.events.add()
                elem.user = event.author
                elem.start_time.FromDatetime(event.start_time)
                elem.end_time.FromDatetime(event.end_time)
                elem.participants.extend(event.participants)

    return Response(status_code=200, content=resp.SerializeToString())


@route('/find_the_gap', 'POST')
async def find_the_gap(request: Request):
    db = request.app.state.db

    req = calendar_pb2.FindTheGapRequest()
    req.ParseFromString(await request.body())

    duration = req.interval.ToTimedelta()

    if duration > datetime.timedelta(days=1):
        return Response(status_code=400, content=f'You are doing wrong, interval {duration} is too big')

    async with db() as session:
        async with session.begin():
            events = [event async for event in list_events_for_users(req.users, session, req.since.ToDatetime(), req.since.ToDatetime() + datetime.timedelta(days=7))]

    event_starts = [event.start_time for event in events]
    event_ends = [event.end_time for event in events]

    event_starts.sort()
    event_ends.sort()

    resp = calendar_pb2.FindTheGapResponse()
    if len(event_ends) == 0:
        resp.start_time.CopyFrom(req.since)
        resp.end_time.FromDatetime(req.since.ToDatetime() + duration)
        return Response(status_code=200, content=resp.SerializeToString())

    i, j = 0, 0
    active_events = 0
    while j < len(event_ends):
        if i < len(event_starts) and event_starts[i] <= event_ends[j]:
            i += 1
            active_events += 1
            continue
        active_events -= 1
        start_time = event_ends[j]
        if event_ends[j] > req.since.ToDatetime() + datetime.timedelta(days=7):
            return Response(status_code=404)
        if active_events == 0 and i < len(event_starts) and start_time + duration <= event_starts[i]:
            resp.start_time.FromDatetime(event_ends[j])
            resp.end_time.FromDatetime(event_ends[j] + duration)
            return Response(status_code=200, content=resp.SerializeToString())
        j += 1
    if event_ends[-1] + duration <= req.since.ToDatetime() + datetime.timedelta(weeks=1):
        resp.start_time.FromDatetime(event_ends[-1])
        resp.end_time.FromDatetime(event_ends[-1] + duration)
        return Response(status_code=200, content=resp.SerializeToString())
    return Response(status_code=404)  # kek
