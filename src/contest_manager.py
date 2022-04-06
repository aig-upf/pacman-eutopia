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


class ContestManager:
    contests: dict

    def __init__(self, contests_json_file: str = ""):
        self.contests = {}
        with open(contests_json_file, "r") as f:
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
                    setattr(team, "last_commit", "")
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
        with open(dest_file_name, "w") as f:
            f.write(json.dumps(self.contests[contest_name].to_json_obj()))

    # def get_new_teams(self, contest_name: str) -> List[Team]:
    #     """Return the list of new/updated teams of a given contest"""
    #     assert contest_name in self.contests
    #     return [team for team in self.contests[contest_name].get_teams() if team.get_updated()]

    def get_all_teams(self, contest_name: str) -> List[Team]:
        """Returns all teams of a given contest"""
        assert contest_name in self.contests
        return self.contests[contest_name].get_teams()

    @staticmethod
    def get_local_team_name(contest_name: str, team: Team):
        print(f"{contest_name}_{team.get_name()}/myTeam.py")
        return f"{contest_name}_{team.get_name()}/myTeam.py"

    def submit_match(self, contest_name: str, blue_team: Team, red_team: Team) -> None:
        """Call the two agents Slurm script"""
        print(f"Slurm task: blue={blue_team.get_name()} vs red={red_team.get_name()}")
        # This is for local running
        match_arguments = ["--contest-name", contest_name,
                           "-b", self.get_local_team_name(contest_name, blue_team),
                           "-r", self.get_local_team_name(contest_name, red_team),
                           "--record", "--record-log"]
        print(match_arguments, file=sys.stdout)
        capture.run(match_arguments)
        # sys.stdout.flush()

    def generate_html(self, contest_name: str) -> None:
        web_dir = "www"
        organizer = "UPF"
        web_gen = HtmlGenerator(www_dir=web_dir, contest=contest_name, organizer=organizer)

        # Directories
        scores_dir = f"{web_dir}/contest_{contest_name}/scores"
        replays_dir = f"{web_dir}/contest_{contest_name}/replays"
        logs_dir = f"{web_dir}/contest_{contest_name}/logs"

        # Collect all files in scores directory
        all_files = [f for f in os.listdir(scores_dir) if os.path.isfile(os.path.join(scores_dir, f))]

        # Process each score file - 1 per contest ran
        pattern = re.compile(r'match_([-+0-9T:.]+)\.json')
        for score_filename in all_files:
            match = pattern.match(score_filename)
            if not match:
                continue
            # Extract the id for that particular content from the score file match_{id}.score
            run_id = match.group(1)

            replays_file_name = f'match_{run_id}.replay'
            logs_file_name = f'match_{run_id}.log'

            score_file_full_path = os.path.join(scores_dir, score_filename)
            replays_file_full_path = os.path.join(replays_dir, replays_file_name) if replays_dir else None
            logs_file_full_path = os.path.join(logs_dir, logs_file_name) if logs_dir else None

            web_gen.add_run(run_id=contest_name, scores_dir=score_file_full_path, replays_dir=replays_file_full_path,
                            logs_dir=logs_file_full_path)



def main():
    print(sys.argv)
    # teams_parser = TeamsParser(json_file="teams_upf-ai22.json")
    # print(teams_parser)
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
        contest_manager.generate_html(contest_name=contest_name)


if __name__ == "__main__":
    main()
