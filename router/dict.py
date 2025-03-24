if __name__ == "__main__":
    import os, sys

    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取上一层目录的路径
    parent_dir = os.path.dirname(current_dir)
    # 将上一层目录添加到模块搜索路径中
    sys.path.append(parent_dir)

import json
from typing import Iterable, List, Any
from models.role import Role
from router.img import convert_asset_url
from services.auth import guest_auth
from services.dict import trace_word, retrieval_expression, retrieval_queue
from oxfordstu.oxfordstu_schema import *
from fastapi import APIRouter, Depends, Query, Request
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
async def retrieved_word(word: str, req: Request, _=Depends(guest_auth)):
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
    stmt = retrieval_expression(subq)

    res = await cursor.execute(stmt)
    cache = []
    for entry in res.fetchall():
        w = trace_word(retrieval_queue(entry), cache)
        if not any((d for d in cache if d["word_id"] == entry[0])):
            cache += [w]
    cache = [convert_asset_url(w, req) for w in cache]
    content = json.dumps(cache) if len(cache) else f"{word} not found"
    return {"status": 200 if len(cache) else 404, "content": content}


@router.get("/search")
async def search_word(
    req: Request, word: str, page: int = 0, max_length: int = 20, _=Depends(guest_auth)
):
    query = word.strip()
    if len(query) == 0:
        return {"status": 200, "content": "[]"}
    contains_unicode = any(ord(char) > 127 for char in query)
    condition = (
        Definition.chinese.regexp_match(rf"\b{query}")
        if contains_unicode
        else (
            Definition.inflection.regexp_match(rf"\b{query}")
            | (Word.word == query)
            | (Explanation.explain == query)
        )
    )
    subq = (
        sql.select(Word.id)
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.definition_id == Definition.id)
        .where(condition)
        .group_by(Word.id)
        .order_by(sql.func.char_length(Word.word).asc())
        .limit(max_length)
        .offset(page * max_length)
    )
    res = await cursor.execute(subq)
    words = await retrieved_word_id((row[0] for row in res.fetchall()))
    words = [convert_asset_url(w, req) for w in words]
    return {"status": 200, "content": json.dumps(words)}


@router.get("/words")
async def get_words(
    req: Request, id: List[int] = Query(default=[]), _=Depends(guest_auth)
):
    words = await retrieved_word_id(id)
    words = [convert_asset_url(w, req) for w in words]
    content = (
        json.dumps(words)
        if len(words) == len(id)
        else f"word@{[d for d in id if d not in (w['word_id'] for w in words)]} not found"
    )
    return {"status": 200 if len(words) == len(id) else 404, "content": content}


@router.get("/word_id/{word_id}")
async def get_word_by_id(word_id: int, req: Request, _=Depends(guest_auth)):
    words = await retrieved_word_id([word_id])
    words = [convert_asset_url(w, req) for w in words]
    content = json.dumps(words[0]) if len(words) else f"word#{word_id} not found"
    return {"status": 200 if len(words) else 404, "content": content}


@router.get("/words/max_id")
async def get_word_max_id():
    stmt = sql.select(sql.func.count(Word.id))
    max_id = await cursor.execute(stmt)
    return {"status": 200, "content": "%d" % max_id.scalar()}


async def retrieved_word_id(word_ids: Iterable[int]) -> list[dict[str, Any]]:
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
        .where(Word.id.in_(word_ids))
        .order_by(sql.func.char_length(Word.word).asc())
    )

    res = await cursor.execute(stmt)
    cache = list[dict[str, Any]]()
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
                    "translate": entry[-4],
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

    return cache


async def a_run():
    async with cursor:
        # cache = await retrieved_word_id([830, 30])
        # print(len(cache))
        res = await get_words(Request(), id=[830, 30])
    # print(json.dumps(cache))


if __name__ == "__main__":
    import asyncio

    asyncio.run(a_run())
