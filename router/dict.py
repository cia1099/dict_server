if __name__ == "__main__":
    import os, sys, json

    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取上一层目录的路径
    parent_dir = os.path.dirname(current_dir)
    # 将上一层目录添加到模块搜索路径中
    sys.path.append(parent_dir)

import re
from typing import Annotated
from services.dict import trace_word
from oxfordstu.oxfordstu_schema import *
from fastapi import APIRouter, Depends
import sqlalchemy as sql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection


DB_URL = "sqlite+aiosqlite:///dictionary/oxfordstu.db"


async def bind_engine():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as cursor:
        yield cursor


CursorDep = Annotated[AsyncConnection, Depends(bind_engine)]


router = APIRouter()


@router.get("/retrieval")
async def retrieved_word(word: str, cursor: CursorDep):
    stmt = (
        sql.select(
            Word.id,
            Word.word,
            Definition.part_of_speech,
            Definition.inflection,
            Definition.alphabet_uk,
            Definition.alphabet_us,
            Definition.audio_uk,
            Definition.audio_us,
            Definition.chinese,
            Explanation.subscript,
            Explanation.explain,
            Example.example,
        )
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.word_id == Definition.word_id)
        .outerjoin(Example, Example.explanation_id == Explanation.id)
        .where(
            Definition.inflection.regexp_match(rf"\b{word}\b")
            | (Word.word == word)
            | (Explanation.explain == word)
        )
    )
    print("\x1b[32m%s\x1b[0m" % stmt)

    engine = create_async_engine(DB_URL)
    res = await cursor.execute(stmt)
    cache = []
    # print(f"\x1b[43mresult has {len(res)}\x1b[0m")
    for entry in res.fetchall():
        w = trace_word(
            [
                {"word_id": entry[0], "word": entry[1]},
                entry[2],
                {
                    "part_of_speech": entry[2],
                    "inflection": entry[3],
                    "phonetic_uk": entry[4],
                    "phonetic_us": entry[5],
                    "audio_uk": entry[6],
                    "audio_us": entry[7],
                },
                {
                    "part_of_speech": entry[2],
                    "explain": entry[-2],
                    "subscript": entry[-3],
                },
                {
                    "part_of_speech": entry[2],
                    "explain": entry[-2],
                    "example": entry[-1],
                },
            ],
            cache,
        )
        if not any((d for d in cache if d["word_id"] == entry[0])):
            cache += [w]

    # print(json.dumps(cache))
    return cache


if __name__ == "__main__":
    import asyncio

    asyncio.run(retrieved_word("apple"))
