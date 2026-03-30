
# This shell script has been adapted from a slurm submission script, with the following setup:

#flic-cirrus@login03:/.../clonezone/RSE-personas(main)$ cat submit_5x_HGBT_tuning_grid.slurm
###!/bin/bash --login

#SBATCH --job-name=5x_HGBT-tuning-grid
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=96:00:00
#SBATCH --hint=nomultithread
#SBATCH --output=/work/####/####/flic-cirrus/clonezone/logcabin/%x_%j_output.out
##SBATCH --error=%x_%j_ERROR.err

# Replace [budget code] below with your project code (e.g. t01)
#SBATCH --account=#####
#SBATCH --partition=standard
#SBATCH --qos=long

# Load the Python module, ...
#module load cray-python

# ..., or, if using local virtual environment
#source /.../clonezone/RSE-personas/coding-smart-github/bin/activate

# Run your Python program
echo "BEGINNING MULTI-SEED TUNING RUNS WITH NOISE!"

echo "============================= Run 0: seed 69: No X Noise =================================="
time python githubanalysis/analysis/ML_tuning.py -n 10000 -i 1 -r 69 -c RF -s HalvingGridSearchCV -j 32 -x 0.0 -y 0.0 -d 1.0

echo "============================= Run 1a: seed 69: 10% X Noise @ 1SD =================================="
time python githubanalysis/analysis/ML_tuning.py -n 10000 -i 1 -r 69 -c RF -s HalvingGridSearchCV -j 32 -x 0.1 -y 0.0 -d 1.0

echo "============================= Run 1b: seed 69: 20% X Noise @ 1SD =================================="
time python githubanalysis/analysis/ML_tuning.py -n 10000 -i 1 -r 69 -c RF -s HalvingGridSearchCV -j 32 -x 0.2 -y 0.0 -d 1.0

echo "============================= Run 2a: seed 69: 10% X Noise @ 1.5SD =================================="
time python githubanalysis/analysis/ML_tuning.py -n 10000 -i 1 -r 69 -c RF -s HalvingGridSearchCV -j 32 -x 0.1 -y 0.0 -d 1.5

echo "============================= Run 2b: seed 69: 20% X Noise @ 1.5SD =================================="
time python githubanalysis/analysis/ML_tuning.py -n 10000 -i 1 -r 69 -c RF -s HalvingGridSearchCV -j 32 -x 0.2 -y 0.0 -d 1.5


echo "COMPLETE"

