from fastapi import APIRouter, Depends, Request, Response, HTTPException, Header
from services.auth import premium_auth

router = APIRouter()


@router.post("/supabase/database")
async def supabase_operator(req: Request):
    body = await req.body()
    query = body.decode("utf-8")
    return "Hello %s" % query
