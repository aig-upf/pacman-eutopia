Scripts Usage Guide

Overview

This guide provides a detailed explanation of the two scripts: process_replays.slurm and prepare_and_submit.sh, outlining their purposes and usage instructions.

1. Script Descriptions
1.1. process_replays.slurm
This script serves as a Slurm job script, outlining how to process a single .replay file. Slurm will execute this script for each task array element defined within it.

1.2. prepare_and_submit.sh
This script automates the following tasks:

Finds all .replay files and writes their paths to a file named replay_files.txt.
Counts the number of .replay files found.
Replaces the placeholder "XXX" in the process_replays.slurm script with the actual number of files.
Submits the process_replays.slurm job to Slurm for execution.

2. Usage Instructions
2.1. Ensure Scripts are Executable
Before executing these scripts, ensure they both have execution permissions. This can be granted using the following command:

code
chmod +x process_replays.slurm prepare_and_submit.sh

2.2. Execute prepare_and_submit.sh
Start by running the prepare_and_submit.sh script. It will automatically locate all .replay files, count them, modify the process_replays.slurm script accordingly, and then submit the job to Slurm.


code
./prepare_and_submit.sh