from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from fastapi import FastAPI
from __init__ import config


@asynccontextmanager
async def db_life(app: FastAPI):
    # await cursor
    async with cursor:
        async with remote_cursor:
            yield
            await remote_cursor.rollback()
        await cursor.rollback()
    await engine.dispose()
    await rengine.dispose()


if __name__ != "__main__":
    engine = create_async_engine(config.DB_URL)
    rengine = create_async_engine(config.REMOTE_DB)
    cursor: AsyncConnection = engine.connect()
    remote_cursor: AsyncConnection = rengine.connect()
else:
    local_db = "sqlite:///dictionary/oxfordstu.db"
    remote_db = config.REMOTE_DB
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
            for i, stmt in enumerate(tqdm(stmts)):
                rows = local_session.scalars(stmt).all()
                # local_session.expunge_all()
                print(f"\x1b[43mrows: {len(rows)}, type: {type(rows[0])}\x1b[0m")
                match i:
                    case 0:
                        remote_session.add_all(
                            (Word(id=w.id, word=w.word) for w in rows)
                        )
                    case 1:
                        remote_session.add_all(
                            (
                                Definition(
                                    id=w.id,
                                    word_id=w.word_id,
                                    part_of_speech=w.part_of_speech,
                                    inflection=w.inflection,
                                    phonetic_us=w.phonetic_us,
                                    phonetic_uk=w.phonetic_uk,
                                    audio_us=w.audio_us,
                                    audio_uk=w.audio_uk,
                                    chinese=w.chinese,
                                )
                                for w in rows
                            )
                        )
                    case 2:
                        remote_session.add_all(
                            (
                                Explanation(
                                    id=w.id,
                                    word_id=w.word_id,
                                    definition_id=w.definition_id,
                                    explain=w.explain,
                                    subscript=w.subscript,
                                    create_at=w.create_at,
                                )
                                for w in rows
                            )
                        )
                    case 3:
                        remote_session.add_all(
                            (
                                Example(
                                    id=w.id,
                                    word_id=w.word_id,
                                    explanation_id=w.explanation_id,
                                    example=w.example,
                                )
                                for w in rows
                            )
                        )
                    case _:
                        remote_session.add_all(
                            (
                                Asset(id=w.id, filename=w.filename, word_id=w.word_id)
                                for w in rows
                            )
                        )
                remote_session.commit()
            # remote_session.add_all(
            #     (Word(id=i, word="shit_%05d" % i) for i in range(1, 10000))
            # )
        # remote_session.commit()
