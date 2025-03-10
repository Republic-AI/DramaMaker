import sys
import os

import pandas as pd
import numpy as np
import json
import re
import pickle
import time

# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

import DBConnect.DBCon as DBCon

import DBConnect.AnnDBJavaBuffer as AnnDBJavaBuffer
import DBConnect.AnnDBAnnBuffer as AnnDBAnnBuffer
import DBConnect.AnnDBInstruction as AnnDBInstruction

import AnnCtrlLgcProcessOnce


dbcon = DBCon.establish_sql_connection()
AnnDBJavaBuffer.delete_database(dbcon, 'AITown')
AnnDBJavaBuffer.create_database(dbcon)

if not AnnDBJavaBuffer.table_exists(dbcon):
    AnnDBJavaBuffer.create_table(dbcon)
if not AnnDBAnnBuffer.table_exists(dbcon):
    AnnDBAnnBuffer.create_table(dbcon)
if not AnnDBInstruction.table_exists(dbcon):
    AnnDBInstruction.create_table(dbcon)

AnnDBJavaBuffer.delete_all_content_in_buffer(dbcon)
AnnDBAnnBuffer.delete_all_announcements(dbcon)
AnnDBInstruction.delete_all_instructions(dbcon)

n = 0
while True:
    print(f"Processing step {n}")
    AnnCtrlLgcProcessOnce.makeAnAnnouncement()
    time.sleep(2)
    n += 1