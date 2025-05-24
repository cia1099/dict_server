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
    stmt = sql.select(Translation.definition_id.label("id"), Translation.zh_CN)
    stmt = stmt.where(Translation.ar_SA == None)
    cc = OpenCC("s2tw")
    log.debug("Start updating translation table with Azure")
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
                log.critical("%s" % e)
        cursor.commit()


if __name__ == "__main__":
    SRC_DB = "sqlite:///dictionary/05232025_oxfordstu.db"
    DST_DB = "sqlite:///dictionary/oxfordstu.db"
    # src_engine = create_engine(SRC_DB)
    # dst_engine = create_engine(DST_DB)
    # stmt = sql.select(Translation).where(Translation.ar_SA != None)  # .limit(5)
    # with src_engine.connect() as src:
    #     res = src.execute(stmt)
    # update = sql.update(Translation)
    # exclude = ["definition_id", "zh_CN", "word_id", "en_US"]
    # with dst_engine.connect() as dst:
    #     for row in tqdm(res.mappings().all()):
    #         id = row.get("definition_id")
    #         values = {k: row[k] for k in row if k not in exclude}
    #         dst.execute(update.where(Translation.definition_id == id).values(**values))
    #     dst.commit()

    asyncio.run(update_translate(DST_DB, batch_size=50))
    # asyncio.run(
    #     azure_translate(
    #         ["record", "drink"],
    #         src="en",
    #     )
    # )
    # for b in batch(3, range(10)):
    #     print(", ".join(("%d" % n for n in b)))
