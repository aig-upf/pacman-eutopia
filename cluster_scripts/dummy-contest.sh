#!/bin/bash
#SBATCH -J prova_eutopia_contest
#SBATCH -p short
#SBATCH -N 1
#SBATCH -n 2 
#SBATCH --chdir=/homedtic/scalo/pacman-eutopia/pacman-contest/src/contest
#SBATCH --time=2:00
#SBATCH -o %N.%J.out # STDOUT
#SBATCH -e %N.%j.err # STDERR

source ../../venv/bin/activate
ml Tkinter
python3 ../pacman-contest/src/contest/capture.py -t -r ../pacman-contest/src/contest/baselineTeam -b ../pacman-contest/src/contest/baselineTeam
deactivate

