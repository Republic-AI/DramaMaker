import mysql.connector
from mysql.connector import Error
import configparser
import os

def check_connection(connection):
    if connection.is_connected():
        print("Connection is still active.")
    else:
        print("Connection is not active. Reconnecting...")
        connection.reconnect(attempts=3, delay=5)  # Attempt to reconnect 3 times with a 5-second delay
        if connection.is_connected():
            print("Reconnection successful.")
        else:
            print("Reconnection failed.")

def create_instruction_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")  # Use the AITown database
    create_table_query = """
    CREATE TABLE IF NOT EXISTS behavior_instruction_buffer (
        time DATETIME NOT NULL,
        npcId INT NOT NULL,
        instruction LONGTEXT,
        isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        requestId BIGINT NOT NULL,
        PRIMARY KEY (time, npcId)
    )
    """
    cursor.execute(create_table_query)
    print("Table 'behavior_instruction_buffer' checked/created successfully.")

def insert_into_instruction_table(connection, time, npcId, instruction, requestId, isProcessed=False):
    cursor = connection.cursor()
    cursor.execute("USE Dramai") 
    insert_query = """
    INSERT INTO behavior_instruction_buffer (time, npcId, instruction, isProcessed, requestId)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        instruction = VALUES(instruction), 
        isProcessed = VALUES(isProcessed), 
        requestId = VALUES(requestId)
    """
    cursor.execute(insert_query, (time, npcId, instruction, isProcessed, requestId))
    connection.commit()
    print(f"Instruction inserted successfully: time={time}, npcId={npcId}, instruction length={len(instruction)}, isProcessed={isProcessed}, requestId={requestId}")

def delete_instruction_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")  # Ensure you're using the correct database
    delete_table_query = "DROP TABLE IF EXISTS behavior_instruction_buffer"
    cursor.execute(delete_table_query)
    connection.commit()
    print(f"Table behavior_instruction_buffer has been deleted successfully.")

def delete_all_instructions(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")  # Ensure you're using the correct database
    delete_query = "DELETE FROM behavior_instruction_buffer"
    cursor.execute(delete_query)
    connection.commit()
    print("All instructions in the 'behavior_instruction_buffer' table have been deleted successfully.")

def get_earliest_unprocessed_instruction(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    query = """
    SELECT * FROM behavior_instruction_buffer 
    WHERE isProcessed = FALSE
    ORDER BY time ASC 
    LIMIT 1
    """
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        print(f"Earliest unprocessed instruction: time={result[0]}, npcId={result[1]}, instruction={result[2]}, requestId={result[4]}")
        return result
    else:
        print("No unprocessed instructions found.")
        return None

def mark_instruction_as_processed(connection, time, npcId):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    update_query = """
    UPDATE behavior_instruction_buffer
    SET isProcessed = TRUE
    WHERE time = %s AND npcId = %s
    """
    cursor.execute(update_query, (time, npcId))
    connection.commit()
    print(f"Instruction with time={time} and npcId={npcId} marked as processed.")

def get_all_unprocessed_instructions(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    query = """
    SELECT * FROM behavior_instruction_buffer 
    WHERE isProcessed = FALSE
    ORDER BY time ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()
    if results:
        print("Unprocessed instructions:")
        for result in results:
            print(f"time={result[0]}, npcId={result[1]}, instruction length={len(result[2])}, requestId={result[4]}")
        return results
    else:
        print("No unprocessed instructions found.")
        return []

def instruction_table_exists(connection):
    db_name = 'AITown'
    table_name = 'behavior_instruction_buffer'
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = '{table_name}'
    """)
    result = cursor.fetchone()
    if result:
        print(f"Table '{table_name}' exists in database '{db_name}'.")
        return True
    else:
        print(f"Table '{table_name}' does not exist in database '{db_name}'.")
        return False

# Usage examples:
# connection = establish_sql_connection()
# create_instruction_table(connection)
# requestId = 1123413412341234
# insert_into_instruction_table(connection, '2024-09-09 12:00:00', 1, 'Some instruction content', requestId)
# get_earliest_unprocessed_instruction(connection)
# mark_instruction_as_processed(connection, '2024-09-09 12:00:00', 1)
# get_all_unprocessed_instructions(connection)
# delete_instruction_table(connection)