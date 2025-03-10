from fastapi import FastAPI, HTTPException, Response, status, Request
from router.dict import router as dict_router
from router.img import router as img_router
from router.audio import router as audio_router
from router.chat import router as chat_router
from database import db_life

app = FastAPI(lifespan=db_life, root_path="/dict")
app.include_router(dict_router)
app.include_router(img_router)
app.include_router(audio_router)
app.include_router(chat_router)


@app.get("/")
async def hello_word():
    # return Response("error occur", status_code=404, media_type="text/plain")
    return "Hello Dictionary"
