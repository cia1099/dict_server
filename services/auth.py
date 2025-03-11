import datetime, json
from firebase_admin import auth
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="firebase/login")


def verify_firebase_token(firebase_token: str | None):
    # """验证 Firebase ID Token"""
    # if not auth_header or not auth_header.startswith("Bearer "):
    #     raise HTTPException(status_code=401, detail="Missing token")

    # firebase_token = auth_header.split("Bearer ")[1]
    try:
        decoded_token = auth.verify_id_token(firebase_token)
        print(json.dumps(decoded_token, indent=4))
        return decoded_token
        # uid = decoded_token["uid"]
        # email = decoded_token.get("email", "")
        # role = decoded_token.get(
        #     "role", "guest"
        # )  # 如果使用 Firebase Custom Claims，可检查 role

        # 生成 JWT Token
        # jwt_payload = {
        #     "sub": uid,
        #     "email": email,
        #     "role": role,
        #     "exp": datetime.datetime.utcnow()
        #     + datetime.timedelta(hours=1),  # 1小时有效期
        # }
        # jwt_token = jwt.encode(jwt_payload, SECRET_KEY, algorithm=ALGORITHM)
        # return {"access_token": jwt_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid Firebase Token: {str(e)}")
