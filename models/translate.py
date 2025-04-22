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
            case "zh-CN":
                return Translation.zh_CN
            case "zh-TW":
                return Translation.zh_TW
            case "ja-JP":
                return Translation.ja_JP
            case "ko-KR":
                return Translation.ko_KR
            case "vi-VN":
                return Translation.vi_VN
            case "ar-SA":
                return Translation.ar_SA
            case "th-TH":
                return Translation.th_TH
            case _:
                return Translation.zh_CN
