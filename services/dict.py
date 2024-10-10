import os, sys

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
def retrieved_word(cursor: sql.engine.Connection, word: str):
    subq = (
        sql.select(
            Word.id,
            Word.word,
            Definition.id,
            Explanation.id,
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
        # .group_by(Explanation.id)
    )
    defq = subq.group_by(Definition.id)
    expq = subq.group_by(Explanation.id)

    print("\x1b[32m%s\x1b[0m" % subq)
    onlye = (
        sql.select(Word.id, Word.word, Explanation.explain)
        .outerjoin(Explanation, Explanation.word_id == Word.id)
        .where(Explanation.word_id == 16)
    )
    res = cursor.execute(expq)
    # print(res.fetchall())
    for entry in res.fetchall():
        print(entry)


if __name__ == "__main__":
    retrieved_word("drunk")
