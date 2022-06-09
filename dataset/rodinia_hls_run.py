import os
import json
import time
import psutil
import subprocess

class Experiment:
	def __init__(self, dirPath, srcFileName, topLevelFunc, device, period):
		self.dirPath           = dirPath
		self.srcFileName       = srcFileName
		self.topLevelFunc      = topLevelFunc
		self.device            = device
		self.period            = period
		self.srcCode           = []
		self.experimentResults = {}
		# runningTime defines the time we wait to synthesize the kernel using Vitis HLS
		self.runningTime       = 3600 # 1 hour
		# timeIncrement defines how often do we check whether the vitis_hls process is finished
		self.timeIncrement     = 5 # 5 sec
		self.outputDir         = device + "_" + period

		# Create output directory which consists of the part id of the target device and the target clock period
		command = 'mkdir -p ' + os.path.join(self.dirPath, self.outputDir)
		print(command)
		os.system(command)

	def __readCode(self):
		with open(os.path.join(self.dirPath, self.srcFileName), "r") as inFile:
			self.srcCode = inFile.readlines()

	def __removeDirectives(self):
		with open(os.path.join(self.dirPath, "noDirectives.cpp"), "w") as outFile:
			for line in self.srcCode:
				if not("#pragma HLS" in line):
					outFile.write(line)

	def __createTCL(self, projectName, srcPath, vitisOpts):
		with open("script.tcl", "w") as outFile:
			outFile.write("""open_project """ + projectName + '\n')
			outFile.write("""set_top """ + self.topLevelFunc + '\n')
			outFile.write("""add_files """ + srcPath + '\n')
			outFile.write("""open_solution "solution1" -flow_target vivado""" + '\n')
			outFile.write("""set_part {""" + self.device + """}""" + '\n')
			outFile.write("""create_clock -period """ + self.period + """ -name default""" + '\n')

			if not(vitisOpts):
				outFile.write("""config_array_partition -auto_partition_threshold 0 -auto_promotion_threshold 0""" + '\n')
				outFile.write("""config_compile -pipeline_loops 0""" + '\n')

			outFile.write("""csynth_design""" + '\n')
			outFile.write("""export_design -format ip_catalog""" + '\n')
			outFile.write("""exit""")

	def __synthesize(self):
		p = subprocess.Popen(['vitis_hls', '-f', 'script.tcl', '-l', 'vitis_hls.log'])

		totalTime = 0
		finished = False
		while (True):
			time.sleep(self.timeIncrement)

			totalTime += self.timeIncrement
			if(totalTime >= self.runningTime or p.poll() != None):
				if(p.poll() != None):
					finished = True
				pid = p.pid

				try:
					for child in psutil.Process(pid).children(recursive = True):
						child.kill()
					p.kill()
				except:
					print("Either failed to terminate or already terminated")
				break

	def __getResults(self, projectName):
		resultMap = {}

		try:
			x = open(projectName + '/solution1/solution1_data.json','r')
		except:
			print("No synthesis data were provided")
			return resultMap
    
		json_import = json.load(x)
        
		try:
			latency = int(json_import["ClockInfo"]["Latency"])
		except:
			latency = -1
			print("Undefined latency")

		period = float(json_import["ClockInfo"]["ClockPeriod"])

		latency = (latency * period) / 1000000

		available = json_import['ModuleInfo']['Metrics'][self.topLevelFunc]['Area']
        
		x = available["UTIL_BRAM"]
		if x[0] != '~':
			util_bram = int(x)
		else:
			util_bram = 0

		x = available["UTIL_DSP"]
		if x[0] != '~':
			util_dsp = int(x)
		else:
			util_dsp = 0

		x = available["UTIL_FF"]
		if x[0] != '~':
			util_ff = int(x)
		else:
			util_ff = 0

		x = available["UTIL_LUT"]
		if x[0] != '~':
			util_lut = int(x)
		else:
			util_lut = 0

		resultMap['latency']   = latency
		resultMap['util_bram'] = util_bram
		resultMap['util_dsp']  = util_dsp
		resultMap['util_ff']   = util_ff
		resultMap['util_lut']  = util_lut

		return resultMap

	def __mvOutput(self, projectName):
		command = 'mv ' + projectName + ' ' + os.path.join(self.dirPath, self.outputDir)
		print(command)
		os.system(command)

		command = 'mv ./script.tcl ' + os.path.join(self.dirPath, self.outputDir, projectName)
		print(command)
		os.system(command)
	
		command = 'mv ./vitis_hls.log ' + os.path.join(self.dirPath, self.outputDir, projectName)
		print(command)
		os.system(command)


	def __writeExperimentResults(self):
		with open(os.path.join(self.dirPath, self.outputDir, "output.json"), "w") as outFile:
			json.dump(self.experimentResults, outFile, indent = 4, sort_keys = True)

	def run(self):
		self.__readCode()
		self.__removeDirectives()
		
		for original in [True, False]:
			name = "original" if original else "no_directives"
			srcPath = os.path.join(self.dirPath, self.srcFileName) if original else os.path.join(self.dirPath, "noDirectives.cpp")

			for vitisOpts in [True, False]:
				totalSynthTime = 0

				projectName = name + "_wVO" if vitisOpts else name + "_woVO"

				self.__createTCL(projectName, srcPath, vitisOpts)

				start = time.time()
				self.__synthesize()
				end = time.time()
				totalSynthTime = end - start

				self.experimentResults[projectName] = self.__getResults(projectName)
				self.experimentResults[projectName]["totalSynthTime"] = totalSynthTime

				self.__mvOutput(projectName)

		self.__writeExperimentResults()

PATH_TO_RODINIA_HLS_DIR = './rodinia_hls'
BENCHS = ['backprop', 'backprop_forward', 'cfd_step_factor', 'hotspot', 'kmeans', 'knn', 'lc_dilate', 'lc_mgvf', 'pathfinder', 'srad', 'streamcluster']
DEVICE = 'xczu9eg-ffvb1156-2-e'
PERIOD = '3.33'

for bench in BENCHS:
	PATH_TO_BENCH_DIR = os.path.join(PATH_TO_RODINIA_HLS_DIR, bench)
	for f in os.listdir(PATH_TO_BENCH_DIR):
		fname = os.fsdecode(f)
		if (fname.endswith(".c") or fname.endswith(".cpp")) and fname != "noDirectives.cpp":
			experiment = Experiment(PATH_TO_BENCH_DIR, fname, "workload", DEVICE, PERIOD)
			experiment.run()

