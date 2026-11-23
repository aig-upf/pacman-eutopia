#!/bin/bash
#SBATCH -J array-matches
#SBATCH -p medium
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=01:00:00
#SBATCH --array=1-999:1                
#SBATCH -o slurm-outputs/%N.%J.out # STDOUT
#SBATCH -e slurm-outputs/%N.%j.err # STDERR

#ml Python
module --ignore-cache load "Python"
source ../venv/bin/activate
TASK_ID=$(( $SLURM_ARRAY_TASK_ID + 999 ))
#python contest_manager.py -s "run_matches" -t $SLURM_ARRAY_TASK_ID
python contest_manager.py -s "run_matches" -t $TASK_ID

deactivate
            
