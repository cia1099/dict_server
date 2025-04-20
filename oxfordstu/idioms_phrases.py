if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from typing import Iterable
import re, json
import sqlalchemy as sql

from macmillan_parse import create_macmillan_word
from cambridge_parse import create_cambridge_word
from thesaurus import speech_thesaurus, valid_speeches
from insert_db import insert_phrase, insert_explanation, insert_example
from oxfordstu_schema import Phrase
from model import Def
from log_config import log


def build_macmillan_phrase(
    cursor: sql.engine.Connection, word_id: int, phrases: Iterable[str]
):
    for phrase in phrases:
        macmillan_dict = create_macmillan_word(phrase, log=log)
        cambridge_dict = create_cambridge_word(phrase, log=log)
        thesaurus = speech_thesaurus(phrase, log=log)

        freq = thesaurus.pop("frequency", None)
        macmillan_dict.pop("phrases", [])
        # print(
        #     f"{phrase} has macmillan = {len(macmillan_dict)}, cambridge = {len(cambridge_dict)}, thesaurus = {len(thesaurus)}"
        # )
        for speech in macmillan_dict:
            if not speech in valid_speeches:
                if len(macmillan_dict) == len(thesaurus) == 1:
                    x_speech = next(iter(thesaurus))
                    part_of_speech = "noun" if "noun" in x_speech else x_speech
                elif len(macmillan_dict) == len(cambridge_dict) == 1:
                    part_of_speech = next(iter(cambridge_dict))
                else:
                    part_of_speech = "idiom"
            else:
                part_of_speech = speech
            try:
                phrase_idx = insert_phrase(
                    cursor,
                    word_id,
                    phrase=phrase,
                    part_of_speech=part_of_speech,
                    frequency=freq,
                )
            except ValueError as e:
                log.critical("%s" % e)
                continue
            for explain in [
                Def.from_dict(d) for d in macmillan_dict[speech].get("def", [])
            ]:
                if explain.explanation.startswith("to ") and part_of_speech != "verb":
                    part_of_speech = "verb"
                    cursor.execute(
                        sql.update(Phrase)
                        .where(Phrase.id == phrase_idx)
                        .values(part_of_speech="verb")
                    )
                explanation_idx = insert_explanation(
                    cursor,
                    word_id,
                    phrase_id=phrase_idx,
                    explain=explain.explanation,
                    subscript=explain.subscript,
                )
                # print("pass line 62 and explanation_id = %d" % explanation_idx)
            for example in explain.examples:
                insert_example(cursor, word_id, explanation_idx, example=example)


if __name__ == "__main__":
    # build_macmillan_phrase(("shit", "fuck", "hello word"))
    explain = "the leave a ship or boat because it is dangerous to stay"
    print(explain.startswith("to "))
