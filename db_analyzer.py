import os
import argparse

from modules.db import DB

parser = argparse.ArgumentParser(description='A script for analyzing the databases created using GAs.')
parser.add_argument('--DB_NAME', type=str, required=True, help='The name of the used database.')
parser.add_argument('--TIMEOUT', type=int, required=True, help='The Vitis HLS 2021.1 procedure timeout.')

args = parser.parse_args()

DB_NAME = args.DB_NAME
TIMEOUT = args.TIMEOUT

DB_PATH = os.path.join("./databases", DB_NAME + ".sqlite")
db = DB(DB_PATH)

# db.print()
db.analyze(TIMEOUT)
# db.export()
