if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Generator
from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from logging import Logger
from oxfordstu import macmillan_URL


def create_macmillan_word(
    word: str, mdx_url: str | None = None, log: Logger | None = None
) -> dict:
    MDX_URL = mdx_url if mdx_url else macmillan_URL
    res = reader.query(MDX_URL, word)
    soup = BeautifulSoup(res, "lxml")
    dict_word = dict()
    for entry in soup.find_all("div", class_="homograph"):
        try:
            pos = entry.find("span", class_="part-of-speech-ctx").get_text()
        except:
            msg = f"{word} doesn't speech in Macmillan"
            log.debug(msg) if log else print(msg)
            continue
        tenses = ", ".join(
            [
                h5.get_text(strip=True)
                for h5 in entry.find("span", class_="head div").find_all(
                    "span", class_="inflection-entry"
                )
                if h5
            ]
        )
        pron = entry.find("span", class_="pron")
        phonetic = pron.get_text(strip=True) if pron else None
        hrefs = entry.find_all("a", href=re.compile(r"sound://*"))
        audio_file = "".join([h["href"].replace("sound", "macmillan") for h in hrefs])
        word_defs = []
        for body in entry.find_all("div", class_="sense"):
            definition = body.find("span", class_="definition")
            explain = definition.get_text().lstrip() if definition else None
            if explain is None:
                msg = f"{word} can't find explain(null) conflicted schema constraint db in macmillan"
                log.warning(msg) if log else print(msg)
                continue
            examples = [e.get_text() for e in body.find_all("p", class_="example") if e]
            try:
                subscript = (
                    body.find("span", class_="syntax-coding")
                    .get_text(strip=True)
                    .strip("[]")
                )
            except:
                syntax = entry.find("span", class_="syntax-coding")
                subscript = syntax.get_text(strip=True).strip("[]") if syntax else None

            word_def = {
                "explanation": explain,
                "subscript": subscript,
                "examples": examples,
            }
            word_defs.append(word_def)

        dict_word[pos] = {
            "def": word_defs,
            "phonetic": phonetic,
            "tenses": tenses if len(tenses) > 0 else None,
            "audio": audio_file if len(audio_file) > 0 else None,
        }
    if "phrasal verb" in dict_word:
        dict_word["verb"] = dict_word.pop("phrasal verb")
    # ====phrases
    if len(dict_word):
        phrases: Generator[str] = (
            p.get_text(strip=True)
            for phrase in soup.find_all(
                "div", re.compile(r"(phrases|phrasal-verbs)-container")
            )
            for p in phrase.find_all("a")
            if p
        )
        dict_word["phrases"] = [p for p in phrases if len(p.split(" ")) > 1]

    return dict_word


if __name__ == "__main__":
    MDX_URL = "/Users/otto/Downloads/dict/MacmillanEnEn.mdx"
    query = "drink down"
    word = create_macmillan_word(query)
    print(json.dumps(word))
    print(len(word))
