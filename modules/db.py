from sqlitedict import SqliteDict

class DB():
	def __init__(self, db_name):
		self.db_name = db_name
		self.db = SqliteDict(db_name)

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
		synth_total = 0
		synth_timeout = 0
		synth_failed = 0
		synth_success = 0
		synth_success_no_feasible = 0
		synth_success_feasible = 0
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
					synth_timeout += 1
				else:
					synth_failed += 1
			elif (util_bram > 101 or util_dsp > 101 or util_ff > 101 or util_lut > 101 or util_uram > 101):
				synth_success_no_feasible += 1
			else:
				synth_success_feasible += 1
						
			synth_total += 1

		# print(synth_total)
		# print(synth_timeout)
		# print(synth_failed)
		# print(synth_success)

		synth_success = synth_success_feasible + synth_success_no_feasible

		synth_timeout_perc = (float(synth_timeout) / synth_total) * 100
		synth_failed_perc = (float(synth_failed) / synth_total) * 100
		synth_success_perc = (float(synth_success) / synth_total) * 100
		synth_success_feasible_perc = (float(synth_success_feasible) / synth_success) * 100
		synth_success_no_feasible_perc = (float(synth_success_no_feasible) / synth_success) * 100

		print("#####")
		print("Database Analytics")
		print("")
		print("Database Path=%s" % self.db_name)
		print("")
		print("#synthesis total = %s" % synth_total)
		print("")
		print("Synthesis timeout percentage = %f (%s)" % (synth_timeout_perc, synth_timeout))
		print("Synthesis failed percentage  = %f (%s)" % (synth_failed_perc, synth_failed))
		print("Synthesis success total percentage = %f (%s)" % (synth_success_perc, synth_success))
		print("- Synthesis feasible percentage = %f (%s)" % (synth_success_feasible_perc, synth_success_feasible))
		print("- Synthesis non feasible percentage = %f (%s)" % (synth_success_no_feasible_perc, synth_success_no_feasible))
		print("#####")
		

	def close(self):
		self.db.close()

