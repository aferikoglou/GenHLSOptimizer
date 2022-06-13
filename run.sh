#!/bin/bash

APP=$1

DIR=./dataset/kernels/$APP

# Copy required files to working directory

cp ./dataset/kernels/$APP/*.cpp .
cp ./dataset/kernels/$APP/*.h .
cp ./dataset/kernels/$APP/*.txt .

# DSE

INPUT_SOURCE_PATH=./*.cpp
INPUT_SOURCE_INFO_PATH=./kernel_info.txt
DB_NAME=$APP

TIMEOUT=7200

python3 automatic_optimizer.py --INPUT_SOURCE_PATH $INPUT_SOURCE_PATH --INPUT_SOURCE_INFO_PATH $INPUT_SOURCE_INFO_PATH --DB_NAME $DB_NAME --GENERATIONS 2 --THREADS 40 --TIMEOUT $TIMEOUT

# DB Analysis

python3 db_analyzer.py --DB_NAME $APP --TIMEOUT $TIMEOUT

# Clean up

# rm -r GENETIC_DSE_*
# rm vitis_*.log
# rm script_*.tcl
# rm kernel_*.cpp
# rm *.cpp
# rm *.h
# rm kernel_info.txt
