if __name__ == "__main__":
    import os, sys

    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取上一层目录的路径
    parent_dir = os.path.dirname(current_dir)
    # 将上一层目录添加到模块搜索路径中
    sys.path.append(parent_dir)

import json
from services.dict import trace_word
from oxfordstu.oxfordstu_schema import *
from fastapi import APIRouter, Depends
import sqlalchemy as sql
from database import cursor

# from typing import Annotated
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
# DB_URL = "sqlite+aiosqlite:///dictionary/oxfordstu.db"
# async def bind_engine():
#     engine = create_async_engine(DB_URL)
#     async with engine.connect() as cursor:
#         yield cursor
# CursorDep = Annotated[AsyncConnection, Depends(bind_engine)]


router = APIRouter()


@router.get("/retrieval")
async def retrieved_word(word: str):
    subq = (
        sql.select(Word.id)
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.definition_id == Definition.id)
        .where(
            Definition.inflection.regexp_match(rf"\b{word}\b")
            | (Word.word == word)
            | (Explanation.explain == word)
        )
        .group_by(Word.id)
    )
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
        .join(Explanation, Explanation.definition_id == Definition.id)
        .outerjoin(Example, Example.explanation_id == Explanation.id)
        .where(Word.id.in_(subq))
    )

    res = await cursor.execute(stmt)
    cache = []
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

    content = json.dumps(cache) if len(cache) else f"{word} not found"
    return {"status": 200 if len(cache) else 404, "content": content}


@router.get("/word/{word_id}")
async def retrieved_word_id(word_id: int):
    stmt = (
        sql.select(
            Word.id,
            Word.word,
            Asset.filename,
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
        .outerjoin(Asset, Asset.word_id == Word.id)
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.definition_id == Definition.id)
        .outerjoin(Example, Example.explanation_id == Explanation.id)
        .where(Word.id == word_id)
    )

    res = await cursor.execute(stmt)
    cache = []
    for entry in res.fetchall():
        w = trace_word(
            [
                {"word_id": entry[0], "word": entry[1], "asset": entry[2]},
                entry[3],
                {
                    "part_of_speech": entry[3],
                    "inflection": entry[4],
                    "phonetic_uk": entry[5],
                    "phonetic_us": entry[6],
                    "audio_uk": entry[7],
                    "audio_us": entry[8],
                },
                {
                    "part_of_speech": entry[3],
                    "explain": entry[-2],
                    "subscript": entry[-3],
                },
                {
                    "part_of_speech": entry[3],
                    "explain": entry[-2],
                    "example": entry[-1],
                },
            ],
            cache,
        )
        if not any((d for d in cache if d["word_id"] == entry[0])):
            cache += [w]

    content = json.dumps(cache[0]) if len(cache) else f"#{word_id} not found"
    # from fastapi.responses import JSONResponse
    # return JSONResponse(
    #     content={"status": 200 if len(cache) else 404, "content": content}
    # )
    return {"status": 200 if len(cache) else 404, "content": content}


async def a_run():
    async with cursor:
        cache = await retrieved_word_id(830)
    print(json.dumps(cache))


if __name__ == "__main__":
    import asyncio

    asyncio.run(a_run)
