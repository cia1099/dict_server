if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

import datetime
import math
from models.role import CharacterBase, Role
from firebase_admin import auth
from fastapi import HTTPException


class Character(CharacterBase):
    def __init__(self, role: Role, uid: str):
        super().__init__(role, uid)

    @staticmethod
    def from_dict(obj: dict) -> "Character":
        role = obj.get("role", Role.GUEST)
        uid = obj.get("uid", "")
        return Character(role, uid)

    def deposit(self) -> float:
        claims = auth.get_user(self.uid).custom_claims or {}
        return claims.get("token", 0.0) + claims.get("gas", 0.0)

    def raise_withdraw(self, cost: float = 1e-3):
        if self.deposit() < cost:
            raise HTTPException(402, "You don't have enough tokens")

    def __add__(self, other: float) -> float:
        # if not isinstance(other, float):
        #     return NotImplemented
        claims = auth.get_user(self.uid).custom_claims or {}
        token = claims.get("token", 0.0) + other
        claims.update({"token": max(math.floor(token * 1e3) / 1e3, 0.0)})
        auth.set_custom_user_claims(self.uid, claims)
        return token

    def __sub__(self, other: float) -> float:
        # if not isinstance(other, float):
        #     return NotImplemented
        claims = auth.get_user(self.uid).custom_claims or {}
        if self.role == Role.PREMIUM:
            claims = self._check_premium(claims)

        gas = claims.get("gas", 0.0) - other
        token = claims.get("token", 0.0) + gas if gas < 1e-6 else 0.0
        claims.update(
            {
                "token": max(math.floor(token * 1e3) / 1e3, 0.0),
                "gas": max(math.floor(gas * 1e3) / 1e3, 0.0),
            }
        )
        auth.set_custom_user_claims(self.uid, claims)
        return claims.get("token", 0.0) + claims.get("gas", 0.0)

    def _check_premium(self, claims: dict) -> dict:
        end = claims.get("end", 0)
        now = datetime.datetime.now()
        if end - int(now.timestamp()) < 0:
            claims.pop("gas", None)
            claims.pop("start", None)
            claims.pop("end", None)
            claims.update({"role": Role.CIVVY})
            # self.role = Role.CIVVY
        return claims

    def register_premium(self, days: int = 30):
        if self.role != Role.CIVVY:
            return False
        start = datetime.datetime.now()
        end = start + datetime.timedelta(days=days)
        claims = auth.get_user(self.uid).custom_claims or {}
        claims.update(
            {
                "role": Role.PREMIUM,
                "gas": 200.0,
                "start": int(start.timestamp()),
                "end": int(end.timestamp()),
            }
        )
        auth.set_custom_user_claims(self.uid, claims)
        return True


if __name__ == "__main__":
    print(math.pow(10, 1 - 2))
