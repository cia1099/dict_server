from fastapi import APIRouter, Depends, Request, Response, HTTPException, Header
from services.auth import premium_auth
from database import remote_cursor
import sqlalchemy as sql
from services.auth import premium_auth

router = APIRouter()


@router.post("/supabase/write")
async def supabase_write(req: Request, _=Depends(premium_auth)):
    body = await req.body()
    query = body.decode("utf-8")
    try:
        await remote_cursor.execute(sql.text(query))
        await remote_cursor.commit()
    except:
        await remote_cursor.rollback()
        return {"status": 400, "content": "Failed to write data to Supabase"}
    return {"status": 200, "content": "Successfully write to Supabase"}
