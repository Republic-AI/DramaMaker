import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

from DBConnect import DBCon
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule
import BhrCtrl.BhrLgcToMemStre as BhrLgcToMemStre
import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce

def clear_printout_folder():
    printout_folder = os.path.join(base_dir, 'BhrCtrl', 'printout')
    if os.path.exists(printout_folder):
        for file_name in os.listdir(printout_folder):
            file_path = os.path.join(printout_folder, file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

# Clear once at start
clear_printout_folder()

global_db_conn = DBCon.establish_sql_connection()

def initialize_database(db_conn):
    # BhrDBJavaBuffer.delete_database(db_conn, 'AITown')
    if not BhrDBJavaBuffer.database_exists(db_conn):
        BhrDBJavaBuffer.create_database(db_conn)
    if not BhrDBJavaBuffer.table_exists(db_conn):
        BhrDBJavaBuffer.create_table(db_conn)
    if not BhrDBMemStre.table_exists(db_conn):
        BhrDBMemStre.create_table(db_conn)
    if not BhrDBReflection.table_exists(db_conn):
        BhrDBReflection.create_table(db_conn)
    if not BhrDBReflectionTracer.table_exists(db_conn):
        BhrDBReflectionTracer.create_table(db_conn)
    if not BhrDBSchedule.table_exists(db_conn):
        BhrDBSchedule.create_table(db_conn)
    if not BhrDBInstruction.instruction_table_exists(db_conn):
        BhrDBInstruction.create_instruction_table(db_conn)

initialize_database(global_db_conn)
if global_db_conn:
    global_db_conn.close()

def process_task(task_id):
    # Just call the function, no exceptions expected
    result = BhrLgcProcessOnce.processOneInputGiveOneInstruction()
    # If result == 0, means no job. That's not an error, just continue.

num_workers = 18
n = 0

with ThreadPoolExecutor(max_workers=num_workers) as executor:
    futures = [executor.submit(process_task, n + i) for i in range(num_workers)]
    for future in futures:
        # If any worker raised exception, this will raise
        # If no exceptions, this returns immediately.
        future.result()
    n += num_workers
