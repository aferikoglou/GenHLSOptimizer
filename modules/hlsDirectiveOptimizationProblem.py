import os
import time
import json
import psutil
import subprocess

import numpy as np

from pymoo.core.problem import ElementwiseProblem

from threading import Lock

class HLSDirectiveOptimizationProblem(ElementwiseProblem):
    """
    A PyMoo-compatible multi-objective optimization problem for exploring HLS directive configurations.
    
    This class evaluates combinations of HLS directives on a given source file using Vitis HLS, 
    extracting performance and resource utilization metrics for optimization.
    """
    
    def __init__(self, INPUT_SOURCE_PATH, src_extension, n_var, xl, xu, top_level_function, directives, db, device_id, clock_period, timeout, **kwargs):
        """
        Initialize the optimization problem with design metadata and search bounds.

        Args:
            INPUT_SOURCE_PATH (str): Path to the base input source file.
            src_extension (str): Source file extension (e.g., ".cpp", ".c").
            n_var (int): Number of optimization variables (action points).
            xl (array): Lower bounds for each variable.
            xu (array): Upper bounds for each variable.
            top_level_function (str): Name of the top-level function for synthesis.
            directives (list): List of directive options per action point.
            db (object): Database object to cache previous synthesis results.
            device_id (str): FPGA part/device identifier (e.g., "xcu250-figd2104-2L-e").
            clock_period (str): Desired clock period for HLS (e.g., "10").
            timeout (int): Maximum synthesis time per evaluation (in seconds).
            **kwargs: Additional arguments for the ElementwiseProblem superclass.
        """
        self.INPUT_SOURCE_PATH = INPUT_SOURCE_PATH
        self.SRC_EXTENSION = src_extension

        self.DB = db
        self.DIRECTIVES = directives

        self.TOP_LEVEL_FUNCTION = top_level_function
        self.DEVICE_ID = device_id
        self.CLOCK_PERIOD = clock_period
        self.TIMEOUT = timeout

        self.i = 0
        self.lock = Lock()
       
        super().__init__(n_var=n_var, n_obj=6, n_constr=5, xl=xl, xu=xu, type_var=int, **kwargs)

    def convert_indices_to_directives(self, directives, X):
        """
        Convert a list of indices into their corresponding HLS directives.

        Args:
            directives (list): List of directive sets per action point.
            X (list): List of chosen directive indices.

        Returns:
            list: List of selected HLS directive strings.
        """
        directive_list = []

        X_len = len(X)
        for i in range(X_len):
            directive = directives[i][X[i]]
            directive_list.insert(i, directive)

        return directive_list
    
    def apply_directives(self, INPUT_FILE_PATH, OUTPUT_FILE_PATH, X):
        """
        Apply selected HLS directives to a copy of the input source file.

        Args:
            INPUT_FILE_PATH (str): Path to the original source file.
            OUTPUT_FILE_PATH (str): Path where the modified file will be saved.
            X (list): List of directive strings to apply.
        """
        fr = open(INPUT_FILE_PATH, 'r')
        fw = open(OUTPUT_FILE_PATH, 'w')

        count = 1
        for line in fr:
            stripped_line = line.replace(' ', '').replace('\n', '').replace('\t', '')

            pattern = 'L' + str(count)
            if pattern in stripped_line:
                fw.write(line)
                added_directive = X[count - 1] + '\n'
                fw.write(added_directive)
                count += 1
                continue
        
            fw.write(line)
        
        fw.close()
        fr.close()

    def _create_tcl(self, TCL_SCRIPT_PATH, project_name, top_level_function, source_code_path, device_id, clock_period, vitis_opts):
        """
        Generate a TCL script to run synthesis in Vitis HLS.

        Args:
            TCL_SCRIPT_PATH (str): Path to output TCL file.
            project_name (str): Name of the synthesis project.
            top_level_function (str): Top-level function to synthesize.
            source_code_path (str): Path to the HLS source file.
            device_id (str): FPGA device identifier.
            clock_period (str): Clock constraint for synthesis.
            vitis_opts (bool): Whether to include Vitis-specific config options.
        """
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
        """
        Run the HLS synthesis flow using the provided directive vector.

        Args:
            x (list): A directive index vector.

        Returns:
            list: A list of performance and resource metrics.
        """
        self.lock.acquire()

        self.i += 1
        my_i = self.i
        
        OUTPUT_SOURCE_PATH = os.path.join("./", "kernel_" + str(my_i) + self.SRC_EXTENSION)
        TCL_SCRIPT_PATH = os.path.join("./", "script_" + str(my_i) + ".tcl")
        VITIS_LOG_PATH = os.path.join("./", "vitis_hls_" + str(my_i) + ".log")

        y = self.convert_indices_to_directives(self.DIRECTIVES, x)
        self.apply_directives(self.INPUT_SOURCE_PATH, OUTPUT_SOURCE_PATH, y)
        self._create_tcl(TCL_SCRIPT_PATH, "GENETIC_DSE_" + str(my_i), self.TOP_LEVEL_FUNCTION, OUTPUT_SOURCE_PATH, self.DEVICE_ID, self.CLOCK_PERIOD, False)
        
        p = subprocess.Popen(['vitis_hls', '-f', TCL_SCRIPT_PATH, '-l', VITIS_LOG_PATH])    

        self.lock.release()

        start_time = int(time.time())
        finished = False
        while (True):
            total_time = int(time.time()) - start_time
            if(total_time >= self.TIMEOUT or p.poll() != None):
                if(p.poll() != None):
                    finished = True
                    print("Finished !")		
                try:
                    process = psutil.Process(p.pid)
                    for proc in process.children(recursive=True):
                        proc.kill()
                    process.kill()
                except:
                    print("Either failed to terminate or already terminated !")
                break

        if(finished == False):
            return [0, 101, 101, 101, 101, 101]

        try:
            temp = open(f'GENETIC_DSE_{my_i}/solution1/solution1_data.json','r')
        except:
            return [0, 101, 101, 101, 101, 101]

        json_import = json.load(temp)
        
        # Handle the latency undef case
        latency = None
        period = None
        try:
            latency = int(json_import["ClockInfo"]["Latency"])
            period = float(json_import["ClockInfo"]["ClockPeriod"])
        except:
            latency = 1000000
            period = 1000000

        latency = (latency * period) / 1000000

        available = json_import['ModuleInfo']['Metrics'][self.TOP_LEVEL_FUNCTION]['Area']

        temp = available["UTIL_BRAM"]
        util_bram = int(temp) if temp[0] != '~' else 0

        temp = available["UTIL_DSP"]
        util_dsp = int(temp) if temp[0] != '~' else 0

        temp = available["UTIL_FF"]
        util_ff = int(temp) if temp[0] != '~' else 0

        temp = available["UTIL_LUT"]
        util_lut = int(temp) if temp[0] != '~' else 0

        temp = available["UTIL_URAM"]
        util_uram = int(temp) if temp[0] != '~' else 0

        # Clean up generated files
        os.system(f'rm -r GENETIC_DSE_{my_i}')
        os.system(f'rm ./kernel_{my_i}{self.SRC_EXTENSION}')
        os.system(f'rm ./script_{my_i}.tcl')
        os.system(f'rm ./vitis_hls_{my_i}.log')

        return [latency, util_bram, util_dsp, util_ff, util_lut, util_uram]

    def _evaluate(self, x, out, *args, **kwargs):
        """
        Evaluate a solution vector by synthesizing it (or retrieving from DB) and 
        returning its fitness and constraint violations.

        Args:
            x (list): Design vector of directive indices.
            out (dict): Dictionary to store evaluation results (objectives and constraints).
        """
        metrics = None

        try:
            metrics = self.DB.get(x)
        except:
            start = int(time.time())
            metrics = self._synthesize(x)
            synth_time = int(time.time()) - start
            metrics_len = len(metrics)
            metrics.insert(metrics_len, synth_time)
            self.DB.insert(x, metrics)

        d = np.array(metrics)
        
        f = d[0:6]
        g = f[1:6] - 100

        out["F"] = f
        out["G"] = g
