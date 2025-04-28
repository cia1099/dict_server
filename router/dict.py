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
from models.translate import TranslateIn
from router.img import convert_asset_url
from services.auth import guest_auth
from services.dict import trace_word, retrieval_expression, retrieval_queue
from services.character import Character
from oxfordstu.oxfordstu_schema import *
from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
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
async def retrieved_word(
    word: str,
    req: Request,
    lang: str | None = None,
    char: Character = Depends(guest_auth),
):
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
    stmt = retrieval_expression(
        subq, TranslateIn.column(lang) if char.role == Role.PREMIUM else None
    )

    res = await cursor.execute(stmt)
    cache = []
    for map in res.mappings().fetchall():
        w = trace_word(retrieval_queue(map), cache)
        if not any((d for d in cache if d["word_id"] == map.get("word_id"))):
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
        Translation.zh_CN.regexp_match(rf"\b{query}")
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
        .outerjoin(Translation, Word.id == Translation.word_id)
        .where(condition)
        .group_by(Word.id)
        .order_by(sql.func.char_length(Word.word).asc())
        .limit(max_length)
        .offset(page * max_length)
    )
    res = await cursor.execute(subq)
    # TODO: support locate in search arguments
    words = await retrieved_word_id(
        (row[0] for row in res.fetchall()), Translation.zh_CN
    )
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


@router.get("/phrases")
async def get_phrases_from_word_id(word_id: int, _=Depends(guest_auth)):
    phrases = await retrieved_phrases(word_id)
    return {"status": 200, "content": json.dumps(phrases)}


@router.get("/words/max_id")
async def get_word_max_id():
    stmt = sql.select(sql.func.count(Word.id))
    max_id = await cursor.execute(stmt)
    return {"status": 200, "content": "%d" % max_id.scalar()}


async def retrieved_word_id(
    word_ids: Iterable[int], locate: sql.Column[str] | None = None
) -> list[dict[str, Any]]:
    stmt = (
        sql.select(
            Word.word,
            Word.frequency,
            Asset.filename.label("asset"),
            Definition,
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
    if not locate is None:
        stmt = stmt.add_columns(locate.label("translate")).outerjoin(
            Translation, Translation.definition_id == Definition.id
        )

    res = await cursor.execute(stmt)
    cache = list[dict[str, Any]]()
    for map in res.mappings().fetchall():
        w = trace_word(retrieval_queue(map), cache)
        if not any((d for d in cache if d["word_id"] == map.get("word_id"))):
            cache += [w]

    return cache


async def retrieved_phrases(word_id: int):
    inf_cte = (
        sql.select(Phrase.id.label("phrase_id"), Definition.inflection)
        .outerjoin(
            Definition,
            (Definition.word_id == Phrase.word_id)
            & (
                (Definition.part_of_speech == Phrase.part_of_speech)
                | (Definition.part_of_speech == "noun")
            ),
        )
        .where(Phrase.word_id == word_id)
        .group_by(Phrase.id)
    ).cte()
    stmt = (
        sql.select(
            Phrase.id.label("word_id"),
            Phrase.phrase,
            Phrase.part_of_speech,
            inf_cte.c.inflection,
            Explanation.subscript,
            Explanation.explain,
            Example.example,
        )
        .join(Explanation, Explanation.phrase_id == Phrase.id)
        .outerjoin(inf_cte, inf_cte.c.phrase_id == Phrase.id)
        .outerjoin(Example, Example.explanation_id == Explanation.id)
        .where(Phrase.word_id == word_id)
    )
    res = await cursor.execute(stmt)
    cache = list[dict[str, Any]]()
    for map in res.mappings().fetchall():
        w = trace_word(retrieval_queue(map), cache)
        if not any((d for d in cache if d["word_id"] == map.get("word_id"))):
            cache += [w]
    # update word_id to phrase_id
    for c in cache:
        c["phrase_id"] = c.pop("word_id")
    return cache


async def a_run():
    async with cursor:
        # cache = await retrieved_word_id([810])
        cache = await retrieved_phrases(4753)  # drink=4753
        # print(len(cache))
        # res = await get_words(Request(), id=[830, 30])
        print(json.dumps(cache))


if __name__ == "__main__":
    import asyncio

    asyncio.run(a_run())
