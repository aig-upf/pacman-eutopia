#!/bin/bash
#SBATCH -J array-matches
#SBATCH -p medium
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --chdir=/homedtic/scalo/pacman-eutopia/src
#SBATCH --time=7:00
#SBATCH --array=1-7:1
#SBATCH -o slurm-outputs/%N.%J.out # STDOUT
#SBATCH -e slurm-outputs/%N.%j.err # STDERR

#ml Python
module --ignore-cache load "Python"
source ../venv/bin/activate
python run_matches.py $SLURM_ARRAY_TASK_ID

deactivate

