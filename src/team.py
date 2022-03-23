from dataclasses import dataclass, field
from member import Member
from typing import List


@dataclass
class Team:
    name: str = "default"
    identifier: int = 0
    repository: str = ""
    last_commit: str = ""
    members: List[Member] = field(default_factory=list)

    def __init__(self, json_team: dict) -> None:
        assert all(k in json_team for k in ("name", "id", "repository", "last_commit", "members"))
        self.name = json_team["name"]
        self.identifier = json_team["id"]
        self.repository = json_team["repository"]
        self.last_commit = json_team["last_commit"]
        self.members = []
        for json_member in json_team["members"]:
            self.members.append(Member(json_member=json_member))

    def get_name(self) -> str:
        return self.name

    def get_identifier(self) -> int:
        return self.identifier

    def get_repository(self) -> str:
        return self.repository

    def get_last_commit(self) -> str:
        return self.last_commit

    def get_members(self) -> List[Member]:
        return self.members
