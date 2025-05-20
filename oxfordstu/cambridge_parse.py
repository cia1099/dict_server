if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from pathlib import Path
from logging import Logger
from oxfordstu import cambridge_URL


def create_cambridge_word(
    word: str, mdx_url: str | None = None, log: Logger | None = None
) -> dict:
    MDX_URL = mdx_url if mdx_url else cambridge_URL
    res = reader.query(MDX_URL, word)
    soup = BeautifulSoup(res, "lxml")
    dict_word = dict()
    for entry in soup.find_all("div", class_="entry-body__el"):
        try:
            pos = entry.find("span", class_="pos").get_text(strip=True)
        except:
            pos = soup.find("span", class_="pos")
            pos = pos.get_text(strip=True) if pos else "abbreviation"
        cn_def = "、".join(
            [h5.get_text(strip=True) for h5 in entry.find_all("span", class_="cn_def")]
        )
        phonetics = [
            h5.get_text(strip=True) for h5 in entry.find_all("span", class_="pron")
        ]
        hrefs = entry.find_all("a", href=re.compile(r"sound://*"))
        audio_files = [h["href"].replace("sound", "cambridge") for h in hrefs]
        word_defs = []
        for def_block in entry.find_all("div", class_="def-block"):
            en_def = def_block.find("span", class_="en_def")
            explain = en_def.get_text().rstrip() if en_def else None
            if explain is None:
                msg = f"{word} can't find explain(null) conflicted schema constraint db in cambridge"
                log.warning(msg) if log else print(msg)
                continue
            gcs = def_block.find("span", class_="gcs")
            subscript = gcs.get_text(strip=True) if gcs else None
            examples = [
                e.get_text() for e in def_block.find_all("span", class_="en_example")
            ]
            word_def = {
                "explanation": explain,
                "subscript": convert_subscript(subscript),
                "examples": examples,
            }
            word_defs.append(word_def)

        dict_word[pos] = {
            "def": word_defs,
            "cn_def": cn_def,
            "phonetics": dict(zip(["uk", "us"], phonetics)),
            "audio": dict(zip(["uk", "us"], audio_files)),
        }
    if "phrasal verb" in dict_word:
        dict_word["verb"] = dict_word.pop("phrasal verb")

    return dict_word


def convert_subscript(subscript: str | None):
    match subscript:
        case "C":
            return "countable"
        case "U":
            return "uncountable"
        case "C or U":
            return "countable, uncountable"
        case "T":
            return "transitive"
        case "I":
            return "intransitive"
        case "T or I":
            return "transitive, intransitive"
        case "M":
            return "masculine"
        case "F":
            return "feminine"
        case "M or F":
            return "masculine, feminine"
        case "S":
            return "singular"
        case "P":
            return "plural"
        case _:
            return subscript


if __name__ == "__main__":
    MDX_URL = "/Users/otto/Downloads/dict/cambridge4.mdx"
    query = "mm"
    word = create_cambridge_word(query, mdx_url=MDX_URL)
    # print(word)
    print(json.dumps(word))
