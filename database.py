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


if __name__ == "__main__":
    local_db = "sqlite:///dictionary/oxfordstu.db"
    remote_db = ""
    import sqlalchemy as sql
    from sqlalchemy.orm import Session
    from oxfordstu.oxfordstu_schema import *
    from tqdm import tqdm

    local_engine = sql.create_engine(local_db)
    remote_engine = sql.create_engine(remote_db)
    Base.metadata.drop_all(remote_engine)
    Base.metadata.create_all(remote_engine)
    with Session(bind=remote_engine) as remote_session:
        with Session(bind=local_engine) as local_session:
            stmts = [
                sql.select(Word),
                sql.select(Definition),
                sql.select(Explanation),
                sql.select(Example),
                sql.select(Asset),
            ]
            for stmt in tqdm(stmts):
                rows = local_session.scalars(stmt).all()
                remote_session.add_all(rows)
                remote_session.commit()
