#!/bin/bash
#SBATCH -J prova_eutopia_contest
#SBATCH -p short
#SBATCH -N 1
#SBATCH -n 2 

#SBATCH --chdir=/homedtic/scalo/pacman-eutopia2/pacman-contest/src/contest
#SBATCH --time=2:00
#SBATCH -o %N.%J.out # STDOUT
#SBATCH -e %N.%j.err # STDERR

ml Python
source ../venv/bin/activate
python ../pacman-contest/src/contest/capture.py --contest-name UPF-EUTOPIA -b upf-ai22_firstTeamName2022/myTeam.py --blue-name firstTeamName2022 -r upf-ai22_secondTeamName2022/myTeam.py --red-name secondTeamName2022 -m 5678 --record --record-log -Q
deactivate

