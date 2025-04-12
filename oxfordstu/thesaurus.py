from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from logging import Logger


def speech_thesaurus(mdx_url: str, word: str, log: Logger | None = None) -> dict:
    res = reader.query(mdx_url, word)
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
            text = "、".join([h.get_text() for h in syn_box.find_all("a") if h])
            # text = ", ".join([h.get_text() for h in syn_box.find_all("a") if h])
            thesaurus_dict.update({h6.get_text(): text if len(text) > 0 else None})

    popular = soup.find("span", class_="popularity-block hidden")
    text = popular.get_text() if popular else ""
    match = re.search(r"(\d+(?:\.\d+)?)%", text)
    dict_word["frequency"] = 1 - float(match.group(1)) * 1e-2 if match else None

    return dict_word


if __name__ == "__main__":
    MDX_URL = "/Users/otto/Downloads/dict/Merriam-Webster Dictionary Online.mdx"
    query = "drink"
    word = speech_thesaurus(MDX_URL, query)
    print(json.dumps(word))
