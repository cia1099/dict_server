from fastapi import FastAPI, HTTPException, Response, status
from router.dict import router as dict_router
from database import db_life

app = FastAPI(lifespan=db_life)
app.include_router(dict_router)


@app.get("/")
async def hello_word():
    return "Hello Dictionary"
