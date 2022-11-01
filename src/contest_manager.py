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
import importlib.util
import importlib.machinery
import pathlib
import argparse

#-------------------------------------
def load_settings():
    parser = argparse.ArgumentParser(
            description='This script generates the HTML structure given the logs of all the runs of this tournament.'
        )
    parser.add_argument(
        "-s", "--step",
        dest='step', type=str, required=True,
        help='name of the step'
        )
    parser.add_argument(
        "-t", "--task",
        dest='task', type=str, required=False,
        help='task number. Argument used when parallelizing games in the cluster'
        )

   
    args = parser.parse_args()

    # First get the options from the configuration file if available
    settings = {'step': args.step, 'task': args.task}

    logging.info(f'Contest manager settings: {settings}')

    return settings
#-----------------    


class ContestManager:
    contests: dict
    www_dir: str

    def __init__(self, contests_json_file: str = ""):
        self.contests = {}
        self.www_dir = "www"
        self.matches = {}
        self.match_counter = 1
	
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
        if not os.path.exists('slurm-outputs'):
                    os.makedirs('slurm-outputs')
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
                error_dir = os.path.join(self.www_dir, f"contest_{contest_name}/errors")
                if not os.path.exists(error_dir):
                    os.makedirs(error_dir)
                error = self.check_syntax_error(repo_local_dir, contest_name)
                loading_error = self.check_loading_errors(False, repo_local_dir, contest_name)

                if error == True:
                    setattr(team, "syntax_error", True)
                        
                if loading_error == [None,None]:
                    setattr(team, "loading_error", True)

                    

            """Clean up old matches of updated teams, at the end there 
            must be n*(n-1)/2 matches where n is the number of teams"""
            self.clean_up_old_matches(contest_name, contest_data_teams)

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

    def dump_contest_teams_json_file(self, contest_name: str, dest_file_name: str) -> None:
        assert contest_name in self.contests
        with open(dest_file_name, "w") as f:
            f.write(json.dumps(self.contests[contest_name]["teams"].to_json_obj(), sort_keys=True, indent=4))

    def dump_contests_json_file(self):
        data = []
        for contest_name in self.contests:
            data.append({"name": contest_name,
                         "organizer": self.contests[contest_name]["organizer"],
                         "last-match-id": int(self.contests[contest_name]["last_match_id"])})
        with open("contests.json", "w") as f:
            f.write(json.dumps({"contests": data}, sort_keys=True, indent=4))
            
    def dump_matches_json_file(self):
        with open("matches.json", "w") as f:
            json.dump(self.matches, f)
    
    def check_syntax_error(self,filename, contest_name):
        source = open(filename+'/myTeam.py', 'r').read() + '\n'
        try:
            compile(source, filename, 'exec')
        except Exception as Argument:
            with open(f"www/contest_{contest_name}/errors/{filename}.log", 'w') as file:
                file.write(str(Argument))
                file.close()
            return True
    
    def check_loading_errors(self, isRed, filename, contest_name):
        try:
            self.load_agents(isRed, filename+'/myTeam.py')
        except Exception as Argument:
            with open(f"www/contest_{contest_name}/errors/{filename}.log", 'w') as file:
                file.write(str(Argument))
                file.close()
            return True
    # def get_new_teams(self, contest_name: str) -> List[Team]:
    #     """Return the list of new/updated teams of a given contest"""
    #     assert contest_name in self.contests
    #     return [team for team in self.contests[contest_name].get_teams() if team.get_updated()]


    
    def load_agents(self, is_red, agent_file, cmd_line_args=[]):
            if not agent_file.endswith(".py"):
                agent_file += ".py"

            module_name = pathlib.Path(agent_file).stem
            agent_file = os.path.abspath(agent_file)

        # just in case other files not in the distribution are loaded
            sys.path.append(os.path.split(agent_file)[0])


        # SS: new way of loading Python modules - Python 3.4+
            loader = importlib.machinery.SourceFileLoader(module_name, agent_file)
            spec = importlib.util.spec_from_loader(module_name, loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)  # will be added to sys.modules dict


            create_team_func = getattr(module, 'create_team')


            return 'All good'
    
    
    
    def get_all_teams(self, contest_name: str) -> List[Team]:
        """Returns all teams of a given contest"""
        assert contest_name in self.contests
        return self.contests[contest_name]["teams"].get_teams()

    @staticmethod
    def get_local_team_name(contest_name: str, team: Team):
        logging.info(f"Local team name at {contest_name}_{team.get_name()}/myTeam.py")
        return f"{contest_name}_{team.get_name()}/myTeam.py"

    def clean_up_old_matches(self, contest_name: str, contest_data_teams: TeamsParser) -> None:
        scores_dir = os.path.join(self.www_dir, f"contest_{contest_name}/scores")
        replays_dir = os.path.join(self.www_dir, f"contest_{contest_name}/replays")
        logs_dir = os.path.join(self.www_dir, f"contest_{contest_name}/logs")

        # No need to clean up matches if folders have not been created yet
        if not os.path.isdir(scores_dir) or not os.path.isdir(replays_dir) or not os.path.isdir(logs_dir):
            return

        # Collect all files in scores directory
        all_score_files = [f for f in os.listdir(scores_dir) if os.path.isfile(os.path.join(scores_dir, f))]

        pattern = re.compile(r'match_([-+\dT:.]+)\.json')

        for score_filename in all_score_files:
            match = pattern.match(score_filename)
            if not match:
                continue

            # Extract the id for that particular content from the score file match_{id}.score
            match_id = match.group(1)

            with open(os.path.join(scores_dir, score_filename), 'r') as f:
                match_data = json.load(f)
                for team_name, _ in match_data["teams_stats"].items():
                    # Delete an old match if at least one team has been updated
                    if contest_data_teams.get_team(team_name).get_updated():
                        os.remove(os.path.join(scores_dir, score_filename))
                        replay_filename = score_filename[:-5]+".replay"  # remove .json and add .replay
                        os.remove(os.path.join(replays_dir, replay_filename))
                        log_filename = score_filename[:-5]+".log"  # remove .json and add .log
                        os.remove(os.path.join(logs_dir, log_filename))
                        logging.info(f"Deleted match #{match_id}, files: {score_filename}, {replay_filename}, "
                                     f"{log_filename}")
                        break
                        

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
                           "--record", "--record-log", "-Q", "-c"]  # record log and score in super quiet mode

        logging.info(f"Match arguments: {match_arguments}")
        #capture.run(match_arguments)
        self.contests[contest_name]["last_match_id"] = last_match_id
        self.matches[self.match_counter] = match_arguments
        self.match_counter += 1
        print(self.matches)
        	
        
        	

    def generate_html(self) -> None:
        web_gen = HtmlGenerator(www_dir=self.www_dir)

        for idx, contest_name in enumerate(self.contests):
            web_gen.add_contest_run(run_id=idx,
                                    contest_name=contest_name,
                                    organizer=self.contests[contest_name]["organizer"])


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Command arguments: {sys.argv}")
    contest_manager = ContestManager(contests_json_file="contests.json")
    settings = load_settings()

    if settings['step'] == 'prepare_matches':
        print('Step 1...')
        for contest_name in contest_manager.get_contest_names():
            all_teams = contest_manager.get_all_teams(contest_name=contest_name)
            for t1_idx in range(0, len(all_teams)):
		    
                for t2_idx in range(t1_idx+1, len(all_teams)):
    	        # Allow only new vs all (not old vs old)
                        if not all_teams[t1_idx].get_updated() and not all_teams[t2_idx].get_updated():
                            continue
                        new_match = [all_teams[t1_idx], all_teams[t2_idx]]
                        random.shuffle(new_match)  # randomize blue vs red
                        if new_match[0].get_syntax_error() == False and new_match[1].get_syntax_error() == False: 
                            if new_match[0].get_loading_error() == False and new_match[1].get_loading_error() == False: 
                                contest_manager.submit_match(contest_name=contest_name, blue_team=new_match[0], red_team=new_match[1])

            contest_manager.dump_contest_teams_json_file(contest_name=contest_name, dest_file_name=f"teams_{contest_name}.json")
        contest_manager.dump_contests_json_file()
        contest_manager.dump_matches_json_file()
        with open("matches.json","r") as f:
                matches_json = f.read()
                matches_json = json.loads(matches_json)

        with open('slurm-array-template.sh', 'r') as template:
            filedata = template.read()

        filedata = filedata.replace('$1', str(len(matches_json)))
        with open('slurm-array.sh', 'w') as file:
            file.write(filedata)


    if settings['step']  == 'run_matches':	    
        with open("matches.json","r") as f:
            matches = f.read()
            matches = json.loads(matches)
            capture.run(matches[settings['task'] ])
        
    if settings['step']  == 'html':	    
        contest_manager.generate_html()




if __name__ == "__main__":
    main()
