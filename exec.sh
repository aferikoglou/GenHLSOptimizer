#!/bin/bash

SCRIPT_PID=$$
echo "Current proc PID "$SCRIPT_PID

check_memory() {

    TOTAL_MEM=$(free --mega | grep Mem | awk '{print $2}')
    # echo "Total memory "$TOTAL_MEM" MB"
    FREE_MEM=$(free --mega | grep Mem | awk '{print $4}')
    # echo "Free memory "$FREE_MEM" MB"
    USED_MEM=$(free --mega | grep Mem | awk '{print $3}')
    # echo "Used memory "$USED_MEM" MB"

    THRESHOLD=$(echo "$TOTAL_MEM*0.95 / 1" | bc)
    echo "Memory threshold "$THRESHOLD" MB"

    while [ $USED_MEM -lt $THRESHOLD ]
    do
        USED_MEM=$(free --mega | grep Mem | awk '{print $3}')
        # echo "Used memory "$USED_MEM" MB"

        sleep 1
    done

    echo "AUTOMATIC OPTIMIZER EXCEEDED MEMORY THRESHOLD !"

    kill -- -$SCRIPT_PID

}

run_func() {
    DIR=./dataset/$APP

    # Copy required files to working directory
    cp ./dataset/$APP/*.cpp .
    cp ./dataset/$APP/*.c .
    cp ./dataset/$APP/*.h .
    cp ./dataset/$APP/*.txt .

    check_memory &
    BACKGROUND_PROC_PID=$!
    echo "check_memory background proc PID "$BACKGROUND_PROC_PID
    sleep 5

    # Start the Design Space Exploration
    
    INPUT_SOURCE_INFO_PATH=./kernel_info.txt
    TOP_LEVEL_FUNCTION=$(head -n 1 kernel_info.txt)
    echo "Top level function = "$TOP_LEVEL_FUNCTION
    INPUT_SOURCE_PATH=$(grep -l $TOP_LEVEL_FUNCTION ./*$SRC_EXTENSION)
    echo "Input source code path = "$INPUT_SOURCE_PATH

    DB_NAME=$APP

    GENERATIONS=24
    THREADS=10
    TIMEOUT=3600 # in sec
    
    python3 automatic_optimizer.py --INPUT_SOURCE_PATH $INPUT_SOURCE_PATH --INPUT_SOURCE_INFO_PATH $INPUT_SOURCE_INFO_PATH --DB_NAME $DB_NAME --SRC_EXTENSION $SRC_EXTENSION --GENERATIONS $GENERATIONS --THREADS $THREADS --TIMEOUT $TIMEOUT

    kill $BACKGROUND_PROC_PID
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

    rm *.json
}

help() {

        echo "Usage: ./driver.sh [MODE]"
    echo " MODE:"
    echo "      run [APPLICATION][SRC_EXTENSION] 	Start the Genetic Algorithm based Design Space Exploration for the given application"
    echo "      kill			Kill all the Vitis HLS 2021.1 processes for the current user"
    echo "      clean			Delete the output files"

}

###############
# Main script #
###############

MODE=$1
APP=$2
SRC_EXTENSION=$3

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
