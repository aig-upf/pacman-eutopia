#!/bin/bash
#SBATCH -J prova_eutopia_contest
#SBATCH -p short
#SBATCH -N 1
#SBATCH -n 2 
#SBATCH --chdir=/homedtic/scalo/pacman-eutopia
#SBATCH --time=2:00
#SBATCH -o %N.%J.out # STDOUT
#SBATCH -e %N.%j.err # STDERR

ml Python
source ../venv/bin/activate
python pacman-contest/src/contest/capture.py --contest-name $1 -b src/$2 --blue-name $3 -r src/$4 --red-name $5 -m 21 --record --record-log -Q &
python pacman-contest/src/contest/capture.py --contest-name $1 -b src/$2 --blue-name $3 -r src/$4 --red-name $5 -m 22 --record --record-log -Q &
python pacman-contest/src/contest/capture.py --contest-name $1 -b src/$2 --blue-name $3 -r src/$4 --red-name $5 -m 23 --record --record-log -Q
deactivate

