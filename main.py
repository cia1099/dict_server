from typing import Annotated
from fastapi import FastAPI, HTTPException, Response, status, Request, Depends
from router.dict import router as dict_router
from router.img import router as img_router
from router.audio import router as audio_router
from router.chat import router as chat_router
from router.user import router as user_router
from database import db_life
from __init__ import config


def app_life(app: FastAPI):
    import firebase_admin
    from firebase_admin import credentials

    cred = credentials.Certificate(config.FIREBASE_ADMIN)
    firebase_admin.initialize_app(cred)

    return db_life(app)


app = FastAPI(lifespan=app_life, root_path="/dict")
app.include_router(dict_router)
app.include_router(img_router)
app.include_router(audio_router)
app.include_router(chat_router)
app.include_router(user_router)


@app.get("/")
async def hello_word(name: str | None = None):
    # return Response("error occur", status_code=404, media_type="text/plain")
    return f"Hello Dictionary {name}"
