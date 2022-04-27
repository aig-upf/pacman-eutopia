from dataclasses import dataclass, field
from team import Team
from typing import List
import json


@dataclass
class TeamsParser:
    """Parse all teams data from a JSON file"""
    teams: List[Team] = field(default_factory=list)

    def __init__(self, json_file: str):
        assert len(json_file) > 5
        assert json_file[-5:] == ".json"
        self.teams = []
        with open(json_file, "r") as f:
            json_teams = json.load(f)
            assert "teams" in json_teams
            for json_team in json_teams["teams"]:
                self.teams.append(Team(json_team=json_team))

    def get_teams(self) -> List[Team]:
        return self.teams

    def get_team(self, team_name) -> Team:
        for team in self.teams:
            if team.get_name() == team_name:
                return team
        return None

    def to_json_obj(self):
        return {"teams": [team.to_json_obj() for team in self.teams]}
