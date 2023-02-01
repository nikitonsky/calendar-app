import databases
import os
from starlette.applications import Starlette
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.routing import ROUTE_TABLE

from src import datamodel
import src.handles


def get_postgres_url():
    return os.environ['DATABASE_URL']


async def init_db():
    database_url = get_postgres_url()
    db = create_async_engine(database_url)
    async with db.begin() as conn:
        await conn.run_sync(datamodel.Base.metadata.drop_all)
        await conn.run_sync(datamodel.Base.metadata.create_all)
    app.state.db = sessionmaker(
        db, expire_on_commit=False, class_=AsyncSession)

app = Starlette(
    routes=ROUTE_TABLE,
    on_startup=[init_db]
)
