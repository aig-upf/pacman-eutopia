from flask import Flask, jsonify, render_template
from flask import send_file
from flask import request
import os
import json
from html_generator import HtmlGenerator

app = Flask(__name__, static_folder='./www/static', template_folder='./www')
html_generator = HtmlGenerator(www_dir='./www')

def find_match(team1, team2):
    directory = './www/scores'  # replace with your directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                for match in data['games']:
                    if (match[0] == team1 and match[1] == team2) or \
                       (match[0] == team2 and match[1] == team1):
                        # Return the match id
                        return match[-1]
    return None

def count_json_files(directory):
    files = os.listdir(directory)
    json_files = [file for file in files if file.endswith('.json')]
    return len(json_files)

@app.route('/json_count')
def json_count():
    directory = './www/scores'  # replace with your directory
    num_json_files = count_json_files(directory)
    return jsonify({'count': num_json_files})

@app.route('/tournament')
def tournament_page():
    directory = './www/scores'  # replace with your directory
    num_json_files = count_json_files(directory)
    print(f'Count: {num_json_files}')
    return render_template('results_0_template.html', count=num_json_files)

@app.route('/search_match', methods=['GET'])
def search_match():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    match = find_match(team1, team2)
    if match:
        return render_template('results_0_template.html', match_id=match['match_id'])
    else:
        return "No match found", 404

@app.route('/get_match_video/<int:match_id>')
def get_match_video(match_id):
    # your directory where the videos are stored
    video_directory = '.'
    
    # the path to the video file
    video_file_path = os.path.join(video_directory, f'match_{match_id}.mp4')
    
    # return the video file
    return send_file(video_file_path, mimetype='video/mp4')

@app.route('/search_team', methods=['GET'])
def search_team():
    team_name = request.args.get('team_name')
    team_info = html_generator.find_team_info(team_name)
    if team_info is None:
        return "No team found", 404
    else:
        return jsonify(team_info)



if __name__ == '__main__':
    app.run(debug=True)