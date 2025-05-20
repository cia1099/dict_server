import asyncio
from math import ceil
from opencc import OpenCC
from sqlalchemy import create_engine
import sqlalchemy as sql
from tqdm import tqdm
from oxfordstu_schema import Translation
import time
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from router.translate import azure_translate
from log_config import log


def batch(size: int, it: Iterable[T]) -> Iterator[list[T]]:
    batch = []
    for item in it:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


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


async def update_translate(url: str, batch_size: int = 10):
    engine = create_engine(url)
    stmt = sql.select(Translation.definition_id.label("id"), Translation.zh_CN).limit(5)
    cc = OpenCC("s2tw")
    with engine.connect() as cursor:
        res = cursor.execute(stmt)
        seq = res.mappings().all()
        for rows in tqdm(batch(batch_size, seq), total=ceil(len(seq) / batch_size)):
            texts = [row["zh_CN"] for row in rows]
            try:
                translate_maps = await azure_translate(texts, src="zh-Hans")
                for i, map in enumerate(translate_maps):
                    map["zh_TW"] = cc.convert(texts[i])
                    id = rows[i]["id"]
                    stmt = (
                        sql.update(Translation)
                        .where(Translation.definition_id == id)
                        .values(**map)
                    )
                    cursor.execute(stmt)
            except Exception as e:
                log.info("%s" % e)
                log.warning(
                    "Failed translate id at [%s]"
                    % ", ".join(["%d" % row["id"] for row in rows])
                )
        cursor.commit()


if __name__ == "__main__":
    DB_URL = "sqlite:///dictionary/oxfordstu.db"
    asyncio.run(update_translate(DB_URL, 2))
    # asyncio.run(
    #     azure_translate(
    #         ["去你妈的，我想把你推到我的床上", "你好吗，我要点一杯可乐"], src="zh-Hans"
    #     )
    # )
    # for b in batch(3, range(10)):
    #     print(", ".join(("%d" % n for n in b)))
