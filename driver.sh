#!/bin/bash

run_func() {
	DIR=./dataset/ready2run/$APP

	# Copy required files to working directory
	cp ./dataset/ready2run/$APP/*.cpp .
	cp ./dataset/ready2run/$APP/*.h .
	cp ./dataset/ready2run/$APP/*.txt .

	# Start the Design Space Exploration
	INPUT_SOURCE_PATH=./*.cpp
	INPUT_SOURCE_INFO_PATH=./kernel_info.txt
	DB_NAME=$APP

	TIMEOUT=3600
	python3 automatic_optimizer.py --INPUT_SOURCE_PATH $INPUT_SOURCE_PATH --INPUT_SOURCE_INFO_PATH $INPUT_SOURCE_INFO_PATH --DB_NAME $DB_NAME --GENERATIONS 24 --THREADS 40 --TIMEOUT $TIMEOUT

	# Get database analytics
	python3 db_analyzer.py --DB_NAME $APP --TIMEOUT $TIMEOUT
}

kill_func() {
	echo "Killing Vitis HLS 2021.1 processes for "$USER

	for pid in `ps -aux | grep $USER | grep vitis | awk '{print $2}'`;
	do
	       	echo $pid	
		kill $pid
	done
}

clean_func() {
	rm -r GENETIC_DSE_*
	rm vitis_*.log
	rm script_*.tcl
	rm kernel_*.cpp
	rm hs_err_pid*.log
	rm -r optimized

	rm *.cpp
	rm *.cl
	rm *.c
	rm *.h
	rm kernel_info.txt
}

help() {

        echo "Usage: ./driver.sh [MODE]"
	echo " MODE:"
	echo "      run [APPLICATION] 	Start the Genetic Algorithm based Design Space Exploration for the given application"
	echo "      kill			Kill all the Vitis HLS 2021.1 processes for the current user"
	echo "      clean			Delete the output files"

}

###############
# Main script #
###############

MODE=$1
APP=$2

if [ "${MODE}" == "run" ];
then
	run_func
elif [ "${MODE}" == "kill" ];
then
        kill_func
elif [ "${MODE}" == "clean" ];
then
        clean_func
else
        help
fi
