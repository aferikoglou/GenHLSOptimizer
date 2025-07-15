import json
from sqlitedict import SqliteDict

class DB():
    """
    A wrapper class around SqliteDict to manage and analyze High-Level Synthesis (HLS) results.
    Stores synthesis metrics such as latency, resource utilization, and synthesis time.
    """

    def __init__(self, db_path):
        """
        Initialize the database interface.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path

        parts = db_path.split('/')
        size = len(parts)
        self.db_name = parts[size - 1].split('.')[0]
        
        self.db = SqliteDict(db_path)

        # Synthesis statistics counters
        self.synth_total = 0
        self.synth_timeout = 0
        self.synth_failed = 0
        self.synth_success = 0
        self.synth_success_no_feasible = 0
        self.synth_success_feasible = 0
        self.synth_latency_undef = 0

    def get(self, x):
        """
        Retrieve synthesis results for a specific key.

        Args:
            x: Key used in the database.

        Returns:
            list: [latency, bram, dsp, ff, lut, uram, synth_time]
        """
        key = str(x)
        temp = self.db[key]
        val = [temp["latency"], temp["util_bram"], temp["util_dsp"], temp["util_ff"], temp["util_lut"], temp["util_uram"], temp["synth_time"]]
        return val

    def get_synth_time(self, x):
        """
        Get only the synthesis time for a specific key.

        Args:
            x: Key used in the database.

        Returns:
            float: Synthesis time in seconds.
        """
        key = str(x)
        temp = self.db[key]
        val = temp["synth_time"]
        return val

    def insert(self, x, val):
        """
        Insert synthesis results into the database.

        Args:
            x: Key for the entry.
            val (list): Values [latency, bram, dsp, ff, lut, uram, synth_time].
        """
        key = str(x)
        self.db[key] = {"latency": val[0], "util_bram": val[1], "util_dsp": val[2], "util_ff": val[3], "util_lut": val[4], "util_uram": val[5], "synth_time": val[6]}
        self.db.commit()

    def print(self):
        """
        Print all entries in the database.
        """
        for key, item in self.db.items():
            print("%s = %s" % (key, item))

    def analyze(self, timeout):
        """
        Analyze the database and compute synthesis statistics.

        Args:
            timeout (int): Timeout threshold in seconds for synthesis.
        """
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

            if (latency == 1000000):
                self.synth_latency_undef += 1
                        
            self.synth_total += 1

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
        """
        Export the analysis summary as a JSON file using the database name.
        """
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
        """
        Close the database.
        """
        self.db.close()
