import json

from sqlitedict import SqliteDict

class DB():
	def __init__(self, db_path):
		self.db_path = db_path

		parts = db_path.split('/')
		size = len(parts)
		self.db_name = parts[size - 1].split('.')[0]
		
		self.db = SqliteDict(db_path)

		self.synth_total = 0
		self.synth_timeout = 0
		self.synth_failed = 0
		self.synth_success = 0
		self.synth_success_no_feasible = 0
		self.synth_success_feasible = 0
		self.synth_latency_undef = 0

	def get(self, x):
		key = str(x)
		temp = self.db[key]
		val = [temp["latency"], temp["util_bram"], temp["util_dsp"], temp["util_ff"], temp["util_lut"], temp["util_uram"], temp["synth_time"]]

		return val

	def get_synth_time(self, x):
		key = str(x)
		temp = self.db[key]
		val = temp["synth_time"]

		return val

	def insert(self, x, val):
		key = str(x)
		self.db[key] = {"latency": val[0], "util_bram": val[1], "util_dsp": val[2], "util_ff": val[3], "util_lut": val[4], "util_uram": val[5], "synth_time": val[6]}
		self.db.commit()

	def print(self):
		for key, item in self.db.items():
			print("%s = %s" % (key, item))

	def analyze(self, timeout):
		for key, item in self.db.items():
			latency    = item["latency"]
			util_bram  = item["util_bram"]
			util_dsp   = item["util_dsp"]
			util_ff    = item["util_ff"]
			util_lut   = item["util_lut"]
			util_uram  = item["util_uram"]
			synth_time = item["synth_time"]

			if (latency == 0 and util_bram == 101 and util_dsp == 101 and util_ff == 101 and util_lut == 101 and util_uram == 101):
				if (synth_time >= timeout):
					self.synth_timeout += 1
				else:
					self.synth_failed += 1
			elif (util_bram > 101 or util_dsp > 101 or util_ff > 101 or util_lut > 101 or util_uram > 101):
				self.synth_success_no_feasible += 1
			else:
				self.synth_success_feasible += 1

			# Check if latency is undef
			if (latency == 1000000):
				self.synth_latency_undef += 1
						
			self.synth_total += 1

		# print(synth_total)
		# print(synth_timeout)
		# print(synth_failed)
		# print(synth_success)

		print("")
		print("Database Analytics")
		print("")
		print("Database Path=%s" % self.db_path)
		print("")
		print("#synthesis total = %s" % self.synth_total)
		print("")

		self.synth_success = self.synth_success_feasible + self.synth_success_no_feasible
		if self.synth_total != 0:
			synth_timeout_perc = (float(self.synth_timeout) / self.synth_total) * 100
			synth_failed_perc = (float(self.synth_failed) / self.synth_total) * 100
			synth_success_perc = (float(self.synth_success) / self.synth_total) * 100

			print("Synthesis timeout percentage = %f (%s)" % (synth_timeout_perc, self.synth_timeout))
			print("Synthesis failed percentage  = %f (%s)" % (synth_failed_perc, self.synth_failed))
			print("Synthesis success total percentage = %f (%s)" % (synth_success_perc, self.synth_success))
		
		if self.synth_success != 0:
			synth_success_feasible_perc = (float(self.synth_success_feasible) / self.synth_success) * 100
			synth_success_no_feasible_perc = (float(self.synth_success_no_feasible) / self.synth_success) * 100

			print("- Synthesis feasible percentage = %f (%s)" % (synth_success_feasible_perc, self.synth_success_feasible))
			print("- Synthesis non feasible percentage = %f (%s)" % (synth_success_no_feasible_perc, self.synth_success_no_feasible))
		
		print("")
	
	def export(self):
		output_map = {}

		output_map["synth_total"] = self.synth_total
		output_map["synth_timeout"] = self.synth_timeout
		output_map["synth_failed"] = self.synth_failed
		output_map["synth_success"] = self.synth_success
		output_map["synth_success_no_feasible"] = self.synth_success_no_feasible
		output_map["synth_success_feasible"] = self.synth_success_feasible
		output_map["synth_latency_undef"] = self.synth_latency_undef

		ouput_file_name = self.db_name + '.json'
		with open(ouput_file_name, 'w') as f:
			json.dump(output_map, f, indent = 4, sort_keys = True)

	def close(self):
		self.db.close()

