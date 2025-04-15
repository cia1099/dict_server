from mdict_utils import reader
from bs4 import BeautifulSoup
import re, json
from pathlib import Path
from logging import Logger


def get_asset_oxfordstu(soup: BeautifulSoup):
    path = None
    try:
        img = soup.find("div", class_="pic").find("img")
        path = img["src"].replace("file", "oxfordstu")
    except:
        pass
        # print("No asset in this word")
    return path


def create_oxfordstu_word(
    soup: BeautifulSoup, word: str, log: Logger | None = None
) -> dict:
    dict_word = dict()
    for entry in soup.find_all("entry"):
        try:
            part_of_speech = entry.find("z_p").get_text()
        except:
            msg = f"'{word}' doesn't speech in <z_p> tag"
            log.debug(msg) if log else print(msg)
            continue
        # alphabet = entry.find("i").get_text() #oxfordstu can't encode utf-8
        word_defs = []
        for n_body in entry.find_all("n-g"):
            try:
                subscript = n_body.find(re.compile(r"z_(gr|pt)")).get_text()
            except:
                msg = f"'{word}' No subscript in n-g tag"
                log.debug(msg) if log else print(msg)
                subscript = entry.find(re.compile(r"(z_(gr|pt)|gram-g)"))
                if subscript:
                    subscript = (
                        "".join([f"({n5.get_text()})" for n5 in n_body.find_all("z_s")])
                        + subscript.get_text()
                    )

            # explain = n_body.find(re.compile(r"(d|xr-g)"))
            explain = n_body.find("d")
            if explain:
                explain = explain.get_text()
            else:
                msg = f"'{word}'({part_of_speech}, subscript={subscript}) doesn't have <d> tag in <n-g>"
                log.warning(msg) if log else print(msg)
                continue
            examples = [h5.get_text() for h5 in n_body.find_all("x")]
            word_defs.append(
                {"explanation": explain, "subscript": subscript, "examples": examples}
            )

        try:
            i_body = entry.find("i-g")
            hrefs = i_body.find_all("a", href=re.compile(r"sound://*"))
            audio_files = [h["href"].replace("sound", "oxfordstu") for h in hrefs]
        except:
            # raise ValueError(f"doesn't have <i-g> tag")
            audio_files = []
        # print(", ".join(["\x1b[32m%s\x1b[0m" % name for name in audio_files]))
        dict_word[part_of_speech] = {
            "def": word_defs,
            "audio": dict(zip(["uk", "us"], audio_files)),
        }
        # # ==== phrase or idioms
        # revout = entry.find(re.compile(r"(pvs|ids)-g"))
        # if revout:
        #     type_name = revout.find("revout").get_text()
        #     phrases = []
        #     for body in revout.find_all(re.compile(r"(pv|id)-g")):
        #         try:
        #             phrase = body.find(re.compile(r"pv|id")).get_text()
        #             explain = body.find("d").get_text()
        #             examples = [h5.get_text() for h5 in body.find_all("x")]
        #             phrases.append(
        #                 {
        #                     "phrase": phrase,
        #                     "explanation": explain,
        #                     "examples": examples,
        #                 }
        #             )
        #         except:
        #             msg = f"{word} fetch phrase error"
        #             log.debug(msg) if log else print(msg)
        #     dict_word[type_name] = phrases

    # ===== dr-g
    for dr_body in soup.find_all("dr-g"):
        try:
            part_of_speech = dr_body.find("z_p").get_text()
        except:
            msg = f"'{word}' doesn't speech in <z_p> tag"
            log.debug(msg) if log else print(msg)
            continue
        subscript = dr_body.find(re.compile(r"(z_(gr|pt)|gram-g)"))
        if subscript:
            subscript = (
                "".join([f"({dr5.get_text()})" for dr5 in dr_body.find_all("z_s")])
                + subscript.get_text()
            )

        explain = dr_body.find(re.compile(r"\b(zd|dr)\b"))
        if explain:
            explain = explain.get_text()
        else:
            msg = f"'{word}'({part_of_speech}, subscript={subscript}) doesn't have <dr|zd> tag in <dr-g>"
            log.warning(msg) if log else print(msg)
            continue
        examples = [h5.get_text() for h5 in dr_body.find_all("x")]
        word_def = {
            "explanation": explain,
            "subscript": subscript,
            "examples": examples,
        }
        try:
            i_body = dr_body.find("i-g")
            hrefs = i_body.find_all("a", href=re.compile(r"sound://*"))
            audio_files = [h["href"].replace("sound", "oxfordstu") for h in hrefs]
        except:
            audio_files = []
        dict_word[part_of_speech] = {
            "def": [word_def],
            "audio": dict(zip(["uk", "us"], audio_files)),
        }

    # print(json.dumps(dict_word))
    return dict_word


if __name__ == "__main__":
    from time import time
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
    from multiprocessing.pool import ThreadPool

    query = "abduct"  # "abdomen"
    mdx_url = "/Users/otto/Downloads/dict/oxfordstu.mdx"
    # print(result)

    tic = time()

    html = reader.query(mdx_url, query)
    soup = BeautifulSoup(html, "lxml")

    ## ---- Pool executor: 388 ms
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     future_oxfordstu = executor.submit(create_oxfordstu_word, soup)
    #     future_cambridge = executor.submit(get_cambridge_chinese, query)
    #     future_macmillan = executor.submit(get_macmillan_tense, query)
    # _, pron_dict = future_cambridge.result()
    # _, p2 = future_macmillan.result()
    # oxfordstu_word = future_oxfordstu.result()
    ## ---- Multiple Thread: 393 ms
    # def outer_query(query: str) -> tuple[dict]:
    #     cambridge = get_cambridge_chinese(query)
    #     macmillan = get_macmillan_tense(query)
    #     return cambridge + macmillan

    # futures = ThreadPool(processes=1).apply_async(outer_query, (query,))
    # oxfordstu_word = create_oxfordstu_word(soup)
    # _, pron_dict, _, p2 = futures.get()
    ## ---- Single core: 388 ms
    oxfordstu_word = create_oxfordstu_word(soup, query)
    print(json.dumps(oxfordstu_word))
    # print(pron_dict)
    # print(p2)
    print(f"Elapsed = \x1b[32m{(time()-tic)*1e3:.3f}\x1b[0m msec")
