import os
import time
import json
import psutil
import subprocess

import numpy as np

from pymoo.core.problem import ElementwiseProblem

from threading import Lock

class HLSDirectiveOptimizationProblem(ElementwiseProblem):
    def __init__(self, INPUT_SOURCE_PATH, src_extension, n_var, xl, xu, top_level_function, directives, db, device_id, clock_period, timeout, **kwargs):
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
        directive_list = []

        X_len = len(X)
        for i in range(X_len):
            directive = directives[i][X[i]]
            directive_list.insert(i, directive)

        return directive_list
    
    def apply_directives(self, INPUT_FILE_PATH, OUTPUT_FILE_PATH, X):
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

        ##########################################
        # Run Vitis High Level Synthesis command #
        ##########################################

        self.lock.acquire()

        self.i += 1
        my_i = self.i
        
        OUTPUT_SOURCE_PATH = os.path.join("./", "kernel_" + str(my_i) + self.SRC_EXTENSION)
        TCL_SCRIPT_PATH = os.path.join("./", "script_" + str(my_i) + ".tcl")
        VITIS_LOG_PATH = os.path.join("./", "vitis_hls_" + str(my_i) + ".log")

        y = self._convert_indices_to_directives(self.DIRECTIVES, x)
        self._apply_directives(self.INPUT_SOURCE_PATH, OUTPUT_SOURCE_PATH, y)
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
        
        # Handle the latency undef case
        latency = None
        period = None
        try:
            latency = int(json_import["ClockInfo"]["Latency"])
            period = float(json_import["ClockInfo"]["ClockPeriod"])
        except:
            # Identify the latency undef case using a magic number
            latency = 1000000
            period = 1000000

        latency = (latency * period) / 1000000

        available = json_import['ModuleInfo']['Metrics'][self.TOP_LEVEL_FUNCTION]['Area']

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
        command = 'rm ' + os.path.join("./", 'kernel_' + str(my_i) + self.SRC_EXTENSION)
        os.system(command)
        command = 'rm ' + os.path.join("./", 'script_' + str(my_i) + '.tcl')
        os.system(command)
        command = 'rm ' + os.path.join("./", 'vitis_hls_' + str(my_i) + '.log')
        os.system(command)

        return [latency, util_bram, util_dsp, util_ff, util_lut, util_uram]

    def _evaluate(self, x, out, *args, **kwargs):
        metrics = None
        # print(x)

        try:
            metrics = self.DB.get(x)
            # print("Found " + str(x) + " configuration in DB")		
        except:
            # print("Could not find " + str(x) + " configuration in DB. Starting synthesis...")
            
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