#!/bin/bash
#SBATCH -J process_replay         
#SBATCH -p short                  
#SBATCH -N 1                      
#SBATCH -n 1                     
#SBATCH --array=1-XXX%10          
#SBATCH --chdir=/path/to/your/working/directory 
#SBATCH --time=2:00               
#SBATCH -o %N.%J.%a.out         
#SBATCH -e %N.%J.%a.err           

# Activate the python environment or load the required modules
source /path/to/your/python/environment/bin/activate

# Get the path to the .replay file for the corresponding task
REPLAY_PATH=$(sed -n "${SLURM_ARRAY_TASK_ID}p" replay_files.txt)

# Execute your command
python ./src/contest/capture.py --replay=$REPLAY_PATH

deactivate
