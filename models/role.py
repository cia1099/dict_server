from dataclasses import dataclass


@dataclass
class Role:
    role: str
    token: int

    @staticmethod
    def from_dict(obj: dict) -> "Role":
        role = obj.get("role", "guest")
        token = obj.get("token", 0)
        return Role(role, token)

    def to_dict(self) -> dict:
        result: dict = {}
        result["role"] = self.role
        result["token"] = self.token
        return result


if __name__ == "__main__":
    role = Role.from_dict({})
    print(role.to_dict())
