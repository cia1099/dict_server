from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import StrEnum


class Role(StrEnum):
    GUEST = "guest"
    CIVVY = "civvy"
    PREMIUM = "premium"


@dataclass
class CharacterBase(ABC):
    def __init__(self, role: Role, uid: str):
        self.role = role
        self.uid = uid

    @abstractmethod
    def from_dict(self):
        pass

    def to_dict(self) -> dict:
        result: dict = {}
        result["role"] = self.role
        result["uid"] = self.uid
        return result
