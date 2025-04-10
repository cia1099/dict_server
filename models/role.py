from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    GUEST = "guest"
    CIVVY = "civvy"
    PREMIUM = "premium"


@dataclass
class Character:
    def __init__(self, role: Role, uid: str):
        self.role = role
        self.uid = uid

    @staticmethod
    def from_dict(obj: dict) -> "Character":
        role = obj.get("role", Role.GUEST)
        uid = obj.get("uid", "")
        return Character(role, uid)

    def to_dict(self) -> dict:
        result: dict = {}
        result["role"] = self.role
        result["uid"] = self.uid
        return result


if __name__ == "__main__":
    character = Character.from_dict({"role": "civvy"})
    c2 = Character.from_dict({"role": "premium"})
    print(character.to_dict())
    print(c2.to_dict())
