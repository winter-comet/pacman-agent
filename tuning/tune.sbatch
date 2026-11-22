#!/bin/bash
#SBATCH --job-name=pac-tune
#SBATCH --partition=all
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=tuning/slurm-%j.out

cd "$SLURM_SUBMIT_DIR"
## TODO: Finish script for agent parameter tuning.