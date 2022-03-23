from dataclasses import dataclass


@dataclass
class Member:
    name: str = "default"
    identifier: str = "default"

    def __init__(self, json_member: dict):
        assert all(k in json_member for k in ("name", "id"))
        self.name = json_member["name"]
        self.identifier = json_member["id"]

    def get_name(self):
        return self.name

    def get_identifier(self):
        return self.identifier
