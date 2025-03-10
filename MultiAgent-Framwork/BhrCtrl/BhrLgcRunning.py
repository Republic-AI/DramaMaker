# import sys
# import os
# import time

# # Add the base directory (one level up from the current directory)
# base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(base_dir)

# # Import project-specific modules
# from DBConnect import DBCon
# from DBConnect import BhrDBJavaBuffer
# from DBConnect import BhrDBInstruction
# from DBConnect import BhrDBReflectionTracer
# from DBConnect import BhrDBMemStre
# from DBConnect import BhrDBReflection
# from DBConnect import BhrDBSchedule
# import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce

# # Function to delete all files in the BhrCtrl/printout folder
# def clear_printout_folder():
#     printout_folder = os.path.join(base_dir, 'BhrCtrl', 'printout')
#     if os.path.exists(printout_folder):
#         for file_name in os.listdir(printout_folder):
#             file_path = os.path.join(printout_folder, file_name)
#             try:
#                 if os.path.isfile(file_path):
#                     os.remove(file_path)
#                     print(f"Deleted: {file_path}")
#             except Exception as e:
#                 print(f"Error deleting {file_path}: {e}")

# # Clear the printout folder
# clear_printout_folder()

# # Establish a database connection
# db_conn = DBCon.establish_sql_connection()

# # Initialize the database by creating required tables
# def initialize_database(db_conn):
#     print("Initializing database...")
#     BhrDBJavaBuffer.delete_database(db_conn, 'AITown')

#     if not BhrDBJavaBuffer.database_exists(db_conn):
#         BhrDBJavaBuffer.create_database(db_conn)

#     if not BhrDBJavaBuffer.table_exists(db_conn):
#         BhrDBJavaBuffer.create_table(db_conn)
#     if not BhrDBMemStre.table_exists(db_conn):
#         BhrDBMemStre.create_table(db_conn)
#     if not BhrDBReflection.table_exists(db_conn):
#         BhrDBReflection.create_table(db_conn)
#     if not BhrDBReflectionTracer.table_exists(db_conn):
#         BhrDBReflectionTracer.create_table(db_conn)
#     if not BhrDBSchedule.table_exists(db_conn):
#         BhrDBSchedule.create_table(db_conn)
#     if not BhrDBInstruction.instruction_table_exists(db_conn):
#         BhrDBInstruction.create_instruction_table(db_conn)

# # Call the initialization function
# initialize_database(db_conn)

# # Infinite loop to process tasks
# n = 0
# try:
#     while True:
#         print(f"Processing step {n}")
#         # Call the core processing function
#         BhrLgcProcessOnce.processOneInputGiveOneInstruction()
#         print("\n" * 5)  # Add spacing between iterations for clarity
#         time.sleep(2)  # Adjust the sleep interval as needed
#         n += 1
# except KeyboardInterrupt:
#     print("Loop terminated by user.")
# finally:
#     # Close the database connection if it exists
#     if db_conn:
#         db_conn.close()
#         print("Database connection closed.")


import sys
import os
import time

# Create a Tee class that duplicates writes to multiple streams
class Tee:
    def __init__(self, *files):
        self.files = files
    
    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

# Add the base directory (one level up from the current directory)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

# Import project-specific modules
from DBConnect import DBCon
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule
import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce

# Open output file and set up tee for printing
log_file = os.path.join(os.path.dirname(__file__), 'output.txt')
with open(log_file, 'w') as f:
    # Create a tee that writes to both stdout and the file
    tee = Tee(sys.stdout, f)
    sys.stdout = tee

    # Function to delete all files in the BhrCtrl/printout folder
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

    # Clear the printout folder
    clear_printout_folder()

    # Establish a database connection
    db_conn = DBCon.establish_sql_connection()

    # Initialize the database by creating required tables
    def initialize_database(db_conn):
        print("Initializing database...")
        BhrDBJavaBuffer.delete_database(db_conn, 'AITown')

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

    # Call the initialization function
    initialize_database(db_conn)

    # Infinite loop to process tasks
    n = 0
    try:
        while True:
            print(f"Processing step {n}")
            # Call the core processing function
            BhrLgcProcessOnce.processOneInputGiveOneInstruction()
            print("\n" * 5)  # Add spacing between iterations for clarity
            time.sleep(2)  # Adjust the sleep interval as needed
            n += 1
    except KeyboardInterrupt:
        print("Loop terminated by user.")
    finally:
        # Close the database connection if it exists
        if db_conn:
            db_conn.close()
            print("Database connection closed.")