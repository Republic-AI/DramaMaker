import sys
import os
import time

# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

import DBConnect.DBCon as DBCon
from DBConnect import DBCon
from DBConnect import CmtRpyDBJavaBuffer
from DBConnect import CmtRpyDBInstruction

import CmtRpyLgcProcessOnce

# Establish database connection
db_conn = DBCon.establish_sql_connection()

# Check if the database and tables exist, create them if not
if not CmtRpyDBJavaBuffer.database_exists(db_conn):
    CmtRpyDBJavaBuffer.create_database(db_conn)

if not CmtRpyDBJavaBuffer.table_exists(db_conn):
    CmtRpyDBJavaBuffer.create_table(db_conn)
    
if not CmtRpyDBInstruction.table_exists(db_conn):
    CmtRpyDBInstruction.create_comment_reply_table(db_conn)

# Clear all content in the tables (optional)
# CmtRpyDBJavaBuffer.delete_all_content_in_buffer(db_conn)
# CmtRpyDBInstruction.delete_all_instructions(db_conn)

# Processing loop
n = 0
while True:
    print(f"Processing step {n}")
    
    # Process one input and generate one instruction
    CmtRpyLgcProcessOnce.choiceOneToReply()
    print()
    print()
    print()
    print()
    print()
    
    # Sleep before the next iteration
    time.sleep(2)
    n += 1