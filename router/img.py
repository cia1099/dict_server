from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response, HTTPException

router = APIRouter()


@router.get("/dictionary/img/thumb/{image_name}")
async def dictionary_img_thumb(image_name: str):
    try:
        p = Path(f"dictionary/img/thumb/{image_name}")
        with open(str(p), "rb") as f:
            return Response(f.read(), media_type=f"image/{p.suffix[1:]}")
    except:
        return HTTPException(404, detail=f"{p} not found or destroyed")


def convert_asset_url(word_dict: dict, req: Request | None):
    word = word_dict
    if word["asset"] and req:
        asset: str = word["asset"]
        if asset.startswith("oxfordstu"):
            asset = asset.replace("oxfordstu:", "dictionary")
        p = Path(asset)
        asset_url = req.url_for("_".join(p.parent.parts), image_name=p.name)
        word["asset"] = str(asset_url)
    return word
