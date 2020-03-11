#!/bin/bash

CONDA_PREFIX="$HOME/miniconda3/"
PROJECT_ROOT="$HOME/weather-flask-app/"

# Source the conda environment (source --> .)
. $CONDA_PREFIX/etc/profile.d/conda.sh
conda activate weather-app

# Change to project root
cd $PROJECT_ROOT

# Run the program
python pull_and_update.py 2>&1 | tee -a $HOME/nws_weather.log
