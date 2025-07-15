#!/bin/bash

# Store the current script's process ID (PID)
SCRIPT_PID=$$
echo "Current proc PID "$SCRIPT_PID

# Function to monitor system memory usage and kill the script if memory usage exceeds a threshold
check_memory() {
    # Get total memory in MB
    TOTAL_MEM=$(free --mega | grep Mem | awk '{print $2}')
    # Get free memory in MB
    FREE_MEM=$(free --mega | grep Mem | awk '{print $4}')
    # Get used memory in MB
    USED_MEM=$(free --mega | grep Mem | awk '{print $3}')

    # Calculate threshold as 95% of total memory
    THRESHOLD=$(echo "$TOTAL_MEM*0.95 / 1" | bc)
    echo "Memory threshold "$THRESHOLD" MB"

    # Loop while used memory is less than threshold (wait until memory exceeds threshold)
    while [ $USED_MEM -lt $THRESHOLD ]
    do
        # Update used memory
        USED_MEM=$(free --mega | grep Mem | awk '{print $3}')
        # Sleep 1 second before checking again
        sleep 1
    done

    # Print warning message when threshold exceeded
    echo "AUTOMATIC OPTIMIZER EXCEEDED MEMORY THRESHOLD !"

    # Kill the entire script process group (script + child processes)
    kill -- -$SCRIPT_PID
}

# Main function to run design space exploration (DSE) on specified devices and clock periods
run_func() {

    # List of FPGA device IDs to run optimization on
    # ZCU104 and Alveo U200 are active here
    for DEVICE_ID in xczu7ev-ffvc1156-2-e xcu200-fsgd2104-2-e; 
    do
        # List of clock periods (in nanoseconds) to explore
        for CLK_PERIOD in 10 5 3.33; 
        do
            # Start memory monitoring in background
            check_memory &
            BACKGROUND_PROC_PID=$!
            echo "check_memory background proc PID "$BACKGROUND_PROC_PID
            # Wait 5 seconds before starting the optimization
            sleep 5

            # Directory for application dataset files
            DIR=./Applications/$APP

            # Copy all relevant source and info files from dataset to current working directory
            cp ./Applications/$APP/*.cpp .
            cp ./Applications/$APP/*.c .
            cp ./Applications/$APP/*.h .
            cp ./Applications/$APP/*.hpp .
            cp ./Applications/$APP/*.txt .

            # Setup input paths for the optimizer
            INPUT_SOURCE_INFO_PATH=./kernel_info.txt

            # Read top-level function name from kernel_info.txt (first line)
            TOP_LEVEL_FUNCTION=$(head -n 1 kernel_info.txt)
            echo "Top level function = "$TOP_LEVEL_FUNCTION

            # Find the source code file that contains the top-level function in its name
            INPUT_SOURCE_PATH=$(grep -l $TOP_LEVEL_FUNCTION ./*$SRC_EXTENSION)
            echo "Input source code path = "$INPUT_SOURCE_PATH

            # Define the database name for this run
            DB_NAME=${APP}_${DEVICE_ID}_${CLK_PERIOD}

            # Print info about the current DSE run
            echo ""
            echo "DESIGN SPACE EXPLORATION FOR "$APP" FOR DEVICE WITH ID "$DEVICE_ID" AND TARGET CLOCK PERIOD "$CLK_PERIOD" USEC"
            echo ""

            THREADS=10

            # Run the Python optimizer with all the specified parameters
            python3 GenHLSOptimizer.py --INPUT_SOURCE_PATH $INPUT_SOURCE_PATH --INPUT_SOURCE_INFO_PATH $INPUT_SOURCE_INFO_PATH --DB_NAME $DB_NAME --SRC_EXTENSION $SRC_EXTENSION --DEVICE_ID $DEVICE_ID --CLK_PERIOD $CLK_PERIOD --THREADS $THREADS
        
            # Clean up generated files after the run
            clean_func

            # Kill the background memory checking process
            kill $BACKGROUND_PROC_PID

        done
    done
}

# Function to kill all running Vitis HLS processes for the current user
kill_func() {
    echo "Killing Vitis HLS processes for "$USER

    # Find and kill all Vitis processes owned by the current user
    for pid in `ps -aux | grep $USER | grep vitis | awk '{print $2}'`;
    do
        echo $pid	
        kill $pid
    done
}

# Function to clean up files generated during optimization runs
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

# Function to display usage information
help() {
    echo "Usage: ./exec.sh [MODE]"
    echo " MODE:"
    echo "      run [APPLICATION] [SRC_EXTENSION] 	Start the Genetic Algorithm based Design Space Exploration for the given application"
    echo "      kill                                Kill all the Vitis HLS processes for the current user"
    echo "      clean                               Delete the output files"
}

###############
# Main script #
###############

# Read input arguments
MODE=$1
APP=$2
SRC_EXTENSION=$3

# Dispatch based on selected mode
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
    # Show help if invalid or no mode specified
    help
fi
