import os, re

if __name__ == "__main__":
    import sys

    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取上一层目录的路径
    parent_dir = os.path.dirname(current_dir)
    # 将上一层目录添加到模块搜索路径中
    sys.path.append(parent_dir)
from pathlib import Path
from datetime import datetime
from mdict_utils import reader
import sqlalchemy as sql
from bs4 import BeautifulSoup
from oxfordstu_schema import *
from log_config import log
from parse_oxfordstu import (
    get_asset_oxfordstu,
    get_cambridge_chinese,
    get_macmillan_tense,
    create_oxfordstu_word,
)
from model import part_word_from_dict
from services.dict import get_indexes


def insert_word(cursor: sql.engine.Connection, word_idx: int, word: str) -> int:
    stmt = sql.insert(Word).values(word=word).returning(Word.id)
    try:
        word_idx = cursor.execute(stmt).scalar()
        # word_idx += 1
    except:
        raise ValueError(f"Cannot replicate word({word}, id={word_idx}) in database")
    return word_idx


def remove_word(cursor: sql.engine.Connection, word_idx: int) -> int:
    stmt = sql.delete(Word).where(Word.id == word_idx)
    try:
        cursor.execute(stmt)
        word_idx -= 1
    except:
        log.debug(f"Cannot delete word({word}, id={word_idx}) in database")
    return word_idx


def insert_definition(
    cursor: sql.engine.Connection, word_idx: int, definition_idx: int, **kwargs
) -> int:
    stmt = (
        sql.insert(Definition)
        .values(word_id=word_idx, **kwargs)
        .returning(Definition.id)
    )
    try:
        definition_idx = cursor.execute(stmt).scalar()
        # definition_idx += 1
    except:
        log.debug(
            f"Fail insert definition(id={definition_idx}) word(id={word_idx}), speech={kwargs['part_of_speech']}"
        )
    return definition_idx


def insert_explanation(
    cursor: sql.engine.Connection,
    word_idx: int,
    definition_idx: int,
    explanation_idx: int,
    **kwargs,
) -> int:
    stmt = (
        sql.insert(Explanation)
        .values(word_id=word_idx, definition_id=definition_idx, **kwargs)
        .returning(Explanation.id)
    )
    try:
        explanation_idx = cursor.execute(stmt).scalar()
        # explanation_idx += 1
    except:
        log.debug(
            f"Fail insert explanation(id={explanation_idx}) word(id={word_idx}), explain={kwargs['explain']}"
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
    example_idx: int,
    **kwargs,
) -> int:
    stmt = (
        sql.insert(Example)
        .values(word_id=word_idx, explanation_id=explanation_idx, **kwargs)
        .returning(Example.id)
    )
    try:
        example_idx = cursor.execute(stmt).scalar()
        # example_idx += 1
    except:
        log.debug(
            f"Fail insert example(id={example_idx}) word(id={word_idx}), example={kwargs['example']}"
        )
    return example_idx


def build_oxfordstu_word(
    word: str,
    soup: BeautifulSoup,
    word_idx: int,
    definition_idx: int,
    explanation_idx: int,
    example_idx: int,
    cursor: sql.engine.Connection,
) -> tuple[int]:
    from log_config import log

    try:
        cn_dict, alphabets = get_cambridge_chinese(word)
    except:
        raise ValueError(f'"{word}" failed getting from cambridge')
    try:
        tense, mac_prons = get_macmillan_tense(word)
    except:
        raise ValueError(f'"{word}" failed getting from macmillan')
    for k, v in mac_prons.items():
        if k in alphabets:
            continue
        alphabets[k] = v
    try:
        word_dict = create_oxfordstu_word(soup, word, log)
    except:
        raise ValueError(f'"{word}" failed getting from oxfordstu')

    valid_derived_speech = [
        PartOfSpeech.verb.value,
        PartOfSpeech.noun.value,
        PartOfSpeech.adjective.value,
        PartOfSpeech.adverb.value,
    ]
    if any((speech in alphabets.keys() for speech in word_dict.keys())):
        if len(word.split(" ")) > 1:
            raise KeyError(f"{word} is not a vocabulary")
        word_idx = insert_word(cursor, word_idx=word_idx, word=word)
    else:
        raise KeyError(
            f'"{word}" {[k for k in word_dict.keys()]} mismatched alphabets: {[k for k in alphabets.keys()]}'
        )
    for part_of_speech in word_dict:
        if not part_of_speech in alphabets.keys():
            log.warning(
                f'"{word}"({part_of_speech}) does\'t have alphabets:{[k for k in alphabets.keys()]}'
            )
            if not part_of_speech in valid_derived_speech:
                continue
        alphabet = alphabets.get(part_of_speech, [])
        chinese = cn_dict.get(part_of_speech, None)
        inflection = tense.get(part_of_speech, None)
        part_word = part_word_from_dict(word_dict[part_of_speech])
        definition_idx = insert_definition(
            cursor,
            word_idx,
            definition_idx,
            part_of_speech=part_of_speech,
            inflection=inflection,
            alphabet_uk=alphabet[0] if len(alphabet) > 0 else None,
            alphabet_us=alphabet[-1] if len(alphabet) > 0 else None,
            audio_uk=part_word.audio[0] if len(part_word.audio) > 0 else None,
            audio_us=part_word.audio[-1] if len(part_word.audio) > 0 else None,
            chinese=chinese,
        )
        for explain in part_word.part_word_def:
            explanation_idx = insert_explanation(
                cursor,
                word_idx,
                definition_idx,
                explanation_idx,
                explain=explain.explanation,
                subscript=explain.subscript,
            )
            for example in explain.examples:
                example_idx = insert_example(
                    cursor, word_idx, explanation_idx, example_idx, example=example
                )

    asset = get_asset_oxfordstu(soup)
    if asset is not None:
        insert_asset(cursor, word_idx=word_idx, filename=asset)

    return word_idx, definition_idx, explanation_idx, example_idx


def modified_null_alphabet(cursor: sql.engine.Connection):
    stmt = (
        sql.select(
            Explanation.explain,
            Definition.part_of_speech,
            Definition.id,
            Definition.alphabet_uk,
            Definition.alphabet_us,
            Definition.inflection,
        )
        .join(Explanation, Explanation.definition_id == Definition.id)
        .where((Definition.alphabet_uk == None) | (Definition.alphabet_us == None))
    )
    res = cursor.execute(stmt)
    log.debug("Start to modified loss alphabets ...")
    for entry in reader.tqdm(res.fetchall()):
        word = entry[0]
        try:
            cn_dict, alphabets = get_cambridge_chinese(word)
        except:
            log.warning(f'"{word}" failed getting from cambridge')
            cn_dict, alphabets = {}, {}
        try:
            tense, mac_prons = get_macmillan_tense(word)
        except:
            log.warning(f'"{word}" failed getting from macmillan')
            tense, mac_prons = {}, {}
        for k, v in mac_prons.items():
            if k in alphabets:
                continue
            alphabets[k] = v

        part_of_speech = entry[1]
        alphabet = alphabets.get(part_of_speech)
        if alphabet:
            content = {
                "alphabet_us": alphabet[-1],
                "alphabet_uk": alphabet[0],
                "inflection": tense.get(part_of_speech),
                "chinese": cn_dict.get(part_of_speech),
            }
            update_query = (
                sql.update(Definition)
                .where(Definition.id == entry[2])
                .values(**content)
            )
            cursor.execute(update_query)


if __name__ == "__main__":
    os.system("rm oxfordstu.db*")
    DB_URL = "sqlite:///oxfordstu.db"
    MDX_URL = "/Users/otto/Downloads/dict/oxfordstu.mdx"

    engine = create_engine(DB_URL, echo=False)
    Base.metadata.create_all(engine)
    test_words = ["abduct", "abdomen"]  # ["apple", "record", "watch", "drunk"]
    tic = datetime.now()
    log.info(f"{tic.replace(microsecond=0)} started creating database ...")
    with engine.connect() as cursor:
        word_idx, definition_idx, explanation_idx, example_idx = get_indexes(cursor)
        # for word in test_words:
        #     html = reader.query(MDX_URL, word)
        for k, v in reader.tqdm(reader.MDX(MDX_URL).items(), total=28895):
            word = str(k, "utf-8")
            html = str(v, "utf-8")
            try:
                word_idx, definition_idx, explanation_idx, example_idx = (
                    build_oxfordstu_word(
                        word,
                        BeautifulSoup(html, "lxml"),
                        word_idx,
                        definition_idx,
                        explanation_idx,
                        example_idx,
                        cursor,
                    )
                )
            except Exception as e:
                if isinstance(e, ValueError):
                    log.critical(f"{e}")
                log.debug("%s" % e)

        cursor.commit()
        modified_null_alphabet(cursor)
        cursor.commit()
        toc = datetime.now()
        log.info(f"{toc.replace(microsecond=0)} finished progress ...")
        elapsed = toc.timestamp() - tic.timestamp()
        log.info(
            f"Elapsed time = {elapsed//3600:02.0f}:{(elapsed%3600)//60:02.0f}:{(elapsed%3600)%60:02.0f}"
        )
