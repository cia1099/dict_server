from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.security import OAuth2PasswordBearer
from services.auth import verify_firebase_token

router = APIRouter()


@router.get("/firebase/login")
async def firebase_login(
    token: Annotated[str, Depends(OAuth2PasswordBearer("firebase"))],
):
    try:
        access = verify_firebase_token(token)
    except HTTPException as e:
        return {"status": e.status_code, "content": e.detail}
    return {"status": 200, "content": access}
