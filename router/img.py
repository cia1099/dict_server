if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
import asyncio, datetime, os
from io import BytesIO
from pathlib import Path
from aiofiles import open
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from aiohttp import ClientResponseError, ClientSession
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

from config import config
from models.role import Role
from services.auth import ApiAuth
from services.utils import read_ram_chunk, iter_file
from services.gcloud import create_punch_cards
from services.runware import runware_imagen

router = APIRouter()
img_auth = ApiAuth(Role.MEMBER, cost_token=2)


@router.get("/dictionary/img/thumb/{image_name}")
async def dictionary_img_thumb(image_name: str):
    try:
        p = Path(f"dictionary/img/thumb/{image_name}")
        async with open(str(p), "rb") as f:
            file_size = os.fstat(f.fileno()).st_size
            return Response(
                await f.read(),
                media_type=f"image/{p.suffix[1:]}",
                headers={"Content-Length": str(file_size)},
            )
    except:
        raise HTTPException(404, detail=f"{p} not found or destroyed")


async def imagener(prompt: str):
    host = "https://imagener.openai.azure.com"
    endpoint = "/openai/deployments/dalle3/images/generations?api-version=2024-02-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": config.AZURE_OPENAI_API_KEY,
    }
    body = {
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
        "style": "natural",
    }
    async with ClientSession(host) as session:
        async with session.post(endpoint, json=body, headers=headers) as res:
            res.raise_for_status()
            jobj: dict = await res.json()
    url: str = jobj["data"][0]["url"]
    revised_prompt: str = jobj["data"][0]["revised_prompt"]

    async with ClientSession() as client:
        async with client.get(url) as res:
            res.raise_for_status()
            fp = BytesIO()
            async for bytes in res.content.iter_chunked(1024 * 512):
                fp.write(bytes)
    # TODO if you need revised prompt
    # return {
    #     "status": 200,
    #     "content": json.dumps({"url": url, "revised_prompt": revised_prompt}),
    # }
    fp.seek(0)
    img = Image.open(fp)
    img.show()
    fp.close()
    print(revised_prompt)


@router.get("/imagen/{size}")
async def imagen(prompt: str, size: int = 256, _=Depends(img_auth)):
    fp = await runware_imagen(prompt, steps=8)
    # cost_token = 2e-2 * 100
    img_size = fp.getbuffer().nbytes
    return StreamingResponse(
        read_ram_chunk(fp),
        # media_type="image/png",
        media_type="image/jpeg",
        headers={"Content-Length": str(img_size)},
    )


@router.get("/imagen/punch/card/qr_code")
async def qr_code():
    p = Path(f"punch_card/qr_code.png")
    try:
        async with open(str(p), "rb") as f:
            file_size = os.fstat(f.fileno()).st_size
            return Response(
                await f.read(),
                media_type=f"image/{p.suffix[1:]}",
                headers={"Content-Length": str(file_size)},
            )
    except:
        raise HTTPException(404, detail=f"{p} not found or destroyed")


@router.get("/imagen/punch/card/{index}")
async def punch_card(index: int):
    now = datetime.datetime.now()
    monday = now - datetime.timedelta(days=now.weekday())
    filename = f"{monday.year}{monday.month:02}{monday.day:02}"
    file = Path(f"punch_card/{filename}_{index:02}.png")
    waiting_times = 5
    while not file.exists() and waiting_times > 0:
        waiting_times -= 1
        if index == 0:
            await create_punch_cards(filename)
        else:
            await asyncio.sleep(3)
    if not file.exists():
        raise HTTPException(404, "Failed generation card")

    file_size = os.path.getsize(file)
    return StreamingResponse(
        iter_file(str(file)),
        media_type="image/png",
        headers={"Content-Length": str(file_size)},
    )


@router.get("/auth/cover/edge.png")
async def get_app_cover_edge():
    p = Path(f"punch_card/edge.png")
    try:
        async with open(str(p), "rb") as f:
            file_size = os.fstat(f.fileno()).st_size
            return Response(
                await f.read(),
                media_type=f"image/{p.suffix[1:]}",
                headers={"Content-Length": str(file_size)},
            )
    except:
        raise HTTPException(404, detail=f"{p} not found or destroyed")


def generate_error_img(message: str, size: int = 512) -> BytesIO:
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_size = 32
    text_x = (size - font_size * len(message) // 2) // 2
    text_y = (size - font_size) // 2
    draw.text((text_x, text_y), message, fill=(255, 0, 0), font_size=font_size)
    fp = BytesIO()
    img.save(fp, format="png")
    return fp


# TODO: calculate words in center image
def draw_text(size: int):
    content = "shit man"
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_size = 40
    # font = ImageFont.truetype("Arial.ttf", font_size)
    boxW = size - font_size * 2
    row = len(content) * font_size // boxW
    col = boxW // font_size
    boxH = row * (font_size + font_size // 4)
    y = (size - boxH // 2) // 2
    for dy in range(row):
        for dx in range(len(content)):
            c = content[dx + dy * col]
            offset = (
                dx * font_size // 2 + font_size,
                y + dy * (font_size + font_size // 4) // 2,
            )
            draw.text(offset, c, fill=(255, 0, 0), font_size=font_size)

    # text_x = (size - font_size * len(content) // 2) // 2
    # text_y = (size - font_size) // 2
    # draw.multiline_text(
    #     (text_x, text_y), content, fill=(255, 0, 0), font_size=font_size
    # )
    img.show()


def replace_root(url: str, new_root: str = "dictionary"):
    if url.startswith("oxfordstu"):
        url = url.replace("oxfordstu:", new_root)
    return url


def convert_asset_url(word_dict: dict, req: Request):
    word = word_dict
    if word.get("asset"):
        asset: str = word["asset"]
        asset = replace_root(asset)
        p = Path(asset)
        asset_url = req.url_for("_".join(p.parent.parts), image_name=p.name)
        word["asset"] = str(asset_url)  # .replace("http", "https")
    for i, word_def in enumerate(word["definitions"]):
        if word_def.get("audio_us"):
            audio = replace_root(word_def["audio_us"])
            p = Path(audio)
            audio_url = req.url_for("_".join(p.parent.parts), filename=p.name)
            word["definitions"][i]["audio_us"] = str(audio_url)
        if word_def.get("audio_uk"):
            audio = replace_root(word_def["audio_uk"])
            p = Path(audio)
            audio_url = req.url_for("_".join(p.parent.parts), filename=p.name)
            word["definitions"][i]["audio_uk"] = str(audio_url)

    return word


if __name__ == "__main__":
    # prompt = "Daylight came in through a chink between the curtains."
    # prompt = "There is an apple juicy on the table."
    prompt = "The child is drinking a bottle of apple juicy."
    import time
    from PIL import Image

    tic = time.perf_counter()
    # fp = asyncio.run(vertex_imagen(prompt))
    # asyncio.run(create_punch_cards("20250626"))
    toc = time.perf_counter()
    # img = Image.open(fp)
    # img.show()
    # print(f"Elapsed time = {toc-tic:.4f} sec")
    # asyncio.run(imagener(prompt))
    # asyncio.run(imagen(prompt, 600))
    # draw_text(256)
