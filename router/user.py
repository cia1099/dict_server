import json
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.security import OAuth2PasswordBearer
from services.auth import verify_firebase_token, verify_api_access

router = APIRouter()


@router.get("/firebase/login")
async def firebase_login(
    token: Annotated[str, Depends(OAuth2PasswordBearer("firebase"))],
):
    try:
        access = verify_firebase_token(token)
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}
    return {"status": 200, "content": json.dumps(access)}


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
