import json
from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
import sqlalchemy as sql

from models.translate import TranslateIn
from oxfordstu.oxfordstu_schema import Translation
from aiohttp import ClientSession

from database import engine
from services.auth import premium_auth
from config import config

router = APIRouter()


@router.post("/definition/translation")
async def definition_translation(body: TranslateIn, _=Depends(premium_auth)):
    if not body.definition_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "null value in definition_id")
    lang = body.locate()
    stmt = sql.select(lang).where(Translation.definition_id == body.definition_id)
    async with engine.connect() as cursor:
        res = await cursor.execute(stmt)
    tr = res.scalar_one_or_none() or ""
    return {"status": 200, "content": tr}


@router.post("/azure/translate")
async def dict_translate(body: TranslateIn):
    if not body.lang or not body.text:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "null value in language or text"
        )
    translate_maps = await azure_translate([body.text], langs=[body.lang])
    tr = translate_maps[0].get(body.lang, "")
    return {"status": 200, "content": tr}


async def azure_translate(
    texts: list[str],
    src: str = "en",
    langs: list[str] = ["ja", "ko", "vi", "ar", "th"],
):
    host = "https://api.cognitive.microsofttranslator.com"
    endpoint = "/translate"
    params = [("api-version", "3.0"), ("from", src)] + [("to", lang) for lang in langs]
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": config.TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": config.TRANSLATOR_REGION,
    }
    body = [{"Text": text} for text in texts]
    async with ClientSession(host) as session:
        async with session.post(
            endpoint, json=body, headers=headers, params=params
        ) as res:
            res.raise_for_status()
            obj = await res.json()
    if isinstance(obj, dict):
        err = obj.get("error", {"code": 555, "message": "Azure failed"})
        raise HTTPException(err["code"], err["message"])

    # print(json.dumps(obj))
    def lazy_result(obj: list[dict]):
        for trs in obj:
            yield {
                TranslateIn.column(tr["to"]).name: tr["text"]
                for tr in trs.get("translations", [])
            }

    translate_maps = list(lazy_result(obj))
    # print(json.dumps(translate_maps))
    return translate_maps
