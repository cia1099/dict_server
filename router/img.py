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
from PIL import Image
from aiohttp import ClientSession

from __init__ import config

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
        fp.seek(0)
        img = Image.open(fp)
    img.show()
    fp.close()
    print(revised_prompt)


async def imagen(prompt: str):
    host = "https://imagener.openai.azure.com"
    endpoint = "/openai/images/generations:submit?api-version=2023-06-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": config.AZURE_OPENAI_API_KEY,
    }
    body = {"prompt": prompt, "size": "256x256", "n": 1}
    async with ClientSession(host) as session:
        res = await session.post(endpoint, json=body, headers=headers)
        jobj: dict = await res.json()
        # print(jobj)
        id = jobj["id"]
        img_point = endpoint.replace("generations:submit", id).replace(
            "openai", "openai/operations"
        )
        while jobj["status"] != "succeeded":
            await asyncio.sleep(1)
            res = await session.get(img_point, headers=headers)
            jobj = await res.json()
            # print(jobj)
        url = jobj["result"]["data"][0]["url"]
    async with ClientSession() as client:
        res = await client.get(url)
        fp = BytesIO()
        async for bytes in res.content.iter_chunked(1024 * 512):
            fp.write(bytes)
        fp.seek(0)
        img = Image.open(fp)
    img.show()
    fp.close()


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
    prompt = "She's hoping to break the record for the 100 metres.(Please emphasize the 'record' as noun in this sentence)"
    # asyncio.run(imagener(prompt))
    asyncio.run(imagen(prompt))
