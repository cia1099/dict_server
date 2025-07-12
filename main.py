from pathlib import Path
from multiprocessing import Process
from fastapi import FastAPI, HTTPException, Response, status, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from scalar_fastapi import get_scalar_api_reference
from aiohttp import ClientResponseError
from router.dict import router as dict_router
from router.img import router as img_router
from router.audio import router as audio_router
from router.chat import router as chat_router
from router.user import router as user_router
from router.translate import router as translate_router
from router.pay import router as pay_router
from router.remote_db import router as db_router
from router.super import router as super_router
from database import db_life
from firebase.helper import clear_expirations
from config import config

from log_config import LOGGER_SETTINGS
import logging, logging.config


def app_life(app: FastAPI):
    from firebase_admin import credentials, initialize_app

    cred = credentials.Certificate(config.FIREBASE_ADMIN)
    # p = Process(target=clear_expirations, args=(cred,))
    # p.daemon = False
    # p.start()
    initialize_app(cred)
    # logging.config.dictConfig(LOGGER_SETTINGS)

    return db_life(app)


app = FastAPI(
    lifespan=app_life,
    root_path="/dict",
    title="AI Vocabulary Dictionary",
    version="1.0.1",
    docs_url=None,
    redoc_url=None,
)

app.include_router(dict_router)
app.include_router(img_router)
app.include_router(audio_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(translate_router)
app.include_router(pay_router)
app.include_router(db_router)
app.include_router(super_router)


@app.exception_handler(ClientResponseError)
async def client_exception_handler(_, exc: ClientResponseError):
    elog = logging.getLogger("error")
    elog.error(f"{exc.message} {exc.status}")
    raise HTTPException(exc.status, exc.message)
    return PlainTextResponse(exc.message, exc.status)


@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url or "",
        title=app.title,
    )


@app.get("/", tags=["Test"])
async def hello_word(name: str | None = None):
    return f"Hello Dictionary {name}"
