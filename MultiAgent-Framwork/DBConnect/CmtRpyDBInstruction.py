import mysql.connector
from mysql.connector import Error
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

def create_comment_reply_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS comment_reply_instruction_buffer (
            requestId BIGINT UNSIGNED NOT NULL PRIMARY KEY,
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            msgId INT NOT NULL,
            instruction LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
        cursor.execute(create_table_query)
        print("Table 'comment_reply_instruction_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def insert_into_instruction_table(connection, requestId, time, npcId, msgId, instruction, isProcessed=False):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai") 
        insert_query = """
        INSERT INTO comment_reply_instruction_buffer (requestId, time, npcId, msgId, instruction, isProcessed)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE instruction = VALUES(instruction), isProcessed = VALUES(isProcessed)
        """
        cursor.execute(insert_query, (requestId, time.strftime('%Y-%m-%d %H:%M:%S'), npcId, msgId, instruction, isProcessed))
        connection.commit()
        print(f"Instruction inserted successfully: requestId={requestId}, time={time}, npcId={npcId}, msgId={msgId}, instruction length={len(instruction)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert instruction: {e}")

def delete_comment_reply_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")  # Ensure you're using the correct database
        delete_table_query = "DROP TABLE IF EXISTS comment_reply_instruction_buffer"
        cursor.execute(delete_table_query)
        connection.commit()
        print("Table 'comment_reply_instruction_buffer' has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete table comment_reply_instruction_buffer: {e}")

def delete_all_instructions(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")  # Ensure you're using the correct database
        delete_query = "DELETE FROM comment_reply_instruction_buffer"
        cursor.execute(delete_query)
        connection.commit()
        print("All instructions in the 'comment_reply_instruction_buffer' table have been deleted successfully.")
    except Error as e:
        print(f"Failed to delete instructions: {e}")

def get_earliest_unprocessed_instruction(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT * FROM comment_reply_instruction_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Earliest unprocessed instruction: requestId={result[0]}, time={result[1]}, npcId={result[2]}, msgId={result[3]}, instruction={result[4]}")
            return result
        else:
            print("No unprocessed instructions found.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest unprocessed instruction: {e}")
        return None

def mark_instruction_as_processed(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        update_query = """
        UPDATE comment_reply_instruction_buffer
        SET isProcessed = TRUE
        WHERE requestId = %s
        """
        cursor.execute(update_query, (requestId,))
        connection.commit()
        print(f"Instruction with requestId={requestId} marked as processed.")
    except Error as e:
        print(f"Failed to mark instruction as processed: {e}")

def get_all_unprocessed_instructions(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT * FROM comment_reply_instruction_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            print("Unprocessed instructions:")
            for result in results:
                print(f"requestId={result[0]}, time={result[1]}, npcId={result[2]}, msgId={result[3]}, instruction length={len(result[4])}")
            return results
        else:
            print("No unprocessed instructions found.")
            return []
    except Error as e:
        print(f"Failed to retrieve unprocessed instructions: {e}")
        return []

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'comment_reply_instruction_buffer'
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

# Usage examples:
# connection = establish_sql_connection()
# create_comment_reply_table(connection)
# insert_into_instruction_table(connection, 1, '2024-09-09 12:00:00', 101, 202, '{"actionId": 117, "npcId": 101, "data": {"playerId": 202, "content": "Sample reply", "msgId": 303}}')
# get_earliest_unprocessed_instruction(connection)
# mark_instruction_as_processed(connection, 1)
# get_all_unprocessed_instructions(connection)
# delete_comment_reply_table(connection)