#!/bin/bash

APP=$1

DIR=./dataset/kernels/$APP

# Copy required files to working directory
cp ./dataset/kernels/$APP/*.c .
cp ./dataset/kernels/$APP/*.cpp .
cp ./dataset/kernels/$APP/*.h .
cp ./dataset/kernels/$APP/*.txt .

INPUT_SOURCE_PATH=./*.cpp
INPUT_SOURCE_INFO_PATH=./kernel_info.txt
DB_NAME=$APP

python3 automatic_optimizer.py --INPUT_SOURCE_PATH $INPUT_SOURCE_PATH --INPUT_SOURCE_INFO_PATH $INPUT_SOURCE_INFO_PATH --DB_NAME $DB_NAME

