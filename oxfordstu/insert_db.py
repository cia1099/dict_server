import sqlalchemy as sql
from oxfordstu_schema import *
from log_config import log


def insert_word(cursor: sql.engine.Connection, word: str, freq: float | None) -> int:
    stmt = sql.insert(Word).values(word=word, frequency=freq).returning(Word.id)
    try:
        word_idx = cursor.execute(stmt).scalar()
        if word_idx is None:
            raise ValueError(f"Duplicate word({word}) in database")
    except:
        raise ValueError(f"Cannot replicate word({word}) in database")
    return word_idx


def insert_definition(cursor: sql.engine.Connection, word_idx: int, **kwargs) -> int:
    zh_CN = kwargs.pop("zh_CN", None)
    stmt = (
        sql.insert(Definition)
        .values(word_id=word_idx, **kwargs)
        .returning(Definition.id)
    )
    try:
        definition_idx = cursor.execute(stmt).scalar()
        if definition_idx is None:
            raise ValueError(
                f"Fail insert definition({kwargs['part_of_speech']}) word(id={word_idx})"
            )
        else:
            insert_translation(cursor, word_idx, definition_idx, zh_CN)
    except:
        raise ValueError(
            f"Fail insert definition({kwargs['part_of_speech']}) word(id={word_idx})"
        )

    return definition_idx


def insert_explanation(
    cursor: sql.engine.Connection,
    word_idx: int,
    **kwargs,
) -> int:
    stmt = (
        sql.insert(Explanation)
        .values(word_id=word_idx, **kwargs)
        .returning(Explanation.id)
    )
    explanation_idx = cursor.execute(stmt).scalar()
    if explanation_idx is None:
        raise ValueError(
            f"Fail insert explanation({kwargs['explain']}) word(id={word_idx})"
        )
    return explanation_idx


def insert_asset(cursor: sql.engine.Connection, word_idx: int, filename: str):
    stmt = sql.insert(Asset).values(word_id=word_idx, filename=filename)
    try:
        cursor.execute(stmt)
    except:
        log.debug(f"Fail asset of word(id={word_idx}), filename={filename}")


def insert_example(
    cursor: sql.engine.Connection,
    word_idx: int,
    explanation_idx: int,
    **kwargs,
) -> int:
    stmt = (
        sql.insert(Example)
        .values(word_id=word_idx, explanation_id=explanation_idx, **kwargs)
        .returning(Example.id)
    )
    example_idx = cursor.execute(stmt).scalar()
    if example_idx is None:
        raise ValueError(
            f"Fail insert example(explanation_id={explanation_idx}) word(id={word_idx}), example={kwargs['example']}"
        )
    return example_idx


def insert_translation(
    cursor: sql.engine.Connection,
    word_idx: int,
    definition_idx: int,
    zh_CN: str | None = None,
):
    if zh_CN is None:
        # log.warning(f"word({word_idx}) don't have zh_CN in cambridge")
        return
    stmt = sql.insert(Translation).values(
        word_id=word_idx, definition_id=definition_idx, zh_CN=zh_CN
    )
    cursor.execute(stmt)


def insert_phrase(cursor: sql.engine.Connection, word_idx: int, **kargs):
    stmt = sql.insert(Phrase).values(word_id=word_idx, **kargs).returning(Phrase.id)

    try:
        phrase_idx = cursor.execute(stmt).scalar()
        if phrase_idx is None:
            raise ValueError(f"{kargs.get("phrase")} Failed insert to db")
    except:
        raise ValueError(f"{kargs.get("phrase")}(word_id={word_idx}) duplicate in db")
    return phrase_idx


# def remove_word(cursor: sql.engine.Connection, word_idx: int) -> int:
#     stmt = sql.delete(Word).where(Word.id == word_idx)
#     try:
#         cursor.execute(stmt)
#         word_idx -= 1
#     except:
#         log.debug(f"Cannot delete word({word}, id={word_idx}) in database")
#     return word_idx
