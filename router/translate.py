from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
import sqlalchemy as sql
from models.translate import TranslateIn
from oxfordstu.oxfordstu_schema import Translation

from database import cursor
from services.auth import premium_auth

router = APIRouter()


@router.post("/definition/translation")
async def definition_translation(body: TranslateIn, _=Depends(premium_auth)):
    if not body.definition_id or not body.lang:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "null value in definition_id or lang"
        )
    stmt = sql.select(body.locate()).where(
        Translation.definition_id == body.definition_id
    )
    res = await cursor.execute(stmt)
    tr = res.scalar_one_or_none() or ""
    return {"status": 200, "content": tr}
