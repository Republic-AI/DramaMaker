import mysql.connector
from mysql.connector import Error
import os

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

def database_exists(connection, db_name='AITown'):
    """
    Checks if a database exists.
    """
    try:
        cursor = connection.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()
        if result:
            print(f"Database '{db_name}' exists.")
            return True
        else:
            print(f"Database '{db_name}' does not exist.")
            return False
    except Error as e:
        print(f"Failed to check if database exists: {e}")
        return False

def table_exists(connection, db_name='AITown'):
    """
    Checks if the specific table 'comment_reply_java_buffer' exists within the database.
    """
    table_name = 'comment_reply_java_buffer'
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
        
def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS comment_reply_java_buffer (
            requestId BIGINT UNSIGNED NOT NULL,  -- Use UNSIGNED for larger positive values
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            msgId INT NOT NULL,
            senderId VARCHAR(255) NOT NULL,  -- Assuming senderId might be alphanumeric
            content LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            sname TEXT,
            privateMsg BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (requestId)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'comment_reply_java_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def insert_into_table(connection, requestId, time, npcId, msgId, senderId, content, sname, isProcessed=False, privateMsg=True):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai") 
        insert_query = """
        INSERT INTO comment_reply_java_buffer (requestId, time, npcId, msgId, senderId, content, isProcessed, sname, privateMsg)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content), isProcessed = VALUES(isProcessed), sname = VALUES(sname)
        """
        cursor.execute(insert_query, (requestId, time, npcId, msgId, senderId, content, isProcessed, sname, privateMsg))
        connection.commit()
        print(f"Data inserted successfully: requestId={requestId}, time={time}, npcId={npcId}, msgId={msgId}, senderId={senderId}, sname={sname}, content length={len(content)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert data: {e}")

def get_earliest_unprocessed_entry(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT requestId, time, npcId, msgId, senderId, content, isProcessed, sname, privateMsg FROM comment_reply_java_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Earliest unprocessed entry: requestId={result[0]}, time={result[1]}, npcId={result[2]}, msgId={result[3]}, senderId={result[4]}, sname={result[7]}, content={result[5]}")
            return result
        else:
            print("No unprocessed entries found.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest unprocessed entry: {e}")
        return None

def mark_entry_as_processed(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        update_query = """
        UPDATE comment_reply_java_buffer
        SET isProcessed = TRUE
        WHERE requestId = %s
        """
        cursor.execute(update_query, (requestId,))
        connection.commit()
        print(f"Entry with requestId={requestId} marked as processed.")
    except Error as e:
        print(f"Failed to mark entry as processed: {e}")

def delete_entry_in_buffer(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        delete_query = "DELETE FROM comment_reply_java_buffer WHERE requestId = %s"
        cursor.execute(delete_query, (requestId,))
        connection.commit()
        print(f"Entry with requestId={requestId} has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entry: {e}")

def get_unprocessed_entries_of_npc(connection, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT requestId, time, npcId, msgId, senderId, content, isProcessed, sname, privateMsg FROM comment_reply_java_buffer
        WHERE isProcessed = FALSE AND npcId = %s
        ORDER BY time ASC
        """
        cursor.execute(query, (npcId,))
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} unprocessed entries for npcId={npcId}.")
        else:
            print(f"No unprocessed entries found for npcId={npcId}.")
        return results
    except Error as e:
        print(f"Failed to retrieve unprocessed entries for npcId={npcId}: {e}")
        return []

def get_all_unprocessed_entries(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT requestId, time, npcId, msgId, senderId, content, isProcessed, sname, privateMsg FROM comment_reply_java_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            print(f"Unprocessed entries count: {len(results)}.")
        else:
            print("No unprocessed entries found.")
        return results
    except Error as e:
        print(f"Failed to retrieve all unprocessed entries: {e}")
        return []

def delete_all_content_in_buffer(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        delete_query = "DELETE FROM comment_reply_java_buffer"
        cursor.execute(delete_query)
        connection.commit()
        print("All content in 'comment_reply_java_buffer' table has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete content in buffer: {e}")

# Usage examples:
# connection = establish_sql_connection()
# if not database_exists(connection):
#     create_database(connection)
# if not table_exists(connection):
#     create_table(connection)