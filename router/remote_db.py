import json
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from models.pull import PullIn
from client.client_shcema import Acquaintance, parse_condition
from database import remote_engine, metadata
import sqlalchemy as sql
from services.auth import premium_auth, civvy_auth

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


@router.delete("/supabase/erase")
async def supabase_delete(req: Request, _=Depends(civvy_auth)):
    body = await req.body()
    query = body.decode("utf-8")
    async with remote_engine.connect() as cursor:
        try:
            await cursor.execute(sql.text(query))
            await cursor.commit()
        except:
            await cursor.rollback()
            return {"status": 500, "content": "Failed to erase data in Supabase"}
    return {"status": 200, "content": "Successfully erase Supabase"}


@router.post("/supabase/pull")
async def supabase_pull(pull: PullIn, page: int = 0, max_length: int = 200):
    table = metadata.tables.get(pull.tablename)
    if table is None:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "content": "No '%s' table in database" % pull.tablename,
        }
    condition = parse_condition(**pull.model_dump())
    stmt = (
        sql.select(*(sql.column(c) for c in table.c.keys() if c != "user_id"))
        .where(condition)
        .limit(max_length)
        .offset(max_length * page)
    )
    async with remote_engine.connect() as cursor:
        res = await cursor.execute(stmt)
    encode = [dict(row) for row in res.mappings().all()]
    return {"status": 200, "content": json.dumps(encode)}
