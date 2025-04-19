import json
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

from parse_oxfordstu import (
    get_asset_oxfordstu,
    create_oxfordstu_word,
)
from macmillan_parse import create_macmillan_word
from cambridge_parse import create_cambridge_word
from thesaurus import speech_thesaurus, valid_speeches
from idioms_phrases import build_macmillan_phrase
from model import PartWord, Thesaurus, Def
from services.dict import get_indexes
from insert_db import *
from oxfordstu import oxfordstu_URL


def build_oxfordstu_word(
    word: str,
    soup: BeautifulSoup,
    cursor: sql.engine.Connection,
):
    try:
        cambridge_dict = create_cambridge_word(word, log=log)
    except:
        raise ValueError(f'"{word}" failed getting from cambridge')
    try:
        macmillan_dict = create_macmillan_word(word, log=log)
    except:
        raise ValueError(f'"{word}" failed getting from macmillan')
    try:
        thesaurus_dict = speech_thesaurus(word, log=log)
    except:
        raise ValueError(f'"{word}" failed getting from thesaurus')
    try:
        word_dict = create_oxfordstu_word(soup, word, log)
    except:
        raise ValueError(f'"{word}" failed getting from oxfordstu')

    speeches = cambridge_dict.keys() | {s for s in macmillan_dict if s != "phrases"}
    if not any((speech in speeches for speech in word_dict)):
        raise KeyError(
            f"{word} {[k for k in word_dict]} mismatch speeches {[k for k in speeches]}"
        )

    word_idx = insert_word(cursor, word=word, freq=thesaurus_dict.get("frequency"))

    for part_of_speech in word_dict:
        if not part_of_speech in speeches:
            log.warning(f'"{word}"({part_of_speech}) extra speech in oxfordstu')
            if not part_of_speech in valid_speeches:
                log.info(f"{word}({part_of_speech}) is unnecessary")
                continue
        alphabet = {
            "uk": cambridge_dict.get(part_of_speech, {}).get("phonetics", {}).get("uk"),
            "us": macmillan_dict.get(part_of_speech, {}).get("phonetic"),
        }
        inflection = macmillan_dict.get(part_of_speech, {}).get("tenses")
        thesaurus = Thesaurus.from_dict(thesaurus_dict.get(part_of_speech, {}))

        part_word = PartWord.from_dict(word_dict.get(part_of_speech))
        definition_idx = insert_definition(
            cursor,
            word_idx,
            part_of_speech=part_of_speech,
            inflection=inflection,
            phonetic_uk=alphabet["uk"],
            phonetic_us=alphabet["us"],
            audio_uk=part_word.audio.uk,
            audio_us=part_word.audio.us,
            synonyms=thesaurus.synonyms,
            antonyms=thesaurus.antonyms,
            zh_CN=cambridge_dict.get(part_of_speech, {}).get("cn_def"),
        )

        if len(part_word.part_word_def) == 0:
            part_word.part_word_def = [
                Def.from_dict(d)
                for d in (
                    cambridge_dict.get(part_of_speech)
                    or macmillan_dict.get(part_of_speech, {})
                ).get("def", [])
            ]
        for explain in part_word.part_word_def:
            explanation_idx = insert_explanation(
                cursor,
                word_idx,
                definition_id=definition_idx,
                explain=explain.explanation,
                subscript=explain.subscript,
            )
            for example in explain.examples:
                insert_example(cursor, word_idx, explanation_idx, example=example)

    asset = get_asset_oxfordstu(soup)
    if asset is not None:
        insert_asset(cursor, word_idx=word_idx, filename=asset)

    build_macmillan_phrase(cursor, word_idx, macmillan_dict.get("phrases", []))

    return word_idx


def modified_null_alphabet(cursor: sql.engine.Connection):
    stmt = (
        sql.select(
            Explanation.explain,
            Definition.part_of_speech,
            Definition.id,
            Definition.word_id,
            Explanation.id,
            Definition.audio_uk,
            Definition.audio_us,
            Example.id,
        )
        .join(Explanation, Explanation.definition_id == Definition.id)
        .outerjoin(Example, Explanation.id == Example.explanation_id)
        .where((Definition.phonetic_uk == None) & (Definition.phonetic_us == None))
        .group_by(Definition.id)
    )
    res = cursor.execute(stmt)
    log.debug("Start to modified loss alphabets ...")
    for entry in reader.tqdm(res.fetchall()):
        word = entry[0]
        part_of_speech = entry[1]
        if part_of_speech not in valid_speeches:
            continue
        log.debug(f"{word} is going to modify")
        cambridge_dict = create_cambridge_word(word, log=log)
        macmillan_dict = create_macmillan_word(word, log=log)
        thesaurus_dict = speech_thesaurus(word, log=log)

        phonetics = cambridge_dict.get(part_of_speech, {}).get("phonetics", {})
        alphabet = {
            "uk": phonetics.get("uk"),
            "us": macmillan_dict.get(part_of_speech, {}).get("phonetic")
            or phonetics.get("us"),
        }
        thesaurus = Thesaurus.from_dict(thesaurus_dict.get(part_of_speech, {}))
        content = {
            "phonetic_uk": alphabet["uk"],
            "phonetic_us": alphabet["us"],
            "inflection": macmillan_dict.get(part_of_speech, {}).get("tenses"),
            "synonyms": thesaurus.synonyms,
            "antonyms": thesaurus.antonyms,
        }
        update_query = (
            sql.update(Definition).where(Definition.id == entry[2]).values(**content)
        )
        cursor.execute(update_query)
        zh_CN = cambridge_dict.get(part_of_speech, {}).get("cn_def")
        try:
            insert_translation(cursor, entry[3], entry[2], zh_CN)
        except Exception as e:
            pass

        if len(word.split(" ")) == 1 and len(macmillan_dict) > 1:
            try:
                word_idx = insert_word(
                    cursor, word=word, freq=thesaurus_dict.get("frequency")
                )
                definition_idx = insert_definition(
                    cursor,
                    word_idx,
                    part_of_speech=part_of_speech,
                    inflection=macmillan_dict.get(part_of_speech, {}).get("tenses"),
                    phonetic_uk=alphabet["uk"],
                    phonetic_us=alphabet["us"],
                    audio_uk=entry[-3],
                    audio_us=entry[-2],
                    synonyms=thesaurus.synonyms,
                    antonyms=thesaurus.antonyms,
                    zh_CN=zh_CN,
                )
                defs = [
                    Def.from_dict(d)
                    for d in macmillan_dict.get(part_of_speech, {}).get("def", [])
                ]
                for explain in defs:
                    explanation_idx = insert_explanation(
                        cursor,
                        word_idx,
                        definition_id=definition_idx,
                        explain=explain.explanation,
                        subscript=explain.subscript,
                    )
                    for example in explain.examples:
                        insert_example(
                            cursor, word_idx, explanation_idx, example=example
                        )
            except Exception as e:
                log.critical("%s" % e)
        if entry[-1] is None:
            examples = [
                e
                for defs in [
                    Def.from_dict(d)
                    for d in cambridge_dict.get(part_of_speech, {}).get("def", [])
                ]
                for e in defs.examples
            ]
            word_idx, explanation_idx = entry[3], entry[4]
            for example in examples:
                insert_example(cursor, word_idx, explanation_idx, example=example)


if __name__ == "__main__":
    os.system("rm oxfordstu.db*")
    DB_URL = "sqlite:///oxfordstu.db"
    MDX_URL = oxfordstu_URL
    # cmd rm dict_oxfordstu.log && python3 oxfordstu/create_oxfordstu_db.py

    engine = create_engine(DB_URL, echo=False)
    Base.metadata.create_all(engine)
    test_words = [
        "drink",
        # "abduct",
        "abet",
        "off the record",
    ]  # ["apple", "record", "watch", "drunk"]
    tic = datetime.now()
    log.info(f"{tic.replace(microsecond=0)} started creating database ...")
    with engine.connect() as cursor:
        word_idx, definition_idx, explanation_idx, example_idx = get_indexes(cursor)
        for word in reader.tqdm(test_words):
            html = reader.query(MDX_URL, word)
            # for k, v in reader.tqdm(reader.MDX(MDX_URL).items(), total=28895):
            #     word = str(k, "utf-8")
            #     html = str(v, "utf-8")
            if len(word.split(" ")) > 1:
                log.info(f"'{word}' is not a vocabulary")
                continue
            try:
                word_idx = build_oxfordstu_word(
                    word,
                    BeautifulSoup(html, "lxml"),
                    cursor,
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
