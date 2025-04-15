if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from logging import Logger

from oxfordstu import merriam_URL


valid_speeches = [
    "noun",
    "verb",
    "adjective",
    "adverb",
]


def speech_thesaurus(
    word: str, mdx_url: str | None = None, log: Logger | None = None
) -> dict:
    MDX_URL = mdx_url if mdx_url else merriam_URL
    res = reader.query(MDX_URL, word)
    soup = BeautifulSoup(res, "lxml")
    dict_word = dict()
    for entry in soup.find_all("span", attrs={"data-source": "entry-dictionary"}):
        header = entry.find("div", class_="entry-header")
        part_of_speech = header.find("span", class_="fl").get_text()
        # print("How many syn-box %d" % len(soup.find_all("div", class_="syn-box-list")))
        thesaurus_dict = {"Synonyms": None, "Antonyms": None}
        dict_word[part_of_speech] = thesaurus_dict
    for i, syn_box in enumerate(soup.find_all("div", class_="syn-box-list")):
        part_of_speech = list(dict_word.keys())[i // 5]
        thesaurus_dict = dict_word[part_of_speech]
        h6 = syn_box.find("h6")
        if h6 and h6.get_text() in thesaurus_dict.keys():
            # 全形顿号
            # text = "、".join([h.get_text() for h in syn_box.find_all("a") if h])
            text = ", ".join([h.get_text() for h in syn_box.find_all("a") if h])
            thesaurus_dict.update({h6.get_text(): text if len(text) > 0 else None})

    if "phrasal verb" in dict_word:
        dict_word["verb"] = dict_word.pop("phrasal verb")

    if len(dict_word):
        popular = soup.find("span", class_="popularity-block hidden")
        text = popular.get_text() if popular else ""
        dict_word["frequency"] = freq_appear(text)

    return dict_word


def freq_appear(text: str) -> float | None:
    matches = re.search(r"(Top|Bottom)\s+(\d+(?:\.\d+)?)%", text)
    if not matches:
        return matches
    direct, digit = matches.group(1), float(matches.group(2))
    if direct == "Top":
        return 1 - digit * 1e-2
    else:
        return digit * 1e-2


if __name__ == "__main__":
    MDX_URL = "/Users/otto/Downloads/dict/Merriam-Webster Dictionary Online.mdx"
    query = "drink down"
    word = speech_thesaurus(query)
    print(json.dumps(word))
