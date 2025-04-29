import json, math
from fastapi import APIRouter, Depends, Request, Response, HTTPException

from services.character import Character
from services.auth import civvy_auth, guest_auth

router = APIRouter()


@router.get("/subscript/prices")
async def get_prices(lang: str = "en-US"):
    price = 100.0
    cut_price = round(price * 10, 2)
    origin = round(price * 12, 2)
    save = round((origin - cut_price) / origin, 2)
    discount = {"origin": origin, "save": save}
    month = {"period": "month", "price": price, "discount": None, "locale": lang}
    year = {
        "period": "year",
        "price": cut_price,
        "discount": discount,
        "locale": lang,
    }
    return {"status": 200, "content": json.dumps([month, year])}


@router.get("/advertisement")
async def advertisement(times: int = 1, character: Character = Depends(guest_auth)):
    bonus = 6.0 * math.pow(10, 1 - max(times, 1))
    token = character + bonus
    return {"status": 200, "content": str(token)}


@router.get("/subscript/premium")
async def subscript_premium(character: Character = Depends(civvy_auth)):
    character.register_premium(1)
    return {"status": 200, "content": "Successful subscription"}
