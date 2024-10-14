from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response, status
from router.dict import router as dict_router


app = FastAPI()
app.include_router(dict_router)


@app.get("/")
async def hello_word():
    return "Hello Dictionary"
