#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Generates the HTML output given logs of the past tournament runs.
"""
__author__ = "Sebastian Sardina, Marco Tamassia, Nir Lipovetzky, and Andrew Chester (refactored by Javier Segovia and Sergio Calo)"
__copyright__ = "Copyright 2017-2022"
__license__ = "GPLv3"

#  ----------------------------------------------------------------------------------------------------------------------
# Import standard stuff

import os
import sys
import argparse
import json
import shutil
import zipfile
import logging
import re
import datetime
from bs4 import BeautifulSoup
import glob

# Setup logging configuration
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO,
                    datefmt='%a, %d %b %Y %H:%M:%S')

# ----------------------------------------------------------------------------------------------------------------------
# Load settings either from config.json or from the command line


def load_settings():
    """
    Parses the command line arguments and returns a settings dictionary.
    
    :return: A dictionary containing the settings specified in the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='This script generates the HTML structure given the logs of all the runs of this tournament.'
    )
    parser.add_argument(
        "-o", "--organizer",
        dest='organizer', type=str, required=True,
        help='name of the organizer of the contest'
    )
    parser.add_argument(
        "-d", "--www-dir",
        dest='www_dir', type=str, default="www",
        help='directory containing contests data'
    )
    parser.add_argument(
        "-c", "--contest",
        dest="contest", type=str, default="contest_default",
        help='output directory containing scores, replays, and log files'
    )
    args = parser.parse_args()

    # First get the options from the configuration file if available
    settings = {'organizer': args.organizer, 'www_dir': args.www_dir, 'contest': args.contest}

    logging.info(f'HTML settings: {settings}')

    return settings


# ----------------------------------------------------------------------------------------------------------------------

class HtmlGenerator:
    www_dir: str
    font_source: str
    file_fonts: str
    file_css: str

    def __init__(self, www_dir: str, font_source: str = "."):
        """
        Initializes this generator.

        :param www_dir: the output path
        :param font_source: path to HTML sources
        """
        self.www_dir = www_dir
        self.font_source = font_source
        self.file_fonts = os.path.join(self.font_source, "fonts.zip")
        #self.file_css = os.path.join(self.font_source, "style.css")
        self.file_css = os.path.join('static', "style.css")

        self.error_score = 9999

        # Preparing fonts and style
        os.makedirs(f"{self.www_dir}", exist_ok=True)
        contest_zip_file = zipfile.ZipFile(self.file_fonts)
        contest_zip_file.extractall(self.www_dir)
        #shutil.copy(self.file_css, self.www_dir)
        os.makedirs(os.path.join(self.www_dir, 'static'), exist_ok=True)
        shutil.copy(self.file_css, os.path.join(self.www_dir, 'static'))


    def _close(self):
        pass

    def clean_up(self):
        """
        Empties and removes the output directory
        """
        shutil.rmtree(self.www_dir)

    def add_contest_run(self, run_id: int, organizer: str) -> None:
        """
        (Re)Generates the HTML for the given run and updates the HTML index.
        :return:
        """
        contest_names = self.get_all_contests()

        self._save_run_html(organizer=organizer, run_id=run_id, contest_names=contest_names)
        self._generate_main_html()
        # Load the template HTML content
        with open("template.html", "r") as file:
            template_html_content = file.read()
        # Load the generated HTML content
        with open(f"www/results_{run_id}.html", "r") as file:
            html_generated = file.read()

        # Insert the generated HTML content into the template
        new_html_content = self.insert_html_content(html_generated, template_html_content)

        # Save the new HTML content to a file
        with open(f"www/results_{run_id}_template.html", "w") as file:
            file.write(new_html_content)
    
    #def _save_run_html(self, organizer: str, run_id: int, scores_dir: str, replays_dir: str, logs_dir: str, errors_dir: str):
    def _save_run_html(self, organizer: str, run_id: int, contest_names: list):
        """
        Generates the HTML of a contest run and saves it in www/results_<run_id>/results.html.
        """
        logging.info("Starting the _save_run_html function.")

        random_layouts, fixed_layouts, max_steps = [], [], None
        all_games = []
        all_teams_stats = {}


        for contest_name in contest_names:
            scores_dir = os.path.join(self.www_dir, f"contest_{contest_name}/scores")
            replays_dir = os.path.join(self.www_dir, f"contest_{contest_name}/replays")
            logs_dir = os.path.join(self.www_dir, f"contest_{contest_name}/logs")
            errors_dir = os.path.join(self.www_dir, f"contest_{contest_name}/errors")

            games = []
            teams_stats = {}

            # Collect all files in scores directory
            all_files = [f for f in os.listdir(scores_dir) if os.path.isfile(os.path.join(scores_dir, f))]

            # Process each score file - 1 per contest ran
            pattern = re.compile(r'match_([-+\dT:.]+)\.json')
            for score_filename in all_files:
                match = pattern.match(score_filename)
                if not match:
                    continue

                # Extract the id for that particular content from the score file match_{id}.score
                match_id = match.group(1)

                with open(os.path.join(scores_dir, score_filename), 'r') as f:
                    match_data = json.load(f)
            
                games.extend(match_data['games'])
                for team_name, data in match_data['teams_stats'].items():
                    if team_name in teams_stats:
                        prev_data = teams_stats[team_name]
                        data = [a+b for (a, b) in zip(data, prev_data)]
                    teams_stats[team_name] = data

                if not max_steps:
                    max_steps = match_data['max_steps']
                random_layouts.extend([layout for layout in match_data['layouts'] if layout.startswith('RANDOM') and layout not in random_layouts])
                fixed_layouts.extend([layout for layout in match_data['layouts'] if not layout.startswith('RANDOM') and layout not in fixed_layouts])

            all_games.extend(games)
            print(all_games)
            for team_name, data in teams_stats.items():
                if team_name in all_teams_stats:
                    prev_data = all_teams_stats[team_name]
                    data = [a+b for (a, b) in zip(data, prev_data)]
                all_teams_stats[team_name] = data
        
        logging.info("Number of all games collected: %d", len(all_games))

        num_matches_per_team = (len(all_teams_stats) - 1)
        for team_name, data in all_teams_stats.items():
            data[0] = data[0]//num_matches_per_team
            all_teams_stats[team_name] = data


        # Step 1: Find the top team
        # After populating all_teams_stats, sort it to find the top team
        sorted_team_stats = sorted(list(all_teams_stats.items()), key=lambda v: (v[1][0], v[1][2], v[1][6]), reverse=True)
        top_team = sorted_team_stats[0][0]  # Name of the top team
        logging.info("Top team determined: %s", top_team)

        # Step 2: Find the highest scoring match for the top team
        def find_highest_scoring_match_for_team(games, team_name):
            highest_score = -float('inf')
            best_match = None
            for game in games:
                n1, n2, layout, score, winner, time_taken, match_id = game
                if team_name in (n1, n2) and score > highest_score:
                    highest_score = score
                    best_match = game
            return best_match

        best_match_for_top_team = find_highest_scoring_match_for_team(all_games, top_team)

        date_run = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        run_html = self._generate_html_result(run_id, date_run, organizer, all_games, all_teams_stats, random_layouts,
                                          fixed_layouts, max_steps, scores_dir, replays_dir, logs_dir, errors_dir)

        html_full_path = os.path.join(self.www_dir, f'results_{run_id}.html')
        with open(html_full_path, "w") as f:
            print(run_html, file=f)

        if best_match_for_top_team is not None:
            best_match_id = best_match_for_top_team[-1]
            logging.info("Best match for top team found with ID: %s", best_match_for_top_team[-1])
        else:
            logging.warning("No best match found for the top team.")
            best_match_id = None


        # Find the contest_name associated with the best_match_id
        best_contest_name = None
        for contest_name in contest_names:
            scores_dir = os.path.join(self.www_dir, f"contest_{contest_name}/scores")
            all_files = [f for f in os.listdir(scores_dir) if os.path.isfile(os.path.join(scores_dir, f))]
            if any(str(best_match_id) in filename for filename in all_files):
                best_contest_name = contest_name
                break
        
        logging.info("Contest name associated with best match ID: %s", best_contest_name)
        # Print race ID (for debugging)
        print(best_match_id)   
        # save best_match_id to a file
        logging.info("Writing to best_match_info.txt with data: %s", {'best_match_id': str(best_match_id), 'contest_name': best_contest_name})
        with open('best_match_info.txt', 'w') as file:
            json.dump({'best_match_id': str(best_match_id), 'contest_name': best_contest_name}, file)


    def _generate_main_html(self):
        """
        Generates the index HTML, containing links to the HTML files of all the runs.
        The file is saved in www/index.html.
        """
        # regenerate main html
        main_html = """<html><head><title>Results for PACMAN Capture the Flag Tournaments</title>\n"""
        main_html += """<link rel="stylesheet" type="text/css" href="style.css"/></head>\n"""
        main_html += """<body><h1>Results Pacman Capture the Flag by Date</h1>\n"""
        main_html += f"""<h3>Managed by Universitat Pompeu Fabra for EUTOPIA partners</h3>\n\n"""
        for d in sorted(os.listdir(self.www_dir)):
            if d.endswith('fonts'):
                continue
            if not d.startswith('results'):
                continue
            main_html += f"""<a href="{d}"> {d[:-5]}  </a> <br/>\n"""
        main_html += "\n\n<br/></body></html>"
        with open(os.path.join(self.www_dir, 'index.html'), "w") as f:
            print(main_html, file=f)

    def _generate_ranking(self, team_stats):
        output = """<tr>"""
        output += """<th>Position</th>"""
        output += """<th>Team</th>"""
        output += """<th>Points %</th>"""
        output += """<th>Points</th>"""
        output += """<th>Win</th>"""
        output += """<th>Tie</th>"""
        output += """<th>Lost</th>"""
        output += """<th>TOTAL</th>"""
        output += """<th>FAILED</th>"""
        output += """<th>Score Balance</th>"""
        output += """</tr>\n"""

        # Sort teams by points_pct v[1][0] first, then no. of wins, then score points.
        # example list(team_stats.items() = [('Blue_team', [6, 2, 0, 0, 2, 2]), ('Red_team', [0, 0, 0, 2, 2, -2])]
        sorted_team_stats = sorted(list(team_stats.items()), key=lambda v: (v[1][0], v[1][2], v[1][6]),
                                   reverse=True)
        sorted_team_stats = sorted_team_stats[:5]  # only keep the top 5
        position = 0
        for key, (points_pct, points, wins, draws, losses, errors, sum_score) in sorted_team_stats:
            position += 1
            output += """<tr>"""
            output += f"""<td>{position}</td>"""
            output += f"""<td>{key}</td>"""
            output += f"""<td>{points_pct}%</td>"""
            output += f"""<td>{points}</td>"""
            output += f"""<td>{wins}</td>"""
            output += f"""<td >{draws}</td>"""
            output += f"""<td>{losses}</td>"""
            output += f"""<td>{(wins + draws + losses)}</td>"""
            output += f"""<td >{errors}</td>"""
            output += f"""<td >{sum_score}</td>"""
            output += f"""</tr>\n"""
        output += "</table>"

        return output
        
    def _generate_disqualified_table(self, errors_dir):
        output = "<h2>Disqualified</h2>\n"

        output += f"<h3>Disqualified teams</h3>"


        output += """<table border="1">"""
        output += """<tr>"""
        output += """<th>Team</th>"""
        output += """<th>Log file</th>"""
        output += """</tr>\n"""
        disqualified_teams = os.listdir(errors_dir)
        for team in disqualified_teams:
            output += """<tr>"""

            # Team 1
            output += """<td align="center">"""
            output += f"<b>{team}</b>"
            
            # Logs file
            logs_filename = f"{team}" 
            logs_file_path = os.path.join(errors_dir[4:], team)
            output += "<td align=\"center\">"
            output += f"<a href=\"{logs_file_path}\">{logs_filename}</a>\n"
            output += "</td>"

            output += """</tr>\n"""
        output += "</table>"
        return output

    def _generate_matches_table(self, games, scores_dir, replays_dir, logs_dir):
        output = "<h2>Games</h2>\n"

        g_times = [g_time for (_, _, _, _, _, g_time, _) in games]
        output += f"<h3>No. of games: {len(games)} / "
        output += f"Avg. game length: {str(datetime.timedelta(seconds=round(sum(g_times) / len(g_times), 0)))} / "
        output += f"Max game length: {datetime.timedelta(seconds=max(g_times))}</h3>\n\n"

        score_dir = (scores_dir[4:] if scores_dir.startswith("www/") else scores_dir)
        replays_dir = (replays_dir[4:] if replays_dir.startswith("www/") else replays_dir)
        logs_dir = (logs_dir[4:] if logs_dir.startswith("www/") else logs_dir)


        output += """<table border="1">"""
        output += """<tr>"""
        output += """<th>Team 1</th>"""
        output += """<th>Team 2</th>"""
        output += """<th>Layout</th>"""
        output += """<th>Time</th>"""
        output += """<th>Score</th>"""
        output += """<th>Winner</th>"""
        output += """<th>Score file</th>"""
        output += """<th>Replay file</th>"""
        output += """<th>Log file</th>"""
        output += """</tr>\n"""

        for idx, (n1, n2, layout, score, winner, time_taken, match_id) in enumerate(games):
            # For games beyond the first 10, add a special class to hide them initially
            row_style = "display: none;" if idx >= 10 else ""
            output += f"""<tr class="game-row" style="{row_style}">"""

            # Team 1
            output += """<td align="center">"""
            if winner == n1:
                output += f"<b>{n1}</b>"
            else:
                output += f"{n1}"
            output += """</td>"""

            # Team 2
            output += """<td align="center">"""
            if winner == n2:
                output += f"<b>{n2}</b>"
            else:
                output += f"{n2}"
            output += """</td>"""

            # Layout
            output += f"""<td>{layout}</td>"""

            # Time taken in the game
            output += f"""<td>{datetime.timedelta(seconds=time_taken)}</td>"""

            # Score and Winner
            if score == self.error_score:
                if winner == n1:
                    output += """<td >--</td>"""
                    output += f"""<td><b>ONLY FAILED: {n2}</b></td>"""
                elif winner == n2:
                    output += """<td >--</td>"""
                    output += f"""<td><b>ONLY FAILED: {n1}</b></td>"""
                else:
                    output += """<td >--</td>"""
                    output += """<td><b>FAILED BOTH</b></td>"""
            else:
                output += f"""<td>{score}</td>"""
                output += f"""<td><b>{winner}</b></td>"""

            # Score file
            score_filename = f"match_{match_id}.json"  # ToDo: possible multiple games in a match
            score_file_path = os.path.join(score_dir, score_filename)
            output += "<td align=\"center\">"
            output += f"<a href=\"{score_file_path}\" download=\"{score_filename}\">{score_filename}</a>\n"
            output += "</td>"

            # Replay file
            replay_filename = f"match_{match_id}.replay"  # ToDo: possible multiple games in a match
            replay_file_path = os.path.join(replays_dir, replay_filename)
            output += "<td align=\"center\">"
            output += f"<a href=\"{replay_file_path}\" download=\"{replay_filename}\">{replay_filename}</a>\n"
            output += "</td>"

            # Logs file
            logs_filename = f"match_{match_id}.log"  # ToDo: possible multiple games in a match
            logs_file_path = os.path.join(logs_dir, logs_filename)
            output += "<td align=\"center\">"
            output += f"<a href=\"{logs_file_path}\" download=\"{logs_filename}\">{logs_filename}</a>\n"
            output += "</td>"

            output += """</tr>\n"""
        
        # Add the Show Full Games button here
        output += """</table>"""

        output += '<button id="showNextGamesButton" onclick="showNextGames()">Show Next 10 Games</button>'
        output += '<button id="collapseGamesButton" onclick="collapseGames()" style="display: none;">Collapse</button>'

        return output

    def _generate_html_result(self, run_id, date_run, organizer, games, team_stats, random_layouts, fixed_layouts,
                              max_steps, scores_dir, replays_dir, logs_dir, errors_dir):
        """
        Generates the HTML of the report of the run.
        """
        output = """<html><head><title>Results for the tournament round</title>\n"""
        output += f"""<link rel="stylesheet" type="text/css" href="{self.file_css}"/></head>\n"""
        output += """<body><h1>PACMAN Capture the Flag Tournament</h1>\n"""
        output += f"""<h2>Tournament Organizer: {organizer} </h2>\n"""
        output += f"""<h3>Name of Tournament: {run_id} </h3>\n"""
        output += f"""<h3>Date of Tournament: {date_run} \n</h3>"""

        output += f"<h3>Configuration:\n"
        output += f"<ul><li>Number of teams: {len(team_stats)}</li>"
        output += f"<li>Layouts: {len(fixed_layouts) + len(random_layouts)} " \
                  f"({len(fixed_layouts)} fixed + {len(random_layouts)} random)</li>"
        output += f"<li>Max steps: {max_steps} steps</li>"
        output += f"</ul></h3>\n"

        output += """<br/><br/><table border="1">"""
        if not games:
            output += "No match was run."
        else:
            output += self._generate_ranking(team_stats=team_stats)
            
            output += "\n\n<br/><br/>"
            output += self._generate_disqualified_table(errors_dir=errors_dir)

            output += "\n\n<br/><br/>"
            output += self._generate_matches_table(games=games, scores_dir=scores_dir, replays_dir=replays_dir,
                                                   logs_dir=logs_dir)

        output += "\n\n</table>"

        # Add JavaScript code to handle the "Show Next 10 Games" and "Collapse" button clicks.
        output += '''
        <script>
        var currentShownGames = 10;

        function showNextGames() {
            var rows = document.getElementsByClassName("game-row");
            var endIndex = Math.min(currentShownGames + 10, rows.length);
            for (var i = currentShownGames; i < endIndex; i++) {
                rows[i].style.display = "";
            }
            currentShownGames = endIndex;
            if (currentShownGames >= rows.length) {
                document.getElementById("showNextGamesButton").style.display = "none";
                document.getElementById("collapseGamesButton").style.display = "";
            }
        }

        function collapseGames() {
            var rows = document.getElementsByClassName("game-row");
            for (var i = 10; i < rows.length; i++) {
                rows[i].style.display = "none";
            }
            currentShownGames = 10;
            document.getElementById("showNextGamesButton").style.display = "";
            document.getElementById("collapseGamesButton").style.display = "none";
        }
        </script>
        '''

        video_container = '''
        <div id="video-player-container">
        <h2>Top Score Match Video</h2>
        <button id="toggle-video-btn">Hide Video</button>
        <video id="videoPlayer" controls>
        <source src="/videos/best_match.mp4" type="video/mp4">
        Your browser does not support the video tag.
        </video>
        </div>
        '''

        toggle_video_script = '''
        <script>
        document.getElementById("toggle-video-btn").addEventListener("click", function() {
            var video = document.getElementById("videoPlayer");
            if (video.style.display !== "none") {
                video.style.display = "none";
                this.innerHTML = "Show Video";
            } else {
                video.style.display = "block";
                this.innerHTML = "Hide Video";
            }
        });
        </script>
        '''

        output += video_container
        output += toggle_video_script

        output += "</body></html>"

        return output

    def insert_html_content(self, html_generated, template_html_content):
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(template_html_content, 'html.parser')

        # Find the 'information' tag
        info_tag = soup.find('h2', string='Information')

        # Create a new tag with the generated content
        new_tag = soup.new_tag("div")
        new_tag.append(BeautifulSoup(html_generated, 'html.parser')) 

        # Insert the new tag after the 'information' tag
        if info_tag:
            info_tag.insert_after(new_tag)

        # Return the modified HTML content
        return str(soup)
    

    def get_all_contests(self):
        """
        Returns a list of all contest names in the www directory, excluding 'contest_default'.
        """
        dir_path = os.path.join(self.www_dir, 'contest_')
        contest_dirs = glob.glob(f"{dir_path}*")
        contest_names = [f.replace(dir_path, '') for f in contest_dirs if f != 'contest_default']
        logging.info(contest_names)  # Recorded to log file
        return contest_names


def main():
    """
    Main function of the script. 
    """
    settings = load_settings()
    html_generator = HtmlGenerator(settings['www_dir'])
    html_generator.add_contest_run(run_id=0, organizer=settings['organizer'])


    

if __name__ == '__main__':
    main()