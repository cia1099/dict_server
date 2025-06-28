import datetime
import json
from typing import Annotated
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from aiofiles import open as aopen
from pathlib import Path
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from services.character import Character
from services.auth import (
    verify_firebase_token,
    register_firebase,
    verify_api_access,
    get_consume_tokens,
)
from services.auth import oauth2, guest_auth

router = APIRouter()


@router.get("/firebase/login")
async def firebase_login(token: Annotated[str, Depends(oauth2)]):
    try:
        customer = await verify_firebase_token(token)
        _ = verify_api_access(customer["access_token"])
        return {"status": 200, "content": json.dumps(customer)}
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}


@router.get("/firebase/register")
async def firebase_register(
    token: Annotated[str, Depends(oauth2)],
    name: str | None = None,
):
    try:
        rep = await register_firebase(token, name)
        return rep
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}


@router.delete("/firebase/delete")
async def firebase_delete(uid: str = Header(None)):
    auth.update_user(uid, disabled=True)
    claims = auth.get_user(uid).custom_claims or {}
    now = datetime.datetime.now(datetime.timezone.utc)
    claims["disabled_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    auth.set_custom_user_claims(uid, claims)


@router.get("/check/access/token")
async def check_expire(req: Request):
    try:
        access_token = await oauth2(req)
        if not access_token:
            raise HTTPException(401, "Missing token")
        verify_api_access(access_token)
        return {"status": 200, "content": "Token is still availiable"}
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}


@router.get("/firebase/consume/token")
async def request_consume_tokens(character: Character = Depends(guest_auth)):
    consume_tokens = await get_consume_tokens(character)
    isNone = consume_tokens is None
    return {
        "status": 200 if not isNone else 404,
        "content": (
            str(consume_tokens) if not isNone else "You don't available consume"
        ),
    }


@router.get("/firebase/auth/action")
async def get_reset_password_page(mode: str, oobCode: str, apiKey: str):
    if mode == "verifyEmail":
        return RedirectResponse(
            f"https://ai-vocabulary-firebase.firebaseapp.com/__/auth/action?mode={mode}&oobCode={oobCode}&apiKey={apiKey}"
        )
    p = Path("templates/reset_password.html")
    async with aopen(str(p)) as f:
        html = await f.read()
    return HTMLResponse(html)
