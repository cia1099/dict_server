import datetime
import json, math
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from aiohttp import ClientSession
from firebase_admin import auth
import jwt
from config import config
from services.character import Character
from services.auth import member_auth, guest_auth
from log_config import elog

router = APIRouter()


@router.patch("/update/subscript/attributes")
async def update_attributes(req: Request, character: Character = Depends(member_auth)):
    body = await req.body()
    entitle_dict = json.loads(str(body, "utf-8"))
    role = entitle_dict.get("identifier", "member").lower()
    start = entitle_dict.get("latestPurchaseDate")
    end = entitle_dict.get("expirationDate")

    claims = {"role": role, "start": start, "end": end}
    gas = entitle_dict.get("gas")
    if gas or role == "member":
        claims["gas"] = gas if role != "member" else 0.0

    character.update_claims(**claims)
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
                "name": user.display_name or user.email.split("@")[0],
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
