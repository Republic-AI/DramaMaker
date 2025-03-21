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

def delete_database(connection, db_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        print(f"Database '{db_name}' deleted successfully.")
    except Error as e:
        print(f"Failed to delete database '{db_name}': {e}")

def list_databases(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("Remaining databases:")
        for db in databases:
            print(db[0])
    except Error as e:
        print(f"Failed to list databases: {e}")

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
        cursor.execute("USE Dramai")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS announcement_java_buffer (
            requestId BIGINT NOT NULL,
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            content LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (requestId, time)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'announcement_java_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def insert_into_table(connection, requestId, time, npcId, content, isProcessed=False):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai") 
        insert_query = """
        INSERT INTO announcement_java_buffer (requestId, time, npcId, content, isProcessed)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content), isProcessed = VALUES(isProcessed)
        """
        cursor.execute(insert_query, (requestId, time, npcId, content, isProcessed))
        connection.commit()
        print(f"Data inserted successfully: requestId={requestId}, time={time}, npcId={npcId}, content length={len(content)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert data: {e}")

def delete_all_content_in_buffer(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")  # Ensure you're using the correct database
        delete_query = "DELETE FROM announcement_java_buffer"
        cursor.execute(delete_query)
        connection.commit()
        print("All content in the 'announcement_java_buffer' table has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete content: {e}")

def get_earliest_unprocessed_entry(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        query = """
        SELECT * FROM announcement_java_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Earliest unprocessed entry: requestId={result[0]}, time={result[1]}, npcId={result[2]}, content={result[3]}")
            return result
        else:
            print("No unprocessed entries found.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest unprocessed entry: {e}")
        return None


def table_exists(connection, table_name = 'announcement_java_buffer'):
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

def mark_entry_as_processed(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE Dramai")
        update_query = """
        UPDATE announcement_java_buffer
        SET isProcessed = TRUE
        WHERE requestId = %s
        """
        cursor.execute(update_query, (requestId,))
        connection.commit()
        print(f"Entry with requestId={requestId} marked as processed.")
    except Error as e:
        print(f"Failed to mark entry as processed: {e}")