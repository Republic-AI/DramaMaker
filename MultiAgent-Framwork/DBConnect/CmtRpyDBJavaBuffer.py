import mysql.connector
from mysql.connector import Error
import os

# Utility functions
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
        """
        )
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

# Schema creation
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
        cursor.execute("USE AITown")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS comment_reply_java_buffer (
            requestId BIGINT UNSIGNED NOT NULL,
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            msgId INT NOT NULL,
            senderId VARCHAR(255) NOT NULL,
            content LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            sname TEXT,
            isBeingProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            privateMsg BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (requestId)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'comment_reply_java_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

# Data manipulation
def insert_into_table(connection, requestId, time, npcId, msgId, senderId, content, sname,
                       isProcessed=False, isBeingProcessed=False, privateMsg=True):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        insert_query = """
        INSERT INTO comment_reply_java_buffer (
            requestId, time, npcId, msgId, senderId,
            content, isProcessed, sname, isBeingProcessed, privateMsg
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            content = VALUES(content),
            isProcessed = VALUES(isProcessed),
            sname = VALUES(sname)
        """
        cursor.execute(insert_query, (
            requestId, time, npcId, msgId, senderId,
            content, isProcessed, sname, isBeingProcessed, privateMsg
        ))
        connection.commit()
        print(f"Data inserted successfully: requestId={requestId}, time={time}, npcId={npcId}, msgId={msgId}, senderId={senderId}, sname={sname}, content length={len(content)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert data: {e}")

# Job queue operations

def get_earliest_unprocessed_entry(connection):
    """
    Atomically claim the earliest unprocessed entry using
    FOR UPDATE SKIP LOCKED within a short transaction, returning a tuple.
    """
    try:
        # Begin a short transaction
        connection.start_transaction()
        cursor = connection.cursor()
        cursor.execute("USE AITown")

        # Select and lock one unprocessed row
        cursor.execute(
            """
            SELECT requestId, time, npcId, msgId, senderId,
                   content, isProcessed, sname, isBeingProcessed, privateMsg
            FROM comment_reply_java_buffer
            WHERE isProcessed = FALSE AND isBeingProcessed = FALSE
            ORDER BY time ASC
            LIMIT 1 FOR UPDATE SKIP LOCKED
            """
        )
        row = cursor.fetchone()

        if not row:
            connection.commit()
            print("No unprocessed entries found.")
            return None

        # Extract values
        request_id, time_stamp = row[0], row[1]

        # Mark row as being processed
        cursor.execute(
            """
            UPDATE comment_reply_java_buffer
            SET isBeingProcessed = TRUE
            WHERE requestId = %s AND time = %s
            """,
            (request_id, time_stamp)
        )
        connection.commit()

        print(f"Claimed entry: requestId={request_id}, time={time_stamp}")
        return row
    except Error as e:
        connection.rollback()
        print(f"Failed to retrieve earliest unprocessed entry: {e}")
        return None

def mark_entry_as_processed(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        cursor.execute(
            "UPDATE comment_reply_java_buffer SET isProcessed = TRUE WHERE requestId = %s",
            (requestId,),
        )
        connection.commit()
        print(f"Entry with requestId={requestId} marked as processed.")
    except Error as e:
        print(f"Failed to mark entry as processed: {e}")

# Deletion
def delete_entry_in_buffer(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        cursor.execute(
            "DELETE FROM comment_reply_java_buffer WHERE requestId = %s",
            (requestId,),
        )
        connection.commit()
        print(f"Entry with requestId={requestId} has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entry: {e}")

def delete_all_content_in_buffer(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        cursor.execute("DELETE FROM comment_reply_java_buffer")
        connection.commit()
        print("All content in 'comment_reply_java_buffer' table has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete content in buffer: {e}")

# Bulk queries
def mark_all_entries_as_processed(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute("UPDATE comment_reply_java_buffer SET isProcessed = TRUE")
    connection.commit()
    print("All entries have been marked as processed, keeping 'isBeingProcessed' unchanged.")

def get_unprocessed_entries_of_npc(connection, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        cursor.execute(
            "SELECT requestId, time, npcId, msgId, senderId, content, isProcessed, sname"
            " FROM comment_reply_java_buffer"
            " WHERE isProcessed = FALSE AND npcId = %s"
            " ORDER BY time ASC",
            (npcId,)
        )
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} unprocessed entries for npcId={npcId}.")
        else:
            print(f"No unprocessed entries found for npcId={npcId}.")
        return results
    except Error as e:
        print(f"Failed to retrieve unprocessed entries for npcId={npcId}: {e}")
        return []
    
def get_unprocessed_entrie_of_npc(connection, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        query = """
        SELECT requestId, time, npcId, msgId, senderId, content, isProcessed, sname, isBeingProcessed, privateMsg FROM comment_reply_java_buffer
        WHERE isProcessed = FALSE AND npcId = %s
        ORDER BY time ASC
        LIMIT 1
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
        cursor.execute("USE AITown")
        cursor.execute(
            "SELECT requestId, time, npcId, msgId, senderId, content, isProcessed, sname"
            " FROM comment_reply_java_buffer"
            " WHERE isProcessed = FALSE"
            " ORDER BY time ASC"
        )
        results = cursor.fetchall()
        if results:
            print(f"Unprocessed entries count: {len(results)}.")
        else:
            print("No unprocessed entries found.")
        return results
    except Error as e:
        print(f"Failed to retrieve all unprocessed entries: {e}")
        return []
