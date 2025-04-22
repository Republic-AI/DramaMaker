import sys
import os
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, TimeoutError

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

import DBConnect.DBCon as DBCon
from DBConnect import DBCon
from DBConnect import CmtRpyDBJavaBuffer
from DBConnect import CmtRpyDBInstruction
from DBConnect import CmtRpyDBMemStre

import CmtRpyLgcProcessOnce

def clear_printout_folder():
    printout_folder = os.path.join(base_dir, 'CmtRpyCtrl', 'printout')
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
    if not CmtRpyDBJavaBuffer.database_exists(db_conn):
        CmtRpyDBJavaBuffer.create_database(db_conn)

    if not CmtRpyDBJavaBuffer.table_exists(db_conn):
        CmtRpyDBJavaBuffer.create_table(db_conn)
        
    if not CmtRpyDBInstruction.table_exists(db_conn):
        CmtRpyDBInstruction.create_comment_reply_table(db_conn)

    if not CmtRpyDBMemStre.table_exists(db_conn):
        CmtRpyDBMemStre.create_table(db_conn)

initialize_database(global_db_conn)
if global_db_conn:
    global_db_conn.close()

def process_task(task_id):
    """
    Runs the main processing function.
    Returns whatever the function returns, or 0 if there's nothing to process.
    """
    return CmtRpyLgcProcessOnce.choiceOneToReply()

def get_num_workers():
    try:
        # Path to char_config.yaml
        config_path = os.path.join(base_dir, 'char_config.yaml')
        
        # Read and parse the YAML file
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Count the number of NPCs by counting npcId entries
        npc_count = len(config.get('npcCharacters', []))
        
        # Set num_workers to 2 times the number of NPCs
        return max(2, npc_count * 5)  # Ensure at least 2 workers
    except Exception as e:
        print(f"Error reading char_config.yaml: {e}")
        return 18  # Default fallback value

# Dynamically set num_workers based on npcCharacters count
num_workers = get_num_workers()
print(f"Setting num_workers to {num_workers} (2 * {num_workers//2} NPCs)")

n = 0

with ThreadPoolExecutor(max_workers=num_workers) as executor:
    while True:
        futures = [executor.submit(process_task, n + i) for i in range(num_workers)]
        
        # Wait for each future to complete or time out after 76 seconds
        for future in futures:
            try:
                # If the function does not finish within 76 seconds, raise TimeoutError
                result = future.result(timeout=76)
                # 'result' is the return value from process_task(...)
                # handle result if needed
            except TimeoutError:
                print("A worker timed out after 76 seconds.")
                # Optionally try to cancel, but if it's already running, it won't stop the thread
                future.cancel()
                # You could add logging or error handling here as needed
            except Exception as e:
                # Catch any other exceptions thrown by process_task
                print(f"Exception in worker: {e}")
        
        n += num_workers
        time.sleep(2)