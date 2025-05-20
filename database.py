from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import MetaData
from fastapi import FastAPI
from config import config


@asynccontextmanager
async def db_life(app: FastAPI):
    async with remote_engine.begin() as conn:
        await conn.run_sync(metadata.reflect)
    yield
    await engine.dispose()
    await remote_engine.dispose()


if __name__ != "__main__":
    engine = create_async_engine(config.DB_URL, poolclass=NullPool)
    # remote_engine = create_async_engine(
    #     "sqlite+aiosqlite:///test.db", poolclass=NullPool
    # )
    remote_engine = create_async_engine(
        config.REMOTE_DB,
        pool_size=10,
        max_overflow=20,
        pool_timeout=15,
        pool_recycle=1800,
    )
    metadata = MetaData()

else:
    local_db = "sqlite:///dictionary/oxfordstu.db"
    remote_db = config.REMOTE_DB
    import sqlalchemy as sql
    from sqlalchemy.orm import Session
    from oxfordstu.oxfordstu_schema import *
    from tqdm import tqdm

    local_engine = sql.create_engine(local_db)
    rengine = sql.create_engine(remote_db)
    Base.metadata.drop_all(rengine)
    Base.metadata.create_all(rengine)
    with Session(bind=rengine) as remote_session:
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
