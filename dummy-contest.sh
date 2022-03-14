#!/bin/bash
#SBATCH -J prova_eutopia_contest
#SBATCH -p short
#SBATCH -N 1
#SBATCH -n 2 
#SBATCH --chdir=/homedtic/jsegovia/pacman-contest-agent
#SBATCH --time=2:00
#SBATCH -o %N.%J.out # STDOUT
#SBATCH -e %N.%j.err # STDERR

source ../venv/bin/activate
ml Tkinter
python3 capture.py -t -r baselineTeam -b baselineTeam
deactivate

