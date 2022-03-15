#!/bin/bash
#SBATCH -J prova_eutopia_contest
#SBATCH -p short
#SBATCH -N 1
#SBATCH -n 2 
#SBATCH --chdir=/homedtic/jsegovia/pacman-eutopia/contest
#SBATCH --time=2:00
#SBATCH -o %N.%J.out # STDOUT
#SBATCH -e %N.%j.err # STDERR

source ../venv/bin/activate
ml Tkinter
python3 capture.py -b agents/team_name_1/myTeam.py -r agents/team_name_2/myTeam.py  --record --game_id 1234
deactivate

