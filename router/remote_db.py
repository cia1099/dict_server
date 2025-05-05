from fastapi import APIRouter, Depends, Request, Response, HTTPException, Header
from services.auth import premium_auth
from database import remote_engine
import sqlalchemy as sql
from services.auth import premium_auth

router = APIRouter()


@router.post("/supabase/write")
async def supabase_write(req: Request, _=Depends(premium_auth)):
    body = await req.body()
    query = body.decode("utf-8")
    async with remote_engine.connect() as cursor:
        try:
            await cursor.execute(sql.text(query))
            await cursor.commit()
        except:
            await cursor.rollback()
            return {"status": 500, "content": "Failed to write data to Supabase"}
    return {"status": 200, "content": "Successfully write to Supabase"}
