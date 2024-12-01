from pydantic import BaseModel


class ChatIn(BaseModel):
    text: str
    is_help: bool = False
