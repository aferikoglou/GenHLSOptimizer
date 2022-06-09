from sqlitedict import SqliteDict

class DB():
	def __init__(self, db_name):
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

	def close(self):
		self.db.close()

