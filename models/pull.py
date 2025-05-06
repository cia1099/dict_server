from pydantic import BaseModel


class PullIn(BaseModel):
    user_id: str
    tablename: str
    exclude_ids: list[int] = []

    # def to_dict(self) -> dict:
    #     result: dict = {}
    #     result["user_id"] = self.user_id
    #     result["tablename"] = self.tablename
    #     result["exclude_ids"] = self.exclude_ids
    #     return result
