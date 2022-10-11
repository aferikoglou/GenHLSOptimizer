import os
import json
import time
import argparse
import numpy as np

from pymoo.core.problem import starmap_parallelized_eval
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.factory import get_sampling, get_crossover, get_mutation, get_selection
from pymoo.optimize import minimize
from pymoo.util.termination.default import MultiObjectiveDefaultTermination

from multiprocessing.pool import ThreadPool

from modules.db import DB
from modules.preprocessor import Preprocessor
from modules.hlsDirectiveOptimizationProblem import HLSDirectiveOptimizationProblem

###############
# Main script #
###############

################################
# Parse command line arguments #
################################

parser = argparse.ArgumentParser(description='A script for optimizing high level synthesis kernels using genetic algorithms.')
parser.add_argument('--INPUT_SOURCE_PATH', type=str, required=True, help='The path to the kernel source code that is going to be optimized.')
parser.add_argument('--INPUT_SOURCE_INFO_PATH', type=str, required=True, help='The path to the kernel source code information.')
parser.add_argument('--SRC_EXTENSION', type=str, default=".cpp", help='The source code file extension.')
parser.add_argument('--DB_NAME', type=str, required=True, help='The name of the used database.')
parser.add_argument('--GENERATIONS', type=int, default=24, help='The number of GA generations.')
parser.add_argument('--OPERATOR_CONFIG_PATH', type=str, default="./operator_config/config_01.json", help='The path to the JSON file that contains the genetic algorithm operator configuration.')
parser.add_argument('--THREADS', type=int, default=40, help='The number of used threads.')
parser.add_argument('--TIMEOUT', type=int, default=3600, help='Vitis HLS timeout in seconds.')
parser.add_argument('--DEVICE_ID', type=str, default="xczu7ev-ffvc1156-2-e", help='The target FPGA device id. (default: MPSoC ZCU104)')
parser.add_argument('--CLK_PERIOD', type=str, default="3.33", help='The target FPGA clock period.')

args = parser.parse_args()

INPUT_SOURCE_PATH      = args.INPUT_SOURCE_PATH
INPUT_SOURCE_INFO_PATH = args.INPUT_SOURCE_INFO_PATH
SRC_EXTENSION          = args.SRC_EXTENSION
DB_NAME                = args.DB_NAME
GENERATIONS            = args.GENERATIONS
OPERATOR_CONFIG_PATH   = args.OPERATOR_CONFIG_PATH
THREAD_NUM             = args.THREADS
TIMEOUT                = args.TIMEOUT
DEVICE_ID              = args.DEVICE_ID
CLOCK_PERIOD           = args.CLK_PERIOD

#########################
# Perform preprocessing #
#########################

preprocessor = Preprocessor(INPUT_SOURCE_INFO_PATH)
(n_var, xl, xu, top_level_function, directives) = preprocessor.preprocess()

####################################
# Create/Open application database #
####################################

DB_PATH = os.path.join("./databases_NEW", DB_NAME + ".sqlite")
db = DB(DB_PATH)

##################################################
# HLS directives optimization problem definition #
##################################################

n_threads = THREAD_NUM
pool = ThreadPool(n_threads)
problem = HLSDirectiveOptimizationProblem(
    INPUT_SOURCE_PATH,
    SRC_EXTENSION,
    n_var,
    xl,
    xu,
    top_level_function,
    directives,
    db,
    DEVICE_ID, 
    CLOCK_PERIOD, 
    TIMEOUT, 
    runner=pool.starmap, func_eval=starmap_parallelized_eval
)

########################
# Algorithm definition #
########################

operator_config = {}
with open(OPERATOR_CONFIG_PATH) as f:
    operator_config = json.load(f)

population_size = 40
offsprings = 40
algorithm = NSGA2(
    pop_size=population_size,
    n_offsprings=offsprings,
    sampling=get_sampling(operator_config["sampling"]),
    selection=get_selection(operator_config["selection"]),
    crossover=get_crossover(operator_config["crossover"]),
    mutation=get_mutation(operator_config["mutation"]),
    eliminate_duplicates=True
)

########################
# Termination criteria #
########################

termination = MultiObjectiveDefaultTermination(
    x_tol=1e-8,
    cv_tol=1e-6,
    f_tol=0.0025,
    nth_gen=1,
    n_last=10,
    n_max_gen=GENERATIONS,
    n_max_evals=5000
)

#############
# Execution #
#############

start_time = int(time.time())
res = minimize(problem, algorithm, termination, seed=42, verbose=True)
actual_dse_time = int(time.time()) - start_time
print("Actual DSE Execution Time = " + str(actual_dse_time))

pool.close()

# Analyze and export the database information
db.analyze(TIMEOUT)
db.export()

db.close()

################################
# Create the optimized kernels #
################################

command = 'rm -r ./optimized'
os.system(command)

if res.X.size != 0:
    pareto_optimal_points_num = len(res.X)

    OPTIMIZED_DIR = "./optimized"
    command = 'mkdir -p ' + OPTIMIZED_DIR
    os.system(command)

    f = open(os.path.join(OPTIMIZED_DIR, 'info.csv'), 'w')
    f.write("name, latency, bram_util, dsp_util, ff_util, lut_util, uram_util\n")
    
    for i in range(pareto_optimal_points_num):
        X = list(res.X[i])
        F = list(res.F[i])

        Y = problem.convert_indices_to_directives(directives, X)

        name = "optimized_" + str(i + 1) + SRC_EXTENSION
        OUTPUT_SOURCE_PATH = os.path.join(OPTIMIZED_DIR, name)
        problem.apply_directives(INPUT_SOURCE_PATH, OUTPUT_SOURCE_PATH, Y)

        f.write(str(name) + ', ' + str(F[0]) + ', ' + str(F[1]) + ', ' + str(F[2]) + ', ' + str(F[3]) + ', ' + str(F[4]) + ', ' + str(F[5]) + '\n')

    f.close()
else:
    print("The genetic algorithm WAS NOT able to provide Pareto Optimal configurations.")
    
#########################
# Delete the DSE output #
#########################

command = 'rm -r GENETIC_DSE_*'
os.system(command)
command = 'rm kernel_*' + SRC_EXTENSION
os.system(command)
command = 'rm script_*.tcl'
os.system(command)
command = 'rm vitis_hls_*.log'
os.system(command)