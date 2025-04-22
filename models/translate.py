from pydantic import BaseModel
from oxfordstu.oxfordstu_schema import Translation
from sqlalchemy import Column


class TranslateIn(BaseModel):
    text: str | None = None
    definition_id: int | None = None
    lang: str

    def locate(self) -> Column[str]:
        return TranslateIn.column(self.lang)

    @staticmethod
    def column(lang: str | None):
        match lang:
            case "zh_CN":
                return Translation.zh_CN
            case "zh_TW":
                return Translation.zh_TW
            case "ja_JP":
                return Translation.ja_JP
            case "ko_KR":
                return Translation.ko_KR
            case "vi_VN":
                return Translation.vi_VN
            case "ar_SA":
                return Translation.ar_SA
            case "th_TH":
                return Translation.th_TH
            case _:
                return Translation.zh_CN
