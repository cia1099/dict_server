from pathlib import Path
from aiofiles import open
from fastapi import APIRouter, Depends, Request, Response, HTTPException

router = APIRouter()


@router.get("/dictionary/img/thumb/{image_name}")
async def dictionary_img_thumb(image_name: str):
    try:
        p = Path(f"dictionary/img/thumb/{image_name}")
        async with open(str(p), "rb") as f:
            return Response(await f.read(), media_type=f"image/{p.suffix[1:]}")
    except:
        return HTTPException(404, detail=f"{p} not found or destroyed")


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
