from pydantic import BaseModel


class ReportIn(BaseModel):
    word_id: int
    user_id: str = "oxfordstu"
    word: str
    issue: str
