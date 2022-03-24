from teams_parser import TeamsParser
import json
from git import Repo
import os


class ContestManager:
    contests: dict

    def __init__(self, json_file: str = ""):
        self.contests = {}
        with open(json_file, "r") as f:
            json_contests = json.load(f)
            for contest_name in json_contests:
                self.contests[contest_name] = TeamsParser(json_file="teams_" + contest_name + ".json")
        # print(self.contest_teams)
        for contest_name in self.contests:
            contest_data = self.contests[contest_name]
            for team in contest_data.get_teams():
                repo_local_dir = self.get_repo_dir(contest_name, team)
                print(repo_local_dir, self.repo_exists(repo_local_dir))
                if not self.repo_exists(repo_local_dir):
                    repo = self.clone_repo(url=team.get_repository(), dest_folder=repo_local_dir)
                else:
                    repo = self.get_cloned_repo(dest_folder=repo_local_dir)
                print(self.get_repo_commit(repo=repo))
                if self.is_repo_updated(repo=repo, last_commit=team.get_last_commit()):
                    print("The repository has been updated!")
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
        # json_str = self.contests[contest_name].to_json_str()
        print(self.contests[contest_name])
        json_str = json.dumps(self.contests[contest_name].to_json_obj())
        print(json_str)


def main():
    # teams_parser = TeamsParser(json_file="teams_upf-ai22.json")
    # print(teams_parser)
    contest_manager = ContestManager(json_file="contests.json")
    for contest_name in contest_manager.get_contest_names():
        contest_manager.dump_json_file(contest_name=contest_name, dest_file_name="")


if __name__ == "__main__":
    main()
