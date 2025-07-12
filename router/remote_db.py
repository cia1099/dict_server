import asyncio
from datetime import datetime
import json
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from models.pull import PullIn
from models.report import ReportIn
from services.auth import Character
from client.client_schema import ReportIssue, SharedApp, parse_condition
from database import remote_engine, metadata
import sqlalchemy as sql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from services.auth import premium_auth, member_auth

router = APIRouter()
earned_token = 2.0


@router.post("/supabase/write")
async def supabase_write(req: Request, c=Depends(premium_auth)):
    body = await req.body()
    query = body.decode("utf-8")
    policy = f"SET LOCAL request.jwt.claim.sub = '{c.uid}'"
    async with remote_engine.connect() as cursor:
        try:
            await cursor.execute(sql.text(policy))
            await cursor.execute(sql.text(query))
            await cursor.commit()
        except:
            await cursor.rollback()
            return {"status": 500, "content": "Failed to write data to Supabase"}
    return {"status": 200, "content": "Successfully write to Supabase"}


@router.delete("/supabase/erase")
async def supabase_delete(req: Request, c=Depends(member_auth)):
    body = await req.body()
    query = body.decode("utf-8")
    policy = f"SET LOCAL request.jwt.claim.sub = '{c.uid}'"
    async with remote_engine.connect() as cursor:
        try:
            await cursor.execute(sql.text(policy))
            await cursor.execute(sql.text(query))
            await cursor.commit()
        except:
            await cursor.rollback()
            return {"status": 500, "content": "Failed to erase data in Supabase"}
    return {"status": 200, "content": "Successfully erase Supabase"}


# User can only see their own rows
# user_id = auth.uid()::text


@router.post("/supabase/pull")
async def supabase_pull(
    pull: PullIn, page: int = 0, max_length: int = 200, c=Depends(member_auth)
):
    table = metadata.tables.get(pull.tablename)
    if table is None:
        raise HTTPException(400, "No '%s' table in database" % pull.tablename)
    condition = parse_condition(**pull.model_dump())
    stmt = (
        sql.select(*(sql.column(c) for c in table.c.keys() if c != "user_id"))
        .where(condition)
        .limit(max_length)
        .offset(max_length * page)
    )
    async with remote_engine.connect() as cursor:
        await cursor.execute(sql.text(f"SET LOCAL request.jwt.claim.sub = '{c.uid}'"))
        res = await cursor.execute(stmt)
    encode = [dict(row) for row in res.mappings().all()]
    return {"status": 200, "content": json.dumps(encode)}


@router.post("/report/issue")
async def report_issue(report: ReportIn, character: Character = Depends(member_auth)):
    report.user_id = character.uid
    await record_issue(report)
    return {
        "status": 200,
        "content": "We've received your report. We'll resolve this ASAP.",
    }


@router.put("/share/to/app")
async def share2app(req: Request, character: Character = Depends(member_auth)):
    body = await req.body()
    app_id = str(body, "utf-8")
    now = datetime.now()
    date = datetime(year=now.year, month=now.month, day=now.day)
    data = {"date": int(date.timestamp()), "user_id": character.uid, "app_id": app_id}
    stmt = pg_insert(SharedApp).values(data)
    ins_cte = stmt.on_conflict_do_nothing().returning(1).cte("ins")
    stmt = sql.select(
        sql.exists(sql.select("*").select_from(ins_cte)).label("inserted")
    )
    async with remote_engine.connect() as cursor:
        await cursor.execute(
            sql.text(f"SET LOCAL request.jwt.claim.sub = '{character.uid}'")
        )
        shared = (await cursor.execute(stmt)).scalar() or False
        if shared:
            await cursor.commit()
            count_stmt = sql_exp_count_appid(character.uid)
            shares = (await cursor.execute(count_stmt)).scalar() or 0
            _ = character + earned_token / (1 + shares)

    if not shared:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already shared today")
    return {"status": 200, "content": "Successfully shared"}


@router.get("/today/shares")
async def today_shared(character: Character = Depends(member_auth)):
    stmt = sql_exp_count_appid(character.uid)
    async with remote_engine.connect() as cursor:
        shares = (await cursor.execute(stmt)).scalar() or 0
    msg = (
        f"Get {earned_token:.1f} tokens for sharing"
        if shares == 0
        else "Share to other app for more tokens"
    )
    return {"status": 200, "content": msg}


async def record_issue(report: ReportIn):
    stmt = pg_insert(ReportIssue).values(report.model_dump())
    stmt = stmt.on_conflict_do_update(
        index_elements=["word_id", "user_id"],
        set_={
            "issue": stmt.excluded.issue,
            "time": stmt.excluded.time,
        },
    )
    async with remote_engine.connect() as cursor:
        try:
            await cursor.execute(
                sql.text(f"SET LOCAL request.jwt.claim.sub = '{report.user_id}'")
            )
            await cursor.execute(stmt)
            await cursor.commit()
        except:
            await cursor.rollback()
            raise HTTPException(500, "Oops~ there is something wrong")


async def clear_user(uid: str):
    tables = [
        "acquaintances",
        "collections",
        "punch_days",
        "shared_apps",
        "report_issues",
    ]
    stmts = (
        sql.text(f"DELETE FROM {table} WHERE user_id=:user_id") for table in tables
    )
    async with remote_engine.connect() as cursor:
        async with cursor.begin():
            for stmt in stmts:
                await cursor.execute(stmt, {"user_id": uid})
    return uid


def sql_exp_count_appid(uid: str):
    now = datetime.now()
    date = datetime(year=now.year, month=now.month, day=now.day)
    today = int(date.timestamp())
    stmt = sql.select(sql.func.count(SharedApp.app_id)).where(
        (SharedApp.date == today) & (SharedApp.user_id == uid)
    )
    return stmt
