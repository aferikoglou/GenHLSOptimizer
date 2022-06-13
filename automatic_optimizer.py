import os
import sys
import json
import time
import psutil
import argparse
import subprocess
import numpy as np
import multiprocessing

from pymoo.core.problem import ElementwiseProblem
from pymoo.core.problem import starmap_parallelized_eval
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.factory import get_sampling, get_crossover, get_mutation, get_selection
from pymoo.factory import get_termination
from pymoo.optimize import minimize
from pymoo.util.termination.default import MultiObjectiveDefaultTermination
from pymoo.core.callback import Callback

from os.path import exists
from multiprocessing.pool import ThreadPool
from threading import Lock

from modules.db import DB
from modules.preprocessor import Preprocessor

#####################
# Utility functions #
#####################

def mkdir_p(OUTPUT_DIR):
	command = 'mkdir -p ' + OUTPUT_DIR

	os.system(command)

def get_var_domains(directives):
	# xl creation
	directives_len = len(directives)

	xl = np.zeros(directives_len, dtype=int)

	# xu creation
	xu_list = []

	cnt = 0
	for i in directives:
		length = len(i)
		xu_list.insert(cnt, length - 1)
		cnt += 1

	xu = np.asarray(xu_list)

	return (xl, xu)

def get_total_dse_time(pop_size, conf, db):
	counter = 0
	total_dse_time = 0
	generation_time = 0
	for x in conf:
		generation_time = max(generation_time, db.get_synth_time(x))

		counter += 1

		if counter % pop_size == 0:
			total_dse_time += generation_time
			generation_time = 0
	# print(counter)
	return total_dse_time

###############
# Main script #
###############

################################
# Parse command line arguments #
################################

parser = argparse.ArgumentParser(description='A script for optimizing high level synthesis kernels using genetic algorithms.')
parser.add_argument('--INPUT_SOURCE_PATH', type=str, required=True, help='The path to the kernel source code that is going to be optimized.')
parser.add_argument('--INPUT_SOURCE_INFO_PATH', type=str, required=True, help='The path to the kernel source code information.')
parser.add_argument('--DB_NAME', type=str, required=True, help='The name of the used database.')
parser.add_argument('--GENERATIONS', type=int, default=24, help='The number of GA generations.')
parser.add_argument('--THREADS', type=int, default=40, help='The number of used threads.')
parser.add_argument('--TIMEOUT', type=int, default=3600, help='Vitis HLS timeout in seconds.')
parser.add_argument('--DEVICE_ID', type=str, default="xczu7ev-ffvc1156-2-e", help='The target FPGA device id. (default: MPSoC ZCU104)')
parser.add_argument('--CLK_PERIOD', type=str, default="3.33", help='The target FPGA clock period.')
parser.add_argument('--OPERATOR_CONFIG_PATH', type=str, default="./operator_config/config_01.json", help='The path to the JSON file that contains the genetic algorithm operator configuration.')

args = parser.parse_args()

INPUT_SOURCE_PATH = args.INPUT_SOURCE_PATH
INPUT_SOURCE_INFO_PATH = args.INPUT_SOURCE_INFO_PATH
DB_NAME = args.DB_NAME

timeout = args.TIMEOUT
generations = args.GENERATIONS
thread_num = args.THREADS
device_id = args.DEVICE_ID
clock_period = args.CLK_PERIOD
OPERATOR_CONFIG_PATH = args.OPERATOR_CONFIG_PATH
operator_config = {}
with open(OPERATOR_CONFIG_PATH) as f:
	operator_config = json.load(f)

preprocessor = Preprocessor(INPUT_SOURCE_INFO_PATH)
(n_var, top_level_function, directives) = preprocessor.preprocess()

DB_PATH = os.path.join("./databases", DB_NAME + ".sqlite")
db = DB(DB_PATH)
# db.print()

(xl, xu) = get_var_domains(directives)

################################

i = 0
count = 0
# conf list keeps all the examined configurations for the DSE execution time calculation
conf = []
lock = Lock()

class HLSDirectiveOptimizationProblem(ElementwiseProblem):
	def __init__(self, **kwargs):
		super().__init__(n_var=n_var, n_obj=6, n_constr=5, xl=xl, xu=xu, type_var=int, **kwargs)

	def convert_indices_to_directives(self, directives, X):
		directive_list = []

		X_len = len(X)
		for i in range(X_len):
			directive = directives[i][X[i]]
			directive_list.insert(i, directive)

		return directive_list
	
	def apply_directives(self, INPUT_FILE_PATH, OUTPUT_FILE_PATH, X):
		fr = open(INPUT_FILE_PATH, 'r')
		fw = open(OUTPUT_FILE_PATH, 'w')

		cnt = 1
		for line in fr:
			stripped_line = line.replace(' ', '').replace('\n', '').replace('\t', '')

			pattern = 'L' + str(cnt)
			if pattern in stripped_line:
				fw.write(line)
				added_directive = X[cnt - 1] + '\n'
				fw.write(added_directive)
				cnt += 1
				continue
		
			fw.write(line)
		
		fw.close()
		fr.close()

	def _create_tcl(self, TCL_SCRIPT_PATH, project_name, top_level_function, source_code_path, device_id, clock_period, vitis_opts):
		with open(TCL_SCRIPT_PATH, "w") as outFile:
			outFile.write("""open_project """ + project_name + '\n')
			outFile.write("""set_top """ + top_level_function + '\n')
			outFile.write("""add_files """ + source_code_path + '\n')
			outFile.write("""open_solution "solution1" -flow_target vivado""" + '\n')
			outFile.write("""set_part {""" + device_id + """}""" + '\n')
			outFile.write("""create_clock -period """ + clock_period + """ -name default""" + '\n')

			if not(vitis_opts):
				outFile.write("""config_array_partition -complete_threshold 0 -throughput_driven off""" + '\n')
				outFile.write("""config_compile -pipeline_loops 0""" + '\n')

			outFile.write("""csynth_design""" + '\n')
			outFile.write("""export_design -format ip_catalog""" + '\n')
			outFile.write("""exit""")

	def _synthesize(self, x):
		global i

		##########################################
		# Run Vitis High Level Synthesis command #
		##########################################

		lock.acquire()

		i += 1
		my_i = i
		
		OUTPUT_SOURCE_PATH = os.path.join("./", "kernel_" + str(my_i) + ".cpp")
		TCL_SCRIPT_PATH = os.path.join("./", "script_" + str(my_i) + ".tcl")
		VITIS_LOG_PATH = os.path.join("./", "vitis_hls_" + str(my_i) + ".log")

		y = self.convert_indices_to_directives(directives, x)
		self.apply_directives(INPUT_SOURCE_PATH, OUTPUT_SOURCE_PATH, y)
		self._create_tcl(TCL_SCRIPT_PATH, "GENETIC_DSE_" + str(my_i), top_level_function, OUTPUT_SOURCE_PATH, device_id, clock_period, False)
		
		p = subprocess.Popen(['vitis_hls', '-f', TCL_SCRIPT_PATH, '-l', VITIS_LOG_PATH])    

		lock.release()

		start_time = int(time.time())
		finished = False
		while (True):
			total_time = int(time.time()) - start_time
			if(total_time >= timeout or p.poll() != None):
				if(p.poll() != None):
					finished = True
					print("Finished !")		
				try:
					process = psutil.Process(p.pid)
					for proc in process.children(recursive=True):
						proc.kill()
					process.kill()
					kill_count = kill_count + 1
				except:
					print("Either failed to terminate or already terminated !")
				break

		###################
		# Get QoR metrics #
		###################

		if(finished == False):
			return [0, 101, 101, 101, 101, 101]

		try:
			temp = open(f'GENETIC_DSE_{my_i}/solution1/solution1_data.json','r')
		except:
			return [0, 101, 101, 101, 101, 101]

		json_import = json.load(temp)
		
		latency = int(json_import["ClockInfo"]["Latency"])
		period = float(json_import["ClockInfo"]["ClockPeriod"])

		latency = (latency * period) / 1000000

		available = json_import['ModuleInfo']['Metrics'][top_level_function]['Area']

		temp = available["UTIL_BRAM"]
		if temp[0]!= '~':
			util_bram = int(temp)
		else:
			util_bram = 0

		temp = available["UTIL_DSP"]
		if temp[0]!= '~':
			util_dsp = int(temp)
		else:
			util_dsp = 0

		temp = available["UTIL_FF"]
		if temp[0]!= '~':
			util_ff = int(temp)
		else:
			util_ff = 0

		temp = available["UTIL_LUT"]
		if temp[0]!= '~':
			util_lut = int(temp)
		else:
			util_lut = 0

		temp = available["UTIL_URAM"]
		if temp[0]!= '~':
			util_uram = int(temp)
		else:
			util_uram = 0

		#################
		# Delete output #
		#################

		command = 'rm -r GENETIC_DSE_' + str(my_i)
		os.system(command)
		command = 'rm ' + os.path.join("./", 'kernel_' + str(my_i) + '.cpp')
		os.system(command)
		command = 'rm ' + os.path.join("./", 'script_' + str(my_i) + '.tcl')
		os.system(command)
		command = 'rm ' + os.path.join("./", 'vitis_hls_' + str(my_i) + '.log')
		os.system(command)

		return [latency, util_bram, util_dsp, util_ff, util_lut, util_uram]

	def _evaluate(self, x, out, *args, **kwargs):
		metrics = None
		# print(x)

		global count

		lock.acquire()

		conf.insert(count, x)
		count += 1

		lock.release()

		try:
			metrics = db.get(x)
			# print("Found " + str(x) + " configuration in DB")		
		except:
			# print("Could not find " + str(x) + " configuration in DB. Starting synthesis...")
			
			start = int(time.time())
			metrics = self._synthesize(x)
			synth_time = int(time.time()) - start
			
			metrics_len = len(metrics)
			metrics.insert(metrics_len, synth_time)
			db.insert(x, metrics)

		d = np.array(metrics)
		
		f = d[0:6]
		g = f[1:6] - 100

		out["F"] = f
		out["G"] = g

######################
# Problem definition #
######################

n_threads = thread_num
pool = ThreadPool(n_threads)
problem = HLSDirectiveOptimizationProblem(runner=pool.starmap, func_eval=starmap_parallelized_eval)

########################
# Algorithm definition #
########################

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
	n_max_gen=generations,
	n_max_evals=5000
)

#############
# Execution #
#############

start_time = int(time.time())

res = minimize(problem, algorithm, termination, seed=1, verbose=True)

actual_dse_time = int(time.time()) - start_time
print("Actual DSE Execution Time = " + str(actual_dse_time))

# print(res.X)
# print(res.F)

calculated_dse_time = get_total_dse_time(population_size, conf, db)
print("Calculated DSE Execution Time = " + str(calculated_dse_time))

pool.close()
db.close()

################################
# Create the optimized kernels #
################################

command = 'rm -r ./optimized'
os.system(command)
OPTIMIZED_DIR = "./optimized"
mkdir_p(OPTIMIZED_DIR)

f = open(os.path.join(OPTIMIZED_DIR, 'info.csv'), 'w')
f.write("name, latency, bram_util, dsp_util, ff_util, lut_util, uram_util\n")

pareto_optimal_points_num = len(res.X)
for i in range(pareto_optimal_points_num):
	X = list(res.X[i])
	F = list(res.F[i])
	Y = problem.convert_indices_to_directives(directives, X)
	name = "optimized_" + str(i + 1) + ".cpp"
	OUTPUT_SOURCE_PATH = os.path.join(OPTIMIZED_DIR, name)
	problem.apply_directives(INPUT_SOURCE_PATH, OUTPUT_SOURCE_PATH, Y)

	f.write(str(name) + ', ' + str(F[0]) + ', ' + str(F[1]) + ', ' + str(F[2]) + ', ' + str(F[3]) + ', ' + str(F[4]) + ', ' + str(F[5]) + '\n')

f.close()
	
#########################
# Delete the DSE output #
#########################

command = 'rm -r GENETIC_DSE_*'
os.system(command)
command = 'rm kernel_*.cpp'
os.system(command)
command = 'rm script_*.tcl'
os.system(command)
command = 'rm vitis_hls_*.log'
os.system(command)

