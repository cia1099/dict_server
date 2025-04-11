from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from logging import Logger


def create_macmillan_word(mdx_url: str, word: str, log: Logger | None = None) -> dict:
    res = reader.query(mdx_url, word)
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
        word_defs = []
        for body in entry.find_all("div", class_="sense"):
            definition = body.find("span", class_="definition")
            explain = definition.get_text().lstrip() if definition else None
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
        }

    return dict_word


if __name__ == "__main__":
    MDX_URL = "/Users/otto/Downloads/dict/MacmillanEnEn.mdx"
    query = "drink"
    word = create_macmillan_word(MDX_URL, query)
    print(json.dumps(word))
