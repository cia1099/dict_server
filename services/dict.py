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
                func(cursor, *args)

        return execute

    return wrapper


@bind_engine(DB_URL)
def test_dictionary(cursor: sql.engine.Connection, word: str):
    subq = (
        sql.select(
            Word.id,
            Word.word,
            Definition.id,
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
def retrieved_word(cursor: sql.engine.Connection, word: str) -> dict:
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
    cache = {}
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
                    "explanation": entry[-2],
                    "subscript": entry[8],
                },
                {
                    "part_of_speech": entry[1].value,
                    "explanation": entry[-2],
                    "examples": entry[-1],
                },
            ],
            cache,
        )
        cache.update({entry[0]: w})

    return cache


def trace_word(nodes: list, cache: dict) -> dict:
    node = nodes.pop()
    if len(nodes) == 0:
        return cache.get(node, {})
    obj = trace_word(nodes, cache)
    if isinstance(node, PartOfSpeech):
        speech_obj = obj.get(node.value, {"definition": []})
        obj.update({node.value: speech_obj})
    else:
        part_of_speech = node.pop("part_of_speech")
        speech_obj = obj.get(part_of_speech, {})
        if node.get("inflection"):
            speech_obj.update(**node)

        definition_objs = speech_obj.get("definition", [])
        if node.get("explanation"):
            if not any(
                (
                    node.get("explanation") == def_obj["explanation"]
                    for def_obj in definition_objs
                )
            ):
                definition_objs += [node]
        speech_obj.update({"definition": definition_objs})

        # insert example
        if node.get("examples"):
            for def_obj in definition_objs:
                exps = def_obj.get("examples", [])
                if def_obj["explanation"] == node["explanation"]:
                    exps += [node["examples"]]
                def_obj.update({"examples": exps})

        obj.update({part_of_speech: speech_obj})
    return obj


if __name__ == "__main__":
    # cache = retrieved_word("drunk")
    # print(json.dumps(cache))
    test_dictionary("apple")
