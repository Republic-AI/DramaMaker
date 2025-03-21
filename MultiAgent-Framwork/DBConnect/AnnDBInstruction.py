import mysql.connector
from mysql.connector import Error

def check_connection(connection):
    if connection.is_connected():
        print("Connection is still active.")
    else:
        print("Connection is not active. Reconnecting...")
        connection.reconnect(attempts=3, delay=5)
        if connection.is_connected():
            print("Reconnection successful.")
        else:
            print("Reconnection failed.")

def create_instruction_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS announcement_instruction_buffer (
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            instruction LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (time, npcId)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'announcement_instruction_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def insert_into_instruction_table(connection, time, npcId, instruction, isProcessed=False):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai") 
        insert_query = """
        INSERT INTO announcement_instruction_buffer (time, npcId, instruction, isProcessed)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE instruction = VALUES(instruction), isProcessed = VALUES(isProcessed)
        """
        cursor.execute(insert_query, (time, npcId, instruction, isProcessed))
        connection.commit()
        print(f"Instruction inserted successfully: time={time}, npcId={npcId}, instruction length={len(instruction)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert instruction: {e}")

def delete_instruction_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        delete_table_query = "DROP TABLE IF EXISTS announcement_instruction_buffer"
        cursor.execute(delete_table_query)
        connection.commit()
        print(f"Table announcement_instruction_buffer has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete table announcement_instruction_buffer: {e}")

def delete_all_instructions(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        delete_query = "DELETE FROM announcement_instruction_buffer"
        cursor.execute(delete_query)
        connection.commit()
        print("All instructions in the 'announcement_instruction_buffer' table have been deleted successfully.")
    except Error as e:
        print(f"Failed to delete instructions: {e}")

def get_earliest_unprocessed_instruction(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT * FROM announcement_instruction_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Earliest unprocessed instruction: time={result[0]}, npcId={result[1]}, instruction={result[2]}")
            return result
        else:
            print("No unprocessed instructions found.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest unprocessed instruction: {e}")
        return None

def mark_instruction_as_processed(connection, time, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        update_query = """
        UPDATE announcement_instruction_buffer
        SET isProcessed = TRUE
        WHERE time = %s AND npcId = %s
        """
        cursor.execute(update_query, (time, npcId))
        connection.commit()
        print(f"Instruction with time={time} and npcId={npcId} marked as processed.")
    except Error as e:
        print(f"Failed to mark instruction as processed: {e}")

def get_all_unprocessed_instructions(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT * FROM announcement_instruction_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            print("Unprocessed instructions:")
            for result in results:
                print(f"time={result[0]}, npcId={result[1]}, instruction length={len(result[2])}")
            return results
        else:
            print("No unprocessed instructions found.")
            return []
    except Error as e:
        print(f"Failed to retrieve unprocessed instructions: {e}")
        return []

def instruction_table_exists(connection):
    db_name = 'AITown'
    table_name = 'announcement_instruction_buffer'
    try:
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
    except Error as e:
        print(f"Failed to check if table exists: {e}")
        return False

def create_database(connection):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' checked/created successfully.")
    except Error as e:
        print(f"Failed to create database '{db_name}': {e}")

def table_exists(connection, table_name = 'announcement_instruction_buffer'):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = %s
        """, (table_name,))
        result = cursor.fetchone()
        if result:
            print(f"Table '{table_name}' exists in database '{db_name}'.")
            return True
        else:
            print(f"Table '{table_name}' does not exist in database '{db_name}'.")
            return False
    except Error as e:
        print(f"Failed to check if table exists: {e}")
        return False


def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS announcement_instruction_buffer (
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            instruction LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (time, npcId)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'announcement_instruction_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")
        
# Usage examples:
# connection = establish_sql_connection()
# create_instruction_table(connection)
# insert_into_instruction_table(connection, '2024-09-09 12:00:00', 1, 'Some instruction content')
# get_earliest_unprocessed_instruction(connection)
# mark_instruction_as_processed(connection, '2024-09-09 12:00:00', 1)
# get_all_unprocessed_instructions(connection)
# delete_instruction_table(connection)