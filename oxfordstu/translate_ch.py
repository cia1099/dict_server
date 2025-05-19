import asyncio
from aiohttp import ClientSession
from opencc import OpenCC
from sqlalchemy import create_engine
import sqlalchemy as sql
from oxfordstu_schema import Translation
import time
from functools import reduce

if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from models.translate import TranslateIn


async def azure_translate(
    texts: list[str],
    src: str = "en",
    langs: list[str] = ["ja", "ko", "vi", "ar", "th"],
):
    import json

    host = "https://api.cognitive.microsofttranslator.com"
    endpoint = "/translate"
    params = [("api-version", "3.0"), ("from", src)] + [("to", lang) for lang in langs]
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": KEY,  # config.TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": REGION,  # config.TRANSLATOR_REGION,
    }
    body = [{"Text": text} for text in texts]
    async with ClientSession(host) as session:
        res = await session.post(endpoint, json=body, headers=headers, params=params)
        obj = await res.json()

    # err = obj.get("error")
    # if err:
    #     raise HttpException(err["code"], err["message"])
    # print(json.dumps(obj))
    def lazy_result(obj: dict):
        for trs in obj:
            yield {
                TranslateIn.column(tr["to"]).name: tr["text"]
                for tr in trs.get("translations", [])
            }

    translate_maps = list(lazy_result(obj))
    print(json.dumps(translate_maps))
    return translate_maps


async def future_delay(delay: float):
    await asyncio.sleep(delay)
    print("completed %g delay" % delay)


async def main():
    tic = time.time()
    futures = (future_delay(i) for i in (1, 1, 2, 3))
    results = await asyncio.gather(*futures)
    # for f in futures:
    #     await f
    print("Elapsed time = %g" % (time.time() - tic))


if __name__ == "__main__":
    # DB_URL = "sqlite:///dictionary/oxfordstu.db"
    # engine = create_engine(DB_URL)
    # stmt = sql.select(Translation.definition_id, Translation.zh_CN).limit(10)
    # with engine.connect() as cursor:
    #     res = cursor.execute(stmt)
    # cc = OpenCC("s2tw")
    # for row in res.all():
    #     new_row = (*row, cc.convert(row[1]))
    #     print(new_row)
    # stmt = sql.update(Translation).where(Translation.definition_id == 1).values()
    # print(stmt)
    # c = TranslateIn.column("ja")
    # print(c.name)
    asyncio.run(
        azure_translate(
            ["去你妈的，我想把你推到我的床上", "你好吗，我要点一杯可乐"], src="zh-Hans"
        )
    )
