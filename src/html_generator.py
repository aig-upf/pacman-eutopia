#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Generates the HTML output given logs of the past tournament runs.
"""
__author__ = "Sebastian Sardina, Marco Tamassia, Nir Lipovetzky, and Andrew Chester (refactored by Javier Segovia)"
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
from pytz import timezone

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO,
                    datefmt='%a, %d %b %Y %H:%M:%S')

# ----------------------------------------------------------------------------------------------------------------------
# Load settings either from config.json or from the command line

def load_settings():
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
        self.file_css = os.path.join(self.font_source, "style.css")
        self.error_score = 9999

        # Preparing fonts and style
        os.makedirs(f"{self.www_dir}", exist_ok=True)
        contest_zip_file = zipfile.ZipFile(self.file_fonts)
        contest_zip_file.extractall(self.www_dir)
        shutil.copy(self.file_css, self.www_dir)

    def _close(self):
        pass

    def clean_up(self):
        """
        Empties and removes the output directory
        """
        shutil.rmtree(self.www_dir)

    def add_contest_run(self, run_id: int, contest_name: str, organizer: str) -> None:
        """
        (Re)Generates the HTML for the given run and updates the HTML index.
        :return:
        """
        scores_dir = os.path.join(self.www_dir, f"contest_{contest_name}/scores")
        replays_dir = os.path.join(self.www_dir, f"contest_{contest_name}/replays")
        logs_dir = os.path.join(self.www_dir, f"contest_{contest_name}/logs")

        self._save_run_html(organizer=organizer, run_id=run_id, scores_dir=scores_dir, replays_dir=replays_dir,
                            logs_dir=logs_dir)
        self._generate_main_html()

    def _save_run_html(self, organizer: str, run_id: int, scores_dir: str, replays_dir: str, logs_dir: str):
        """
        Generates the HTML of a contest run and saves it in www/results_<run_id>/results.html.

        The URLs passed should be either:
         - HTTP URLs, in which case the scores file is downloaded to generate the HTML
         - local relative paths, which are assumed to start from self.www_dir

        No checks are done, so mind your parameters.
        """
        random_layouts, fixed_layouts, max_steps = None, None, None
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
            # points_pct, points, wins, draws, losses, errors, sum_score
            # team_stats = {'Blue_team': [6, 2, 0, 0, 2, 2], 'Red_team': [0, 0, 0, 2, 2, -2]}  # data['team_stats']
            for team_name, data in match_data['teams_stats'].items():
                if team_name in teams_stats:
                    prev_data = teams_stats[team_name]
                    data = [a+b for (a, b) in zip(data, prev_data)]  # add the content of old and new data
                teams_stats.update({team_name: data})

            if max_steps is None:
                max_steps = match_data['max_steps']
                random_layouts = [layout for layout in match_data['layouts'] if layout.startswith('RANDOM')]
                fixed_layouts = [layout for layout in match_data['layouts'] if not layout.startswith('RANDOM')]

        num_matches_per_team = (len(teams_stats) - 1)
        for team_name, data in teams_stats.items():
            data[0] = data[0]//num_matches_per_team  # averaging the percentage of points
            teams_stats.update({team_name: data})

        date_run = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        run_html = self._generate_html_result(run_id, date_run, organizer, games, teams_stats, random_layouts,
                                              fixed_layouts, max_steps, scores_dir, replays_dir, logs_dir)

        html_full_path = os.path.join(self.www_dir, f'results_{run_id}.html')
        with open(html_full_path, "w") as f:
            print(run_html, file=f)

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

    def _generate_matches_table(self, games, scores_dir, replays_dir, logs_dir):
        output = "<h2>Games</h2>\n"

        times_taken = [time_game for (_, _, _, _, _, time_game, _) in games]
        output += f"<h3>No. of games: {len(games)} / "
        output += f"Avg. game length: {str(datetime.timedelta(seconds=round(sum(times_taken) / len(times_taken), 0)))} / "
        output += f"Max game length: {datetime.timedelta(seconds=max(times_taken))}</h3>\n\n"

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

        for (n1, n2, layout, score, winner, time_taken, match_id) in games:
            output += """<tr>"""

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
            output += f"<a href=\"{score_file_path}\">{score_filename}</a>\n"
            output += "</td>"

            # Replay file
            replay_filename = f"match_{match_id}.replay"  # ToDo: possible multiple games in a match
            replay_file_path = os.path.join(replays_dir, replay_filename)
            output += "<td align=\"center\">"
            output += f"<a href=\"{replay_file_path}\">{replay_filename}</a>\n"
            output += "</td>"

            # Logs file
            logs_filename = f"match_{match_id}.log"  # ToDo: possible multiple games in a match
            logs_file_path = os.path.join(logs_dir, logs_filename)
            output += "<td align=\"center\">"
            output += f"<a href=\"{logs_file_path}\">{logs_filename}</a>\n"
            output += "</td>"

            output += """</tr>\n"""
        return output

    def _generate_html_result(self, run_id, date_run, organizer, games, team_stats, random_layouts, fixed_layouts,
                              max_steps, scores_dir, replays_dir, logs_dir):
        """
        Generates the HTML of the report of the run.
        """
        output = """<html><head><title>Results for the tournament round</title>\n"""
        output += """<link rel="stylesheet" type="text/css" href="style.css"/></head>\n"""
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
            # First, print a table with the final standing
            output += self._generate_ranking(team_stats=team_stats)

            # Second, print each game result
            output += "\n\n<br/><br/>"
            output += self._generate_matches_table(games=games, scores_dir=scores_dir, replays_dir=replays_dir,
                                                   logs_dir=logs_dir)

        output += "\n\n</table></body></html>"

        return output


def main():
    settings = load_settings()
    html_generator = HtmlGenerator(settings['www_dir'])
    html_generator.add_contest_run(run_id=0, contest_name="default", organizer=settings['organizer'])


if __name__ == '__main__':
    main()
