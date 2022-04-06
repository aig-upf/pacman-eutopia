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

DIR_SCRIPT = sys.path[0]
FILE_FONTS = os.path.join(DIR_SCRIPT, "fonts.zip")
FILE_CSS = os.path.join(DIR_SCRIPT, "style.css")


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
    settings['scores_dir'] = os.path.join(settings['www_dir'], "scores")
    settings['replays_dir'] = os.path.join(settings['www_dir'], "replays")
    settings['logs_dir'] = os.path.join(settings['www_dir'], "logs")

    logging.info(f'Script will run with this configuration: {settings}')

    return settings


# ----------------------------------------------------------------------------------------------------------------------

class HtmlGenerator:
    def __init__(self, www_dir, contest, organizer, score_thresholds=None):
        """
        Initializes this generator.

        :param www_dir: the output path
        :param organizer: the name of the organizer of the tournament (e.g., XX University)
        """

        # path that contains files that make-up a html navigable web folder
        self.www_dir = www_dir
        self.contest = contest

        # just used in html as a readable string
        self.organizer = organizer
        self.score_thresholds = score_thresholds
        self.ERROR_SCORE = 9999

    def _close(self):
        pass

    def clean_up(self):
        """
        Empties and removes the output directory
        """
        shutil.rmtree(self.www_dir)

    def add_run(self, run_id, scores_dir, replays_dir, logs_dir):
        """
        (Re)Generates the HTML for the given run and updates the HTML index.
        :return:
        """
        self._save_run_html(run_id, scores_dir, replays_dir, logs_dir)
        self._generate_main_html()

    def _save_run_html(self, run_id, scores_file, replays_file, logs_file):
        """
        Generates the HTML of a contest run and saves it in www/results_<run_id>/results.html.

        The URLs passed should be either:
         - HTTP URLs, in which case the scores file is downloaded to generate the HTML
         - local relative paths, which are assumed to start from self.www_dir

        No checks are done, so mind your parameters.
        """
        # The URLs may be in byte format - convert them to strings if needed
        try:
            scores_file = scores_file.decode()
        except AttributeError:
            pass
        try:
            replays_file = replays_file.decode()
        except AttributeError:
            pass
        try:
            logs_file = logs_file.decode()
        except AttributeError:
            pass

        #stats_file_path = os.path.join(self.www_dir, self.contest, scores_file)
        #with open(stats_file_path, 'r') as f:
        with open(scores_file, 'r') as f:
            match_data = json.load(f)

        games = match_data['games']
        max_steps = match_data['max_steps']
        # [('Blue_team', [6, 2, 0, 0, 2, 2]), ('Red_team', [0, 0, 0, 2, 2, -2])]
        # points_pct, points, wins, draws, losses, errors, sum_score
        # team_stats = {'Blue_team': [6, 2, 0, 0, 2, 2], 'Red_team': [0, 0, 0, 2, 2, -2]}  # data['team_stats']
        team_stats = match_data['team_stats']
        random_layouts = [layout for layout in match_data['layouts'] if layout.startswith('RANDOM')]
        fixed_layouts = [layout for layout in match_data['layouts'] if not layout.startswith('RANDOM')]
        organizer = self.organizer
        date_run = run_id

        os.makedirs(f"{self.www_dir}", exist_ok=True)
        contest_zip_file = zipfile.ZipFile(FILE_FONTS)
        contest_zip_file.extractall(self.www_dir)
        shutil.copy(FILE_CSS, self.www_dir)

        run_html = self._generate_output(run_id, date_run, organizer, games, team_stats, random_layouts, fixed_layouts,
                                         max_steps, scores_file, replays_file, logs_file)

        html_full_path = os.path.join(self.www_dir, f'results_{run_id}.html')
        with open(html_full_path, "w") as f:
            print(run_html, file=f)

    def _generate_main_html(self):
        """
        Generates the index HTML, containing links to the HTML files of all the runs.
        The file is saved in www/results.html.
        """
        # regenerate main html
        main_html = """<html><head><title>Results for PACMAN Capture the Flag the tournament</title>\n"""
        main_html += """<link rel="stylesheet" type="text/css" href="style.css"/></head>\n"""
        main_html += """<body><h1>Results Pacman Capture the Flag by Date</h1>\n"""
        main_html += f"""<body><h2>Organizer: {self.organizer} </h1>\n\n"""
        for d in sorted(os.listdir(self.www_dir)):
            if d.endswith('fonts'):
                continue
            if not d.startswith('results'):
                continue
            main_html += f"""<a href="{d}"> {d[:-5]}  </a> <br/>\n"""
        main_html += "\n\n<br/></body></html>"
        with open(os.path.join(self.www_dir, 'index.html'), "w") as f:
            print(main_html, file=f)

    def _generate_output(self, run_id, date_run, organizer, games, team_stats, random_layouts, fixed_layouts, max_steps,
                         scores_dir, replays_dir, logs_dir):
        """
        Generates the HTML of the report of the run.
        """

        if organizer is None:
            organizer = self.organizer

        output = """<html><head><title>Results for the tournament round</title>\n"""
        output += """<link rel="stylesheet" type="text/css" href="style.css"/></head>\n"""
        output += """<body><h1>PACMAN Capture the Flag Tournament</h1>\n"""
        output += f"""<body><h2>Tournament Organizer: {organizer} </h1>\n"""
        if not run_id == date_run:
            output += f"""<body><h2>Name of Tournament: {run_id} </h1>\n"""
        output += f"""<body><h2>Date of Tournament: {date_run} \n</h1>"""

        output += """<h2>Configuration: %d teams in %d (%d fixed + %d random) layouts for %d steps</h2>\n""" \
                  % (len(team_stats), len(fixed_layouts) + len(random_layouts), len(fixed_layouts), len(random_layouts),
                     max_steps)

        output += """<br/><br/><table border="1">"""
        if not games:
            output += "No match was run."
        else:
            # First, print a table with the final standing
            output += """<tr>"""
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

            # If score thresholds exist for table, sort in reverse order and add -1 as terminal boundary
            if self.score_thresholds is None:
                score_thresholds = [-1]
            else:
                score_thresholds = sorted(self.score_thresholds, reverse=True) + [-1]

            next_threshold_index = 0

            # Sort teams by points_pct v[1][0] first, then no. of wins, then score points.
            # example list(team_stats.items() = [('Blue_team', [6, 2, 0, 0, 2, 2]), ('Red_team', [0, 0, 0, 2, 2, -2])]
            sorted_team_stats = sorted(list(team_stats.items()), key=lambda v: (v[1][0], v[1][2], v[1][6]),
                                       reverse=True)
            position = 0
            for key, (points_pct, points, wins, draws, losses, errors, sum_score) in sorted_team_stats:
                while score_thresholds[next_threshold_index] > points_pct:
                    output += f"""<tr bgcolor="#D35400"><td colspan="10" style="text-align:center">{
                    score_thresholds[next_threshold_index]}%% </td></tr>\n"""
                    next_threshold_index += 1
                position += 1
                output += """<tr>"""
                output += f"""<td>{position}</td>"""
                output += f"""<td>{key}</td>"""
                output += f"""<td>{points_pct}%%</td>"""
                output += f"""<td>{points}</td>"""
                output += f"""<td>{wins}</td>"""
                output += f"""<td >{draws}</td>"""
                output += f"""<td>{losses}</td>"""
                output += f"""<td>{(wins + draws + losses)}</td>"""
                output += f"""<td >{errors}</td>"""
                output += f"""<td >{sum_score}</td>"""
                output += f"""</tr>\n"""
            output += "</table>"

            # Second, print each game result
            output += "\n\n<br/><br/><h2>Games</h2>\n"

            times_taken = [time_game for (_, _, _, _, _, time_game) in games]
            output += """<h3>No. of games: %d / Avg. game length: %s / Max game length: %s</h3>\n""" \
                      % (len(games), str(datetime.timedelta(seconds=round(sum(times_taken) / len(times_taken), 0))),
                         str(datetime.timedelta(seconds=max(times_taken))))

            if replays_dir:
                output += f"""<a href="{replays_dir}">DOWNLOAD REPLAYS</a><br/>\n"""
            if logs_dir:
                output += f"""<a href="{logs_dir}">DOWNLOAD LOGS</a><br/>\n"""
            if scores_dir:
                output += f"""<a href="{scores_dir}">DOWNLOAD SCORES</a><br/>\n\n"""
            output += """<table border="1">"""
            output += """<tr>"""
            output += """<th>Team 1</th>"""
            output += """<th>Team 2</th>"""
            output += """<th>Layout</th>"""
            output += """<th>Time</th>"""
            output += """<th>Score</th>"""
            output += """<th>Winner</th>"""
            output += """</tr>\n"""
            for (n1, n2, layout, score, winner, time_taken) in games:
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
                output += f"""<td>{str(datetime.timedelta(seconds=time_taken))}</td>"""

                # Score and Winner
                if score == self.ERROR_SCORE:
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

                output += """</tr>\n"""

        output += "\n\n</table></body></html>"

        return output


def main():
    settings = load_settings()

    scores_dir = settings['scores_dir']
    replays_dir = settings['replays_dir']
    logs_dir = settings['logs_dir']

    html_generator = HtmlGenerator(settings['www_dir'], settings['organizer'])

    if scores_dir is not None:
        # Collect all files in scores directory
        all_files = [f for f in os.listdir(scores_dir) if os.path.isfile(os.path.join(scores_dir, f))]

        # make paths relative to www_dir
        www_dir = settings['www_dir']
        scores_dir = os.path.relpath(scores_dir, www_dir)
        replays_dir = os.path.relpath(replays_dir, www_dir) if replays_dir else None
        logs_dir = os.path.relpath(logs_dir, www_dir) if logs_dir else None

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

            html_generator.add_run(run_id, score_file_full_path, replays_file_full_path, logs_file_full_path)


if __name__ == '__main__':
    main()
