from typing import Annotated
import datetime, json
from firebase_admin import auth
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from models.role import Role, Character
from __init__ import config

oauth2 = OAuth2PasswordBearer("arbitrary url")


async def verify_firebase_token(firebase_token: str | None) -> dict:
    try:
        firebase = auth.verify_id_token(firebase_token)
        # return firebase
        uid = firebase["uid"]
        email = firebase.get("email", "")
        role = firebase.get("role", "guest")
        name = firebase.get("name", "TODO Faker")
        auth_time = firebase.get(
            "auth_time", datetime.datetime.now(datetime.timezone.utc)
        )

        # 生成 JWT Token
        expire = datetime.datetime.fromtimestamp(auth_time) + datetime.timedelta(days=1)
        play_load = {"uid": uid, "role": role, "exp": expire}
        access_token = jwt.encode(play_load, key=config.JWT_SECRETE_KEY)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "uid": uid,
            "name": name if name else "TODO Faker",
            "email": email,
        }

    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid Firebase Token: {str(e)}")


async def register_firebase(firebase_token: str, name: str | None):
    try:
        firebase = auth.verify_id_token(firebase_token)
        uid = firebase["uid"]
        auth.set_custom_user_claims(
            uid,
            {"role": Role.CIVVY, "name": name if name else "TODO Faker", "token": 10.0},
        )
        return {"status": 200, "content": "Successfully create a User"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Firebase Token: {str(e)}",
        )


def verify_api_access(token: Annotated[str, Depends(oauth2)]):
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
    return Character.from_dict(play_load)


class ApiAuth:
    # static member
    role_index_map = {role: i for i, role in enumerate(Role)}

    def __init__(self, role: Role, cost_token: float = 0):
        self.role = role
        self.cost_token = cost_token

    def __call__(self, character: Character = Depends(verify_api_access)):
        if self.role_index_map[self.role] > ApiAuth.role_index_map[character.role]:
            raise HTTPException(403, "Permission denied")
        if self.cost_token > 0:
            claims = auth.get_user(character.uid).custom_claims or {}
            user_token = claims.get("token", 0.0)
            if user_token < self.cost_token:
                raise HTTPException(403, "Don't have enough token")
            user_token -= self.cost_token
            claims.update({"token": user_token})
            auth.set_custom_user_claims(character.uid, claims)
