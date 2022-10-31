from dataclasses import dataclass, field
from member import Member
from typing import List


@dataclass
class Team:
    name: str = "default"
    identifier: int = 0
    repository: str = ""
    last_commit: str = ""
    updated: bool = False
    syntax_error: bool = False
    loading_error: bool = False
    members: List[Member] = field(default_factory=list)

    def __init__(self, json_team: dict) -> None:
        assert all(k in json_team for k in ("name", "id", "repository", "last_commit", "updated", "members"))
        self.name = json_team["name"]
        self.identifier = json_team["id"]
        self.repository = json_team["repository"]
        self.last_commit = json_team["last_commit"]
        self.updated = json_team["updated"]
        self.members = []
        self.syntax_error = json_team["syntax_error"]
        self.loading_error = json_team["loading_error"]
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

    def get_updated(self) -> bool:
        return self.updated
        
    def get_syntax_error(self) -> bool:
        return self.syntax_error
        
    def get_loading_error(self) -> bool:
        return self.loading_error

    def get_members(self) -> List[Member]:
        return self.members

    def to_json_obj(self):
        return {
            "name": self.name,
            "id": self.identifier,
            "repository": self.repository,
            "last_commit": self.last_commit,
            "updated": self.updated,
            "syntax_error": self.syntax_error,
            "loading_error": self.loading_error,
            "members": [member.to_json_obj() for member in self.members]
        }
