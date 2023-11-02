#!/bin/bash

# 1. find all .replay files and write their paths to replay_files.txt
find ~ -name "*.replay" > replay_files.txt

# 2. Counting the number of documents found
NUM_FILES=$(wc -l < replay_files.txt)
echo "Found $NUM_FILES .replay files."

# 3. Use the sed command to replace XXX in the Slurm script with the actual number of documents
sed -i "s/XXX/$NUM_FILES/" process_replays.sh

# 4. Submission of Slurm tasks
sbatch process_replays.sh
