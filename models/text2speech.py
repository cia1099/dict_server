from pydantic import BaseModel


class Text2SpeechIn(BaseModel):
    text: str
    lang: str
    gender: str | None = None
    name: str | None = None
