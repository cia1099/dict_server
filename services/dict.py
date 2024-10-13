import os, sys, json

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上一层目录的路径
parent_dir = os.path.dirname(current_dir)
# 将上一层目录添加到模块搜索路径中
sys.path.append(parent_dir)
import sqlalchemy as sql
from oxfordstu.oxfordstu_schema import *

DB_URL = "sqlite:///dictionary/oxfordstu.db"


def bind_engine(db_url: str):
    def wrapper(func: callable):
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
            Word.word,
            Definition.part_of_speech,
            Explanation.id,
            Explanation.subscript,
            Explanation.explain,
            Example.example,
        )
        .join(Definition, Word.id == Definition.word_id)
        .join(Explanation, Explanation.definition_id == Definition.id)
        .join(Example, Example.explanation_id == Explanation.id)
        .where(
            Definition.inflection.regexp_match(rf"\b{word}\b")
            | (Word.word == word)
            | (Explanation.explain == word)
        )
    )
    # print("\x1b[32m%s\x1b[0m" % subq)
    onlye = (
        sql.select(Word.id, Word.word, Explanation.explain)
        .outerjoin(Explanation, Explanation.word_id == Word.id)
        .where(Explanation.word_id == 16)
    )
    res = cursor.execute(subq)
    # print(res.fetchall())
    for entry in res.fetchall():
        print(entry)


@bind_engine(DB_URL)
def retrieved_word(cursor: sql.engine.Connection, word: str) -> list[dict]:
    stmt = (
        sql.select(
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
        .join(Example, Example.explanation_id == Explanation.id)
        .where(
            Definition.inflection.regexp_match(rf"\b{word}\b")
            | (Word.word == word)
            | (Explanation.explain == word)
        )
    )

    res = cursor.execute(stmt)
    cache = []
    for entry in res.fetchall():
        w = trace_word(
            [
                entry[0],
                entry[1],
                {
                    "part_of_speech": entry[1].value,
                    "inflection": entry[2],
                    "phonetic_uk": entry[3],
                    "phonetic_us": entry[4],
                    "audio_uk": entry[5],
                    "audio_us": entry[6],
                },
                {
                    "part_of_speech": entry[1].value,
                    "explain": entry[-2],
                    "subscript": entry[8],
                },
                {
                    "part_of_speech": entry[1].value,
                    "explain": entry[-2],
                    "examples": entry[-1],
                },
            ],
            cache,
        )
        # print(json.dumps(w))
        if not any((d for d in cache if d["word"] == entry[0])):
            cache += [w]

    # print(json.dumps(cache))
    return cache


def trace_word(nodes: list, cache: list[dict]) -> dict:
    node = nodes.pop()
    if len(nodes) == 0:
        return next(
            filter(lambda d: d["word"] == node, cache),
            {"word": node, "definitions": []},
        )

    obj = trace_word(nodes, cache)
    definition_objs: list = obj["definitions"]
    if isinstance(node, PartOfSpeech):
        def_obj: dict = next(
            (d for d in definition_objs if d["part_of_speech"] == node.value), None
        )
        if not def_obj:
            definition_objs += [{"part_of_speech": node.value, "explanations": []}]
    else:
        part_of_speech = node.pop("part_of_speech")
        def_obj: dict = next(
            (d for d in definition_objs if d["part_of_speech"] == part_of_speech)
        )
        if len(node) == 5:  # node.get("inflection"):
            def_obj.update(**node)

        explanations = def_obj["explanations"]
        if node.get("explain"):
            if not any(
                (node.get("explain") == exp_obj["explain"] for exp_obj in explanations)
            ):
                explanations += [{**node, "examples": []}]

        # insert example
        if node.get("examples"):
            for explanation in explanations:
                if explanation["explain"] == node["explain"]:
                    explanation["examples"] += [node["examples"]]

        # obj.update({"definitions": definition_objs})
    return obj


if __name__ == "__main__":
    cache = retrieved_word("drunk")
    print(json.dumps(cache))
    # test_dictionary("abduct")
