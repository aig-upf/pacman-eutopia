from flask import Flask, render_template, jsonify, request
import os
import json
from flask import send_file

app = Flask(__name__, static_folder='./www/static', template_folder='./www')

def get_team_names():
    team_names = set()
    directories = [
        './www/contest_upf-ai22/scores',
        './www/contest_upf-ai23/scores'
    ]  # Directories for both years
    for directory in directories:
        for filename in os.listdir(directory):
            if filename.startswith('match_') and filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)
                    for team_name in data['teams_stats']:
                        team_names.add(team_name)
    return list(team_names)

@app.route('/download/<year>/<file_type>/<file_name>')
def download_file(year, file_type, file_name):
    # Get current working directory
    current_dir = os.getcwd()
    # Construct file paths from the current working directory
    file_path = os.path.join(current_dir, f'www/contest_upf-ai{year}/{file_type}s/{file_name}')
    print(file_path)
    return send_file(file_path, as_attachment=True)






@app.route('/tournament')
def tournament_page():
    team_names = get_team_names()
    return render_template('results_0_template.html', team_names=team_names)

@app.route('/get_matches')
def get_matches():
    selected_team = request.args.get('team_name')
    selected_year = request.args.get('year')  # Get the selected year
    matches = []
    directory = f'./www/contest_upf-ai{selected_year}/scores'  # Construct pathways based on year
    for filename in os.listdir(directory):
        if filename.startswith('match_') and filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                for game in data['games']:
                    if selected_team in game[:2]:
                        # Add the correct suffix based on the file type
                        score_file = filename
                        replay_file = filename.replace('.json', '.replay')
                        log_file = filename.replace('.json', '.log')
                        match = {
                            'team1': game[0],
                            'team2': game[1],
                            'layout': game[2],
                            'time': game[3],
                            'score': game[5],
                            'winner': game[0] if game[5] > 0 else game[1],
                            'score_file': f"/download/{selected_year}/score/{score_file}",
                            'replay_file': f"/download/{selected_year}/replay/{replay_file}",
                            'log_file': f"/download/{selected_year}/log/{log_file}"
                        }
                        matches.append(match)
    return jsonify({'matches': matches})


@app.route('/get_teams')
def get_teams():
    selected_year = request.args.get('year')
    directory = f'./www/contest_upf-ai{selected_year}/scores'
    team_names = set()
    for filename in os.listdir(directory):
        if filename.startswith('match_') and filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                for team_name in data['teams_stats']:
                    team_names.add(team_name)
    return jsonify({'teams': list(team_names)})

if __name__ == '__main__':
    app.run(debug=True)