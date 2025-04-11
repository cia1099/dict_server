from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from logging import Logger


def create_macmillan_word(mdx_url: str, word: str, log: Logger | None = None) -> dict:
    res = reader.query(mdx_url, word)
    soup = BeautifulSoup(res, "lxml")
    dict_word = dict()
    for body in soup.find_all("div", class_="dict-american"):
        pass
    return dict_word
