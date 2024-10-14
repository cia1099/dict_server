from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from fastapi import FastAPI

DB_URL = "sqlite+aiosqlite:///dictionary/oxfordstu.db"
engine = create_async_engine(DB_URL)
cursor: AsyncConnection = engine.connect()


@asynccontextmanager
async def db_life(app: FastAPI):
    # await cursor
    async with cursor:
        yield
        await cursor.rollback()
    await engine.dispose()
