from typing import Annotated
import datetime, json
from firebase_admin import auth
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from models.role import Role
from __init__ import config


async def verify_firebase_token(firebase_token: str | None) -> dict:
    try:
        firebase = auth.verify_id_token(firebase_token)
        # return firebase
        uid = firebase["uid"]
        email = firebase.get("email", "")
        role = firebase.get("role", "guest")
        token = firebase.get("token", 0)
        name = firebase.get("name", "TODO Faker")
        auth_time = firebase.get(
            "auth_time", datetime.datetime.now(datetime.timezone.utc)
        )

        # 生成 JWT Token
        expire = datetime.datetime.fromtimestamp(auth_time) + datetime.timedelta(days=1)
        play_load = {"role": role, "token": token, "exp": expire}
        access_token = jwt.encode(play_load, key=config.JWT_SECRETE_KEY)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "uid": uid,
            "name": name,
            "email": email,
        }

    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid Firebase Token: {str(e)}")


async def register_firebase(firebase_token: str, name: str | None):
    try:
        firebase = auth.verify_id_token(firebase_token)
        uid = firebase["uid"]
        auth.set_custom_user_claims(uid, {"role": "civvy", "name": name, "token": 0})
        return {"status": 200, "content": "Successfully create a User"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Firebase Token: {str(e)}",
        )


def verify_api_access(
    token: Annotated[str, Depends(OAuth2PasswordBearer("access_token"))],
):
    try:
        play_load = jwt.decode(token, key=config.JWT_SECRETE_KEY)
    except ExpiredSignatureError as e:
        raise HTTPException(
            401, "Token has expired", headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Role.from_dict(play_load)
