from fastapi import FastAPI, HTTPException, Response, status, Request
from router.dict import router as dict_router
from router.img import router as img_router
from database import db_life

app = FastAPI(lifespan=db_life)
app.include_router(dict_router)
app.include_router(img_router)


@app.get("/")
async def hello_word():
    return "Hello Dictionary"
