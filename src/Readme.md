Flask_app.py 

1. Overview
This is a web application built using the Flask framework to manage and display information about a contest called "Pacman Contest". The application provides several routes (API interfaces) to perform the following functions. 

1. Get a directory of all competitions. 
2. Get all team names.
3. Asynchronously generates the tournament playback video. 
4. Download various types of files (e.g., match scores, replays, and logs). 
5. Get complete rankings of all teams.
6. Display the tournament page. 
7. Get tournament information based on team name and year. 
8. Get a list of teams by selected year. 
9. Get available tournament years. 
10. Provide tournament video. 
11. Provide the best match video.

2. Specific functions
get_all_contest_directories(base_dir='. /www')
This function is used to get all the contest directories starting with `contest_` and returns a list of directories within those directories that have `scores` subdirectories.

get_team_names()
This function is used to get the names of all teams and return a list of team names.

generate_video_async(replay_path)
This function is used to generate a match replay video asynchronously. It accepts a `replay_path` parameter which specifies the path to the replay file.

download_file(year, file_type, file_name)
This function is used to download various types of files such as match scores, replays and logs. It accepts year, file_type, and file_name as arguments.

get_full_ranking()
This function is used to get the full ranking of all teams and returns a JSON object.

tournament_page()
This function is used to render the tournament page and return an HTML template.

get_matches()
This function is used to get the matches by team name and year and returns a JSON object.

get_teams()
This function is used to get a list of teams based on the selected year and returns a JSON object.

get_years()
This function is used to get the available years of the tournament and returns a JSON object.

serve_video(selected_year, match_name)
This function is used to serve a video of a match. It accepts the selected year and match name as arguments.

serve_best_match_video()
This function is used to serve the best match video.


File folder:
1. src/contest_video
Folder for all contest videos(Video merged with .png files)

2. src/frames
Save each of Pacman's moves as a frame in .ps files

3. src/frames_png
Convert every .ps file to .png files

4. src/static
Stored html page styles, flask_app.py would access it.

File:
1. best_match.info.txt
Saved the best matches
