#!/bin/bash
#SBATCH --job-name=create_files
#SBATCH --output=logs/out/create_files%A_%a.out
#SBATCH --error=logs/err/create_files%A_%a.err
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=20GB
#SBATCH --time=10:00:00
#SBATCH --account metabolinkai

echo "Running on $(hostname) at $(date)"

cd /idiap/temp/mcarlsson/chebin/binche2 || exit

# shellcheck source=/dev/null
source .venv/bin/activate

python -m chebin.preparing_data.create_files

echo Done!
