from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from pathlib import Path
from logging import Logger


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


def create_cambridge_word(mdx_url: str, word: str, log: Logger | None = None) -> dict:
    res = reader.query(mdx_url, word)
    soup = BeautifulSoup(res, "lxml")
    dict_word = dict()
    for entry in soup.find_all("div", class_="entry-body__el"):
        try:
            pos = entry.find("span", class_="pos").get_text(strip=True)
        except:
            pos = soup.find("span", class_="pos")
            if pos is not None:
                pos = pos.get_text(strip=True)
        cn_def = "、".join(
            [
                h5.get_text(strip=True)
                for h5 in entry.find_all("span", class_="cn_def")
                if h5
            ]
        )
        phonetics = [
            h5.get_text(strip=True)
            for h5 in entry.find_all("span", class_="pron")
            if h5
        ]
        word_defs = []
        for def_block in entry.find_all("div", class_="def-block"):
            en_def = def_block.find("span", class_="en_def")
            explain = en_def.get_text(strip=True) if en_def else None
            gcs = def_block.find("span", class_="gcs")
            subscript = gcs.get_text(strip=True) if gcs else None
            examples = [
                e.get_text()
                for e in def_block.find_all("span", class_="en_example")
                if e
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
        }

    return dict_word


if __name__ == "__main__":
    MDX_URL = "/Users/otto/Downloads/dict/cambridge4.mdx"
    query = "record"
    word = create_cambridge_word(MDX_URL, query)
    # print(word)
    print(json.dumps(word))
