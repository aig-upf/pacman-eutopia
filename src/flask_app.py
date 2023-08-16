from flask import Flask, render_template, jsonify, request
import os
import json
from flask import send_file
import subprocess
from subprocess import Popen
import logging

# Logging Configuration
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
logging.basicConfig(
    filename='app.log',
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.debug("This is a debug message")


app = Flask(__name__, static_folder='./www/static', template_folder='./www')



def get_all_contest_directories(base_dir='./www'):

    directories = []
    for folder in os.listdir(base_dir):
        if folder.startswith('contest_'):
            score_dir = os.path.join(base_dir, folder, 'scores')
            if os.path.exists(score_dir):
                directories.append(score_dir)
    return directories



def get_team_names():
    team_names = set()
    directories = get_all_contest_directories()
    for directory in directories:
        for filename in os.listdir(directory):
            if filename.startswith('match_') and filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)
                    for team_name in data['teams_stats']:
                        team_names.add(team_name)
    return list(team_names)

def generate_video_async(replay_path):
    command = ['python', 'capture.py', f'--replay={replay_path}']
    process = subprocess.Popen(command)
    return process


@app.route('/download/<year>/<file_type>/<file_name>')
def download_file(year, file_type, file_name):
    if year == "default":
        # Directly set the directory for default
        file_path = f'./www/contest_default/{file_type}s/{file_name}'
    else:
        # Extract only the last part of the year (e.g., 'ai22' from 'contest_upf-ai22')
        extracted_year = year.split('-')[-1]
        # Construct file paths using the relative directory
        file_path = f'./www/contest_upf-{extracted_year}/{file_type}s/{file_name}'
    
    logging.debug("File Path: %s", file_path)
    return send_file(file_path, as_attachment=True)




@app.route('/get_full_ranking')
def get_full_ranking():
    # Collect all team statistics
    teams_stats = {}
    directories = get_all_contest_directories()
    for directory in directories:
        for filename in os.listdir(directory):
            if filename.startswith('match_') and filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)
                    for team_name, stats in data['teams_stats'].items():
                        if team_name in teams_stats:
                            prev_stats = teams_stats[team_name]
                            stats = [a + b for (a, b) in zip(stats, prev_stats)]  # add the stats of old and new data
                        teams_stats.update({team_name: stats})

    # Sort teams by points_pct v[1][0] first, then no. of wins, then score points.
    sorted_team_stats = sorted(list(teams_stats.items()), key=lambda v: (v[1][0], v[1][2], v[1][6]), reverse=True)
    
    # Return the sorted team stats as JSON
    return jsonify({'ranking': sorted_team_stats})




@app.route('/tournament')
def tournament_page():
    team_names = get_team_names()
    return render_template('results_0_template.html', team_names=team_names)

@app.route('/get_matches')
def get_matches():
    selected_team = request.args.get('team_name')
    selected_year = request.args.get('year')  # Get the selected year

    if selected_year == "default":
        directory = './www/contest_default/scores'
    else:
        directory = f'./www/contest_upf-ai{selected_year[-2:]}/scores'  # Construct pathways based on year
    
    matches = []
    for filename in os.listdir(directory):
        if filename.startswith('match_') and filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                match_id = filename.replace('.json', '')
                for game in data['games']:
                    if selected_team in game[:2]:
                        # Add the correct suffix based on the file type
                        score_file = filename
                        replay_file = filename.replace('.json', '.replay')
                        log_file = filename.replace('.json', '.log')
                        match = {
                            'match_id': match_id,
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
    logging.debug("Received year: %s", selected_year)
    if selected_year == "default":
        directory = './www/contest_default/scores'
    else:
        directory = f'./www/contest_upf-ai{selected_year[-2:]}/scores'
    team_names = set()
    for filename in os.listdir(directory):
        if filename.startswith('match_') and filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                for team_name in data['teams_stats']:
                    team_names.add(team_name)
    return jsonify({'teams': list(team_names)})


@app.route('/get_years')
def get_years():
    base_dir = './www'
    years = ['default']  # Start with the default option
    years.extend([folder.split('-')[-1] for folder in os.listdir(base_dir) if folder.startswith('contest_upf-ai')]) 
    return jsonify({'years': years})


@app.route('/videos/<selected_year>/<match_name>.mp4')
def serve_video(selected_year, match_name):
    logging.info("serve_video function was called with selected_year: %s and match_name: %s", selected_year, match_name)

    # 根据 selected_year 构建相应的 replay 文件路径
    if selected_year == 'default':
        replay_directory = '/Users/player/Documents/GitHub/pacman-eutopia/src/www/contest_default/replays'
    else:
        replay_directory = f'/Users/player/Documents/GitHub/pacman-eutopia/src/www/contest_upf-{selected_year}/replays'
    
    # 根据 match_name 构建完整的 .replay 文件路径
    replay_path = os.path.join(replay_directory, f'{match_name}.replay')

    # mp4 文件保存的目录
    mp4_directory = '/Users/player/Documents/GitHub/pacman-eutopia/src/contest_video'
    # 构建对应的 .mp4 文件路径
    mp4_path = os.path.join(mp4_directory, f'{match_name}.mp4')
    
    logging.debug("Selected Year: %s", selected_year)
    logging.debug("Match Name: %s", match_name)
    logging.debug("Replay Path: %s", replay_path)
    logging.debug("MP4 Path: %s", mp4_path)

    # 检查 .mp4 文件是否存在
    if os.path.exists(mp4_path):
        logging.info(".MP4 file found. Sending file: %s", mp4_path)
        # 如果 .mp4 文件存在，将其作为响应返回
        return send_file(mp4_path, mimetype='video/mp4')
    else:
        logging.debug(".MP4 file not found. Checking for .replay file...")
        # 如果 .mp4 文件不存在，检查 .replay 文件是否存在
        if os.path.exists(replay_path):
            logging.debug(".Replay file found. Starting async video generation...")
            
            #capture.py的路径
            capture_script_path = '/Users/player/Documents/GitHub/pacman-eutopia/pacman-contest/src/contest/capture.py'
            
            # 启动异步进程生成视频
            command = ['python', capture_script_path, f'--replay={replay_path}']
            process = Popen(command)  # 使用 Popen 异步执行命令
            
            # 立即回应客户端，告知视频正在生成
            return jsonify({'status': 'Video is being generated, please check back later'}), 202
        
        else:
            logging.error(".Replay file not found.")
            # 如果 .replay 文件不存在，返回一个错误消息
            return jsonify({'error': 'Replay file not found'}), 404



if __name__ == '__main__':
    app.run(debug=True)