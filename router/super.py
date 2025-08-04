from multiprocessing import Process
from typing import Annotated
from firebase_admin import credentials
from config import config
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer
from firebase.helper import clear_expirations

router = APIRouter(prefix="/admin")


@router.post(
    "/clear/anonymous", response_class=PlainTextResponse, include_in_schema=False
)
async def clear_anonymous(
    admin: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl=""))],
):
    if admin != config.FIREBASE_ADMIN:
        raise HTTPException(status_code=400, detail="Permission deny")
    cred = credentials.Certificate(admin)
    p = Process(target=clear_expirations, args=(cred,))
    p.daemon = False
    p.start()
    return "Process is setting off"
