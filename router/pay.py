import datetime
import json, math
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from aiohttp import ClientSession
from firebase_admin import auth
import jwt
from config import config
from services.character import Character
from services.auth import member_auth, guest_auth

router = APIRouter()


# @router.get("/subscript/prices")
# async def get_prices(lang: str = "en-US"):
#     price = 100.0
#     cut_price = round(price * 10, 2)
#     origin = round(price * 12, 2)
#     save = round((origin - cut_price) / origin, 2)
#     discount = {"origin": origin, "save": save}
#     month = {"period": "month", "price": price, "discount": None, "locale": lang}
#     year = {
#         "period": "year",
#         "price": cut_price,
#         "discount": discount,
#         "locale": lang,
#     }
#     return {"status": 200, "content": json.dumps([month, year])}


@router.get("/advertisement")
async def advertisement(times: int = 1, character: Character = Depends(guest_auth)):
    bonus = 6.0 * math.pow(10, 1 - max(times, 1))
    token = character + bonus
    return {"status": 200, "content": str(token)}


@router.patch("/update/subscript/attributes")
async def update_attributes(req: Request, character: Character = Depends(member_auth)):
    body = await req.body()
    entitle_dict = json.loads(str(body, "utf-8"))
    role = entitle_dict.get("identifier", "member").lower()
    start = entitle_dict.get("latestPurchaseDate")
    if isinstance(start, str):
        t = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        start = int(t.timestamp())
    end = entitle_dict.get("expirationDate")
    if isinstance(end, str):
        t = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        end = int(t.timestamp())
    gas = entitle_dict.get("gas", 0.0)

    character.update_claims(role=role, start=start, end=end, gas=gas)
    user: auth.UserRecord = auth.get_user(character.uid)

    expire = datetime.datetime.fromtimestamp(
        (user.user_metadata.last_sign_in_timestamp or 0) * 1e-3
    ) + datetime.timedelta(days=1)
    play_load = {"uid": user.uid, "role": role, "exp": expire}
    access_token = jwt.encode(play_load, key=config.JWT_SECRETE_KEY)
    return {
        "status": 200,
        "content": json.dumps(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "uid": user.uid,
                "name": user.display_name,
                "email": user.email,
                "role": role,
            }
        ),
    }


async def subscript_status(uid: str):
    PUBLIC_KEY = "appl_BhfSwLRtzObwxuwlHUNddWezqtr"
    host = "https://api.revenuecat.com/v1/"
    endpoint = f"subscribers/{uid}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PUBLIC_KEY}",
    }
    async with ClientSession(host) as session:
        async with session.get(endpoint, headers=headers) as res:
            res.raise_for_status()
            jobj = await res.json()
        print(json.dumps(jobj))
