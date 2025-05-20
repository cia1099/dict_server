from pydantic import BaseModel
from oxfordstu.oxfordstu_schema import Translation
from sqlalchemy import Column


class TranslateIn(BaseModel):
    text: str | None = None
    definition_id: int | None = None
    lang: str | None = None

    def locate(self) -> Column[str]:
        return TranslateIn.column(self.lang)

    @staticmethod
    def column(lang: str | None):
        match lang:
            case "zh-CN":
                return Translation.zh_CN
            case "zh-TW":
                return Translation.zh_TW
            case "ja-JP" | "ja":
                return Translation.ja_JP
            case "ko-KR" | "ko":
                return Translation.ko_KR
            case "vi-VN" | "vi":
                return Translation.vi_VN
            case "ar-SA" | "ar":
                return Translation.ar_SA
            case "th-TH" | "th":
                return Translation.th_TH
            case _:
                return Translation.en_US
