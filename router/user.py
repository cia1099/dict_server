import json
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.security import OAuth2PasswordBearer
from services.auth import verify_firebase_token, register_firebase, verify_api_access

router = APIRouter()


@router.get("/firebase/login")
async def firebase_login(
    token: Annotated[str, Depends(OAuth2PasswordBearer("firebase"))],
):
    try:
        customer = await verify_firebase_token(token)
        return {"status": 200, "content": json.dumps(customer)}
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}


@router.get("/firebase/register")
async def firebase_register(
    token: Annotated[str, Depends(OAuth2PasswordBearer("firebase"))],
    name: str | None = None,
):
    try:
        rep = await register_firebase(token, name)
        return rep
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}


@router.get("/check/access/token")
async def check_expire(req: Request):
    oauth = OAuth2PasswordBearer("check")
    try:
        access_token = await oauth(req)
        if not access_token:
            raise HTTPException(401, "Missing token")
        verify_api_access(access_token)
        return {"status": 200, "content": "Token is still availiable"}
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}
