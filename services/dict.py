if __name__ == "__main__":
    import os, sys, json

    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取上一层目录的路径
    parent_dir = os.path.dirname(current_dir)
    # 将上一层目录添加到模块搜索路径中
    sys.path.append(parent_dir)
import sqlalchemy as sql
from typing import Any
from oxfordstu.oxfordstu_schema import *

DB_URL = "sqlite:///dictionary/oxfordstu.db"


def bind_engine(db_url: str):
    def wrapper(func: ...):
        engine = sql.create_engine(db_url)

        def execute(*args):
            with engine.connect() as cursor:
                return func(cursor, *args)

        return execute

    return wrapper


@bind_engine(DB_URL)
def test_dictionary(cursor: sql.engine.Connection, word: str):
    subq = (
        sql.select(
            Word.id,
        )
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.definition_id == Definition.id)
        .where(
            Definition.inflection.regexp_match(rf"\b{word}\b")
            | (Word.word == word)
            | (Explanation.explain == word)
        )
        .group_by(Word.id)
    )
    onlye = (
        sql.select(Word.id, Word.word, Explanation.explain)
        .outerjoin(Explanation, Explanation.word_id == Word.id)
        .where(Explanation.word_id.in_(subq))
    )
    print("\x1b[32m%s\x1b[0m" % onlye)
    res = cursor.execute(onlye)
    print(res.fetchall())
    # for row in res.fetchall():
    #     print(row)


@bind_engine(DB_URL)
def find_null_alphabets(cursor: sql.engine.Connection):
    stmt = (
        sql.select(
            Definition.id,
            Explanation.explain,
        )
        # .outerjoin(Definition, Definition.word_id == Word.id)
        .join(Explanation, Explanation.definition_id == Definition.id).where(
            (Definition.alphabet_uk == None) | (Definition.alphabet_us == None)
        )
    )
    res = cursor.execute(stmt)
    print(len(res.fetchall()))
    # for row in res:
    #     print(row)


# @bind_engine(DB_URL)
def get_indexes(cursor: sql.engine.Connection):
    stmt = sql.select(
        sql.select(sql.func.count(Word.id)).scalar_subquery(),
        sql.select(sql.func.count(Definition.id)).scalar_subquery(),
        sql.select(sql.func.count(Explanation.id)).scalar_subquery(),
        sql.select(sql.func.count(Example.id)).scalar_subquery(),
    )
    # stmt = sql.select(sql.func.count(Word.id))
    # print("\x1b[32m%s\x1b[0m" % stmt)
    res = cursor.execute(stmt)
    return res.one()


@bind_engine(DB_URL)
def retrieved_word_id(cursor: sql.engine.Connection, word_id: int):
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

    res = cursor.execute(stmt)
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

    return (
        cache[0]
        if len(cache) > 0
        else {"word_id": word_id, "word": "not found", "definitions": []}
    )


@bind_engine(DB_URL)
def retrieved_word(cursor: sql.engine.Connection, word: str) -> list[dict]:
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
    # print("\x1b[32m%s\x1b[0m" % stmt)

    res = cursor.execute(stmt)
    cache = []
    # print(f"\x1b[43mresult has {len(res.fetchall())}\x1b[0m")
    for row in res.fetchall():
        w = trace_word(retrieval_queue(row), cache)
        # print(json.dumps(w))
        if not any((d for d in cache if d["word_id"] == row[0])):
            cache += [w]

    # print(json.dumps(cache))
    return cache


@bind_engine(DB_URL)
def search_word(cursor: sql.engine.Connection, word: str, page: int = 0):
    contains_unicode = any(ord(char) > 127 for char in word)
    condition = (
        Definition.chinese.regexp_match(rf"\b{word}")
        if contains_unicode
        else (
            Definition.inflection.regexp_match(rf"\b{word}")
            | (Word.word == word)
            | (Explanation.explain == word)
        )
    )
    select = (
        (Word.id, Word.word, Definition.chinese)
        if contains_unicode
        else (Word.id, Word.word, Definition.part_of_speech)
    )
    max_length = 20
    subq = (
        sql.select(*select)
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.definition_id == Definition.id)
        .where(condition)
        .group_by(Definition.id)
        .order_by(sql.func.char_length(Word.word).asc())
        .limit(max_length)
        .offset(page * max_length)
    )
    # print(subq)
    res = cursor.execute(subq)
    cache = list[dict[str, Any]]()
    for row in res.fetchall():
        w = trace_search_result(
            [{"word_id": row[0], "word": row[1]}, row[2]],
            cache,
        )
        if not any((d for d in cache if d["word_id"] == row[0])):
            cache += [w]

    for c in cache:
        c.update({"description": ", ".join(c["description"])})
    return cache


def trace_word(nodes: list, cache: list[dict]) -> dict:
    node = nodes.pop()
    if len(nodes) == 0:
        return next(
            filter(lambda d: d["word_id"] == node["word_id"], cache),
            {**node, "definitions": []},
        )

    obj = trace_word(nodes, cache)
    definition_objs: list = obj["definitions"]
    if isinstance(node, str):
        def_oo = next((d for d in definition_objs if d["part_of_speech"] == node), None)
        if not def_oo:
            definition_objs += [{"part_of_speech": node, "explanations": []}]
    else:
        part_of_speech = node.pop("part_of_speech")
        def_obj: dict = next(
            (d for d in definition_objs if d["part_of_speech"] == part_of_speech)
        )
        if "inflection" in node.keys():
            if not all((k in def_obj for k in node.keys())):
                def_obj.update(**node)

        explanations = def_obj["explanations"]
        if node.get("explain"):
            if not any(
                (node.get("explain") == exp_obj["explain"] for exp_obj in explanations)
            ):
                explanations += [{**node, "examples": []}]

        # insert example
        if node.get("example"):
            for explanation in explanations:
                if explanation["explain"] == node["explain"]:
                    explanation["examples"] += [node["example"]]

        # obj.update({"definitions": definition_objs})
    return obj


def trace_search_result(nodes: list, cache: list[dict]) -> dict:
    node = nodes.pop()
    if len(nodes) == 0:
        return next(
            filter(lambda d: d["word_id"] == node["word_id"], cache),
            {**node, "description": []},
        )
    obj = trace_search_result(nodes, cache)
    obj["description"] += [node]
    return obj


def retrieval_expression(subq: sql.Select) -> sql.Select:
    return (
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


def retrieval_queue(row: sql.Row) -> list:
    return [
        {"word_id": row[0], "word": row[1]},
        row[2],
        {
            "part_of_speech": row[2],
            "inflection": row[3],
            "phonetic_uk": row[4],
            "phonetic_us": row[5],
            "audio_uk": row[6],
            "audio_us": row[7],
            "translate": row[-4],
        },
        {
            "part_of_speech": row[2],
            "explain": row[-2],
            "subscript": row[-3],
        },
        {
            "part_of_speech": row[2],
            "explain": row[-2],
            "example": row[-1],
        },
    ]


if __name__ == "__main__":
    # cache = retrieved_word("drunk")
    # cache = retrieved_word_id(830)
    # print(json.dumps(cache))
    # test_dictionary("drunk")
    # find_null_alphabets()
    # print(get_indexes())
    search_word("app", 1)
    # print(json.dumps(search_word("app"), indent=2))
    # print([ord(char) for char in text])
