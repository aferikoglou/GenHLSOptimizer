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
    
    # Zynq UltraScale+ ZCU104 Evaluation Board (xczu7ev-ffvc1156-2-e)
    # Zynq UltraScale+ ZCU102 Evaluation Board (xczu9eg-ffvb1156-2-e)
    # Alveo U50 Data Center Accelerator Card (xcu50-fsvh2104-2-e)
    # Alveo U200 Data Center Accelerator Card (xcu200-fsgd2104-2-e)

    for DEVICE_ID in xcu200-fsgd2104-2-e; # xczu7ev-ffvc1156-2-e xcu200-fsgd2104-2-e
    do
        for CLK_PERIOD in 10 5 3.33; # 10 5 3.33
        do
            check_memory &
            BACKGROUND_PROC_PID=$!
            echo "check_memory background proc PID "$BACKGROUND_PROC_PID
            sleep 5

            DIR=./dataset/$APP

            # Copy required files to working directory
            cp ./dataset/$APP/*.cpp .
            cp ./dataset/$APP/*.c .
            cp ./dataset/$APP/*.h .
            cp ./dataset/$APP/*.hpp .
            cp ./dataset/$APP/*.txt .

            # Start the Design Space Exploration
    
            INPUT_SOURCE_INFO_PATH=./kernel_info.txt
            TOP_LEVEL_FUNCTION=$(head -n 1 kernel_info.txt)
            echo "Top level function = "$TOP_LEVEL_FUNCTION
            INPUT_SOURCE_PATH=$(grep -l $TOP_LEVEL_FUNCTION ./*$SRC_EXTENSION)
            echo "Input source code path = "$INPUT_SOURCE_PATH

            DB_NAME=${APP}_${DEVICE_ID}_${CLK_PERIOD}

            echo ""
            echo "DESIGN SPACE EXPLORATION FOR "$APP" FOR DEVICE WITH ID "$DEVICE_ID" AND TARGET CLOCK PERIOD "$CLK_PERIOD" USEC"
            echo ""

            THREADS=20
            python3 automatic_optimizer.py --INPUT_SOURCE_PATH $INPUT_SOURCE_PATH --INPUT_SOURCE_INFO_PATH $INPUT_SOURCE_INFO_PATH --DB_NAME $DB_NAME --SRC_EXTENSION $SRC_EXTENSION --DEVICE_ID $DEVICE_ID --CLK_PERIOD $CLK_PERIOD --THREADS $THREADS
        
            clean_func

            kill $BACKGROUND_PROC_PID

        done
    done

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

    # rm *.json
}

help() {

        echo "Usage: ./exec.sh [MODE]"
    echo " MODE:"
    echo "      run [APPLICATION] [SRC_EXTENSION] 	Start the Genetic Algorithm based Design Space Exploration for the given application"
    echo "      kill                                Kill all the Vitis HLS 2021.1 processes for the current user"
    echo "      clean                               Delete the output files"

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
