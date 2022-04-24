import random

from teams_parser import TeamsParser
import json
from git import Repo
import os
from team import Team
from typing import List
from contest import capture
import sys
from html_generator import HtmlGenerator
import re
import logging


class ContestManager:
    contests: dict

    def __init__(self, contests_json_file: str = ""):
        self.contests = {}
        with open(contests_json_file, "r") as f:
            json_contests = json.load(f)
            for contest_data_teams in json_contests["contests"]:
                contest_name = contest_data_teams['name']
                self.contests[contest_name] = {
                    "teams": TeamsParser(json_file="teams_" + contest_name + ".json"),
                    "organizer": contest_data_teams['organizer'],
                    "last_match_id": int(contest_data_teams['last-match-id'])
                }
        logging.info(self.contests)
        for contest_name in self.contests:
            contest_data_teams = self.contests[contest_name]["teams"]
            for team in contest_data_teams.get_teams():
                repo_local_dir = self.get_repo_dir(contest_name, team)
                logging.info(f"Repository local dir: {repo_local_dir} (exists? {self.repo_exists(repo_local_dir)})")
                if not self.repo_exists(repo_local_dir):
                    setattr(team, "last_commit", "")
                    repo = self.clone_repo(url=team.get_repository(), dest_folder=repo_local_dir)
                else:
                    repo = self.get_cloned_repo(dest_folder=repo_local_dir)
                logging.info(f"Repository commit: {self.get_repo_commit(repo=repo)}")
                if self.is_repo_updated(repo=repo, last_commit=team.get_last_commit()):
                    logging.info("The repository has been updated!")
                    setattr(team, "last_commit", self.get_repo_commit(repo=repo))
                    setattr(team, "updated", True)
                    assert team.get_last_commit() == self.get_repo_commit(repo=repo)
                else:
                    setattr(team, "updated", False)

    @staticmethod
    def get_repo_dir(contest_name, team):
        """Generate the repository local directory"""
        return contest_name + "_" + team.get_name()

    @staticmethod
    def repo_exists(repo_dir):
        """Check if the repository already exists locally"""
        return os.path.isdir(repo_dir)  # optional +"/.git"

    @staticmethod
    def clone_repo(url: str, dest_folder: str) -> Repo:
        """Method to easily clone a public repository"""
        return Repo.clone_from(url, dest_folder)  # optional argument branch='main'

    @staticmethod
    def get_cloned_repo(dest_folder: str) -> Repo:
        """Method to get an already cloned repository"""
        return Repo(dest_folder)

    @staticmethod
    def get_repo_commit(repo: Repo) -> str:
        return str(repo.head.reference.commit)

    def is_repo_updated(self, repo: Repo, last_commit: str) -> bool:
        return self.get_repo_commit(repo=repo) != last_commit

    def get_contest_names(self):
        return [contest_name for contest_name in self.contests]

    def dump_json_file(self, contest_name: str, dest_file_name: str) -> None:
        assert contest_name in self.contests
        with open(dest_file_name, "w") as f:
            f.write(json.dumps(self.contests[contest_name]["teams"].to_json_obj()))

    # def get_new_teams(self, contest_name: str) -> List[Team]:
    #     """Return the list of new/updated teams of a given contest"""
    #     assert contest_name in self.contests
    #     return [team for team in self.contests[contest_name].get_teams() if team.get_updated()]

    def get_all_teams(self, contest_name: str) -> List[Team]:
        """Returns all teams of a given contest"""
        assert contest_name in self.contests
        return self.contests[contest_name]["teams"].get_teams()

    @staticmethod
    def get_local_team_name(contest_name: str, team: Team):
        logging.info(f"Local team name at {contest_name}_{team.get_name()}/myTeam.py")
        return f"{contest_name}_{team.get_name()}/myTeam.py"

    def submit_match(self, contest_name: str, blue_team: Team, red_team: Team) -> None:
        """Call the two agents Slurm script"""
        logging.info(f"Slurm task: blue={blue_team.get_name()} vs red={red_team.get_name()}")
        last_match_id = self.contests[contest_name]["last_match_id"] + 1
        # This is for local running
        match_arguments = ["--contest-name", contest_name,
                           "-b", self.get_local_team_name(contest_name, blue_team),
                           "--blue-name", blue_team.get_name(),
                           "-r", self.get_local_team_name(contest_name, red_team),
                           "--red-name", red_team.get_name(),
                           "-m", str(last_match_id),  # set the match id to save log and score
                           "--record", "--record-log", "-Q"]  # record log and score in super quiet mode
        logging.info(f"Match arguments: {match_arguments}")
        capture.run(match_arguments)
        self.contests[contest_name]["last_match_id"] = last_match_id

    def generate_html(self) -> None:
        web_gen = HtmlGenerator(www_dir="www")

        for idx, contest_name in enumerate(self.contests):
            web_gen.add_contest_run(run_id=idx,
                                    contest_name=contest_name,
                                    organizer=self.contests[contest_name]["organizer"])


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Command arguments: {sys.argv}")
    contest_manager = ContestManager(contests_json_file="contests.json")
    for contest_name in contest_manager.get_contest_names():
        all_teams = contest_manager.get_all_teams(contest_name=contest_name)
        for t1_idx in range(0, len(all_teams)):
            for t2_idx in range(t1_idx+1, len(all_teams)):
                # Allow only new vs all (not old vs old)
                if not all_teams[t1_idx].get_updated() and not all_teams[t2_idx].get_updated():
                    continue
                new_match = [all_teams[t1_idx], all_teams[t2_idx]]
                random.shuffle(new_match)  # randomize blue vs red
                contest_manager.submit_match(contest_name=contest_name, blue_team=new_match[0], red_team=new_match[1])

        contest_manager.dump_json_file(contest_name=contest_name, dest_file_name=f"teams_{contest_name}.json")
    contest_manager.generate_html()


if __name__ == "__main__":
    main()
