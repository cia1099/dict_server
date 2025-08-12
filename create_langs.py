from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString
import json, asyncio
from typing import cast
from router.translate import azure_translate

if __name__ == "__main__":
    filename = "/Users/otto/project/entry/assets/langs.yaml"
    yaml = YAML()
    yaml.preserve_quotes = True  # 保留引號
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(filename) as f:
        map = yaml.load(f)["zh_TW"]
    # print(json.dumps(data))
    app_name = map["app_name"]
    app_subtitle = map["app_subtitle"]
    keywords = map["keywords"]
    description: str = map["description"]
    screenshot: dict = map["screenshot"]
    base_list = [app_name, app_subtitle, keywords, description]
    texts = base_list + [t for _, page in screenshot.items() for t in page.values()]
    # print(json.dumps(texts))
    translate = asyncio.run(
        azure_translate(texts=texts, src="zh-Hant", langs=["ja", "ko", "vi"])
    )
    # print(json.dumps(translate))
    for lang in ["ja_JP", "ko_KR", "vi_VN"]:
        new_shot = {k: page for k, page in screenshot.items()}
        i = len(base_list)
        for page in new_shot.values():
            for k in page.keys():
                page[k] = translate[i][lang]
                i += 1
        # print(json.dumps(new_shot))
        # print(translate[0][lang])
        new_lang = {
            "app_name": translate[0][lang],
            "app_subtitle": translate[1][lang],
            "keywords": translate[2][lang],
            "description": LiteralScalarString(translate[3][lang]),
            "screenshot": new_shot,
        }

        with open(filename, "a") as f:
            yaml.dump({lang: new_lang}, f)

    # ---- en base
    with open(filename) as f:
        map = yaml.load(f)["en"]
    app_name = map["app_name"]
    app_subtitle = map["app_subtitle"]
    keywords = map["keywords"]
    description: str = map["description"]
    screenshot: dict = map["screenshot"]
    base_list = [app_name, app_subtitle, keywords, description]
    texts = base_list + [t for _, page in screenshot.items() for t in page.values()]
    translate = asyncio.run(azure_translate(texts=texts, src="en", langs=["th", "ar"]))
    for lang in ["th_TH", "ar_SA"]:
        new_shot = {k: page for k, page in screenshot.items()}
        i = len(base_list)
        for page in new_shot.values():
            for k in page.keys():
                page[k] = translate[i][lang]
                i += 1
        new_lang = {
            "app_name": translate[0][lang],
            "app_subtitle": translate[1][lang],
            "keywords": translate[2][lang],
            "description": LiteralScalarString(translate[3][lang]),
            "screenshot": new_shot,
        }

        with open(filename, "a") as f:
            yaml.dump({lang: new_lang}, f)
