if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
import asyncio
from io import BytesIO
from pathlib import Path
from aiofiles import open
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from aiohttp import ClientSession
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

from __init__ import config
from router.audio import read_ram_chunk

router = APIRouter()


@router.get("/dictionary/img/thumb/{image_name}")
async def dictionary_img_thumb(image_name: str):
    try:
        p = Path(f"dictionary/img/thumb/{image_name}")
        async with open(str(p), "rb") as f:
            return Response(await f.read(), media_type=f"image/{p.suffix[1:]}")
    except:
        return HTTPException(404, detail=f"{p} not found or destroyed")


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
        res = await session.post(endpoint, json=body, headers=headers)
        jobj: dict = await res.json()
        url: str = jobj["data"][0]["url"]
        revised_prompt: str = jobj["data"][0]["revised_prompt"]

    async with ClientSession() as client:
        res = await client.get(url)
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


async def vertex_imagen(prompt: str) -> BytesIO:
    locate = "us-central1"
    host = f"https://{locate}-aiplatform.googleapis.com"
    model = "imagegeneration@002"
    endpoint = f"/v1/projects/china-wall-over/locations/{locate}/publishers/google/models/{model}:predict"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
        },
    }
    import json, base64
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import Request

    credentials = Credentials.from_service_account_file(
        config.GCLOUD_SERVICE_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    # print(f"get token = {credentials.token}")
    headers.update({"Authorization": f"Bearer {credentials.token}"})

    async with ClientSession(host) as session:
        res = await session.post(endpoint, json=body, headers=headers)
        jobj: dict = await res.json()
        pred = jobj.get("predictions")
        if pred:
            bytes = base64.b64decode(pred[0]["bytesBase64Encoded"])
            fp = BytesIO(bytes)
            pred[0].update({"bytesBase64Encoded": None})
            print(json.dumps(pred, indent=4))
        else:
            print(json.dumps(jobj, indent=4))
            fp = generate_error_img(jobj["error"]["message"])

    if pred and __name__ == "__main__":
        img = Image.open(fp)
        img.show()
        fp.close()
    return fp


@router.get("/imagen/punch/card/{index}")
async def punch_card():
    prompt = "Generate cute animals to encourage people to finish dairy task\
          of memorizing vocabulary.\nThe slogan like:\n\
        AI Vocabulary Punch Card\nMemorize words\nI'm memorizing words with AI Vocabulary, punch with me!"


@router.get("/imagen/{size}")
async def imagen(prompt: str, size: int = 256):
    host = "https://imagener.openai.azure.com"
    endpoint = "/openai/images/generations:submit?api-version=2023-06-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": config.AZURE_OPENAI_API_KEY,
    }
    ssize = "x".join("%d" % (size & (1 << 8 | 1 << 9 | 1 << 10)) for _ in range(2))
    body = {"prompt": prompt, "size": ssize, "n": 1}
    async with ClientSession(host) as session:
        res = await session.post(endpoint, json=body, headers=headers)
        jobj: dict = await res.json()
        # print(jobj)
        id = jobj["id"]
        img_point = endpoint.replace("generations:submit", id).replace(
            "openai", "openai/operations"
        )
        while jobj["status"] != "succeeded" and jobj["status"] != "failed":
            await asyncio.sleep(1)
            res = await session.get(img_point, headers=headers)
            jobj = await res.json()
            # print(jobj)
        if jobj["status"] == "failed":
            error: dict = jobj["error"]
            # content = f"({error['code']}){error['message']}"
            content = "Blocked by sensitive content"
            fp = generate_error_img(content, size)
            return StreamingResponse(read_ram_chunk(fp), media_type=f"image/png")

        if jobj.get("result"):
            url = jobj["result"]["data"][0]["url"]
        else:
            url = jobj["data"][0]["url"]
    async with ClientSession() as client:
        res = await client.get(url)
        fp = BytesIO()
        async for bytes in res.content.iter_chunked(1024 * 512):
            fp.write(bytes)
    if __name__ != "__main__":
        return StreamingResponse(read_ram_chunk(fp), media_type=f"image/png")
    else:
        fp.seek(0)
        img = Image.open(fp)
        img.show()
        fp.close()


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
        word["asset"] = str(asset_url).replace("http", "https")
    for i, word_def in enumerate(word["definitions"]):
        if word_def.get("audio_us"):
            audio = replace_root(word_def["audio_us"])
            p = Path(audio)
            audio_url = req.url_for("_".join(p.parent.parts), filename=p.name)
            word["definitions"][i]["audio_us"] = str(audio_url).replace("http", "https")
        if word_def.get("audio_uk"):
            audio = replace_root(word_def["audio_uk"])
            p = Path(audio)
            audio_url = req.url_for("_".join(p.parent.parts), filename=p.name)
            word["definitions"][i]["audio_uk"] = str(audio_url).replace("http", "https")

    return word


if __name__ == "__main__":
    # prompt = "Daylight came in through a chink between the curtains."
    prompt = "There is an apple juicy on the table."
    import time

    tic = time.perf_counter()
    asyncio.run(vertex_imagen(prompt))
    toc = time.perf_counter()
    print(f"Elapsed time = {toc-tic:.4f} sec")
    # asyncio.run(imagener(prompt))
    # asyncio.run(imagen(prompt, 600))
    # draw_text(256)
