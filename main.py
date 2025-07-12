from pathlib import Path
from multiprocessing import Process
from fastapi import FastAPI, HTTPException, Response, status, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from aiofiles import open as aopen
from aiohttp import ClientResponseError
from router.dict import router as dict_router
from router.img import router as img_router
from router.audio import router as audio_router
from router.chat import router as chat_router
from router.user import router as user_router
from router.translate import router as translate_router
from router.pay import router as pay_router
from router.remote_db import router as db_router
from database import db_life
from firebase.helper import clear_expirations
from config import config

from log_config import LOGGER_SETTINGS
import logging, logging.config


def app_life(app: FastAPI):
    import firebase_admin
    from firebase_admin import credentials

    cred = credentials.Certificate(config.FIREBASE_ADMIN)
    p = Process(target=clear_expirations, args=(cred,))
    p.daemon = False
    p.start()
    firebase_admin.initialize_app(cred)
    logging.config.dictConfig(LOGGER_SETTINGS)

    return db_life(app)


app = FastAPI(lifespan=app_life, root_path="/dict")
app.include_router(dict_router)
app.include_router(img_router)
app.include_router(audio_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(translate_router)
app.include_router(pay_router)
app.include_router(db_router)


@app.exception_handler(ClientResponseError)
async def client_exception_handler(_, exc: ClientResponseError):
    elog = logging.getLogger("error")
    elog.error(f"{exc.message} {exc.status}")
    raise HTTPException(exc.status, exc.message)
    return PlainTextResponse(exc.message, exc.status)


@app.get("/")
async def hello_word(name: str | None = None):
    return f"Hello Dictionary {name}"
