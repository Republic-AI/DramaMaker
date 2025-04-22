import mysql.connector
from mysql.connector import Error
import threading

# Create a global lock
lock = threading.Lock()

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
    cursor = connection.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
    print(f"Database '{db_name}' deleted successfully.")

def list_databases(connection):
    cursor = connection.cursor()
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    print("Remaining databases:")
    for db in databases:
        print(db[0])

def create_database(connection):
    db_name = 'AITown'
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    print(f"Database '{db_name}' checked/created successfully.")

def database_exists(connection):
    db_name = 'AITown'
    cursor = connection.cursor()
    cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
    result = cursor.fetchone()
    if result:
        print(f"Database '{db_name}' exists.")
        return True
    else:
        print(f"Database '{db_name}' does not exist.")
        return False

def create_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")  # Use the AITown database
    create_table_query = """
    CREATE TABLE IF NOT EXISTS behavior_java_buffer (
        requestId BIGINT NOT NULL,
        time DATETIME NOT NULL,
        npcId INT NOT NULL,
        content LONGTEXT,
        isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        isBeingProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        isFullyProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (requestId, time)
    )
    """
    cursor.execute(create_table_query)
    print("Table 'behavior_java_buffer' checked/created successfully.")

def delete_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")  # Ensure you're using the correct database
    delete_table_query = f"DROP TABLE IF EXISTS behavior_java_buffer"
    cursor.execute(delete_table_query)
    connection.commit()
    print(f"Table behavior_java_buffer has been deleted successfully.")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'behavior_java_buffer'
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

def insert_into_table(connection, requestId, time, npcId, content, isProcessed=False, isBeingProcessed=False):
    cursor = connection.cursor()
    cursor.execute("USE AITown") 
    insert_query = """
    INSERT INTO behavior_java_buffer (requestId, time, npcId, content, isProcessed, isBeingProcessed)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE content = VALUES(content), isProcessed = VALUES(isProcessed)
    """
    cursor.execute(insert_query, (requestId, time, npcId, content, isProcessed, isBeingProcessed))
    connection.commit()
    print(f"Data inserted successfully: requestId={requestId}, time={time}, npcId={npcId}, content length={len(content)}, isProcessed={isProcessed}")

def delete_entry_in_buffer(connection, time, npcId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")  # Ensure you're using the correct database
    delete_query = "DELETE FROM behavior_java_buffer WHERE time = %s AND npcId = %s"
    cursor.execute(delete_query, (time, npcId))
    connection.commit()  # Commit the changes
    print(f"Entry with time={time} and npcId={npcId} has been deleted successfully.")

def delete_all_content_in_buffer(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")  # Ensure you're using the correct database
    delete_query = "DELETE FROM behavior_java_buffer"
    cursor.execute(delete_query)
    connection.commit()  # Commit the changes
    print("All content in the 'behavior_java_buffer' table has been deleted successfully.")

def get_earliest_unprocessed_entry(connection):
    with lock:  # Acquire the lock
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Use the AITown database

        # Query to get the earliest unprocessed entry with isBeingProcessed = FALSE
        query = """
        SELECT requestId, time, npcId, content, isProcessed, isBeingProcessed 
        FROM behavior_java_buffer
        WHERE isProcessed = FALSE AND isBeingProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            request_id = result[0]  # Extract requestId
            time_stamp = result[1]  # Extract time (DATETIME primary key)

            print(f"Earliest unprocessed entry: requestId={request_id}, time={time_stamp}, npcId={result[2]}, content={result[3]}")

            # Update the entry to set isBeingProcessed = TRUE
            update_query = """
            UPDATE behavior_java_buffer
            SET isBeingProcessed = TRUE
            WHERE requestId = %s AND time = %s
            """
            cursor.execute(update_query, (request_id, time_stamp))
            connection.commit()

            print(f"Entry with requestId={request_id}, time={time_stamp} marked as being processed.")
            return result
        else:
            print("No unprocessed entries found.")
            return None

def get_unprocessed_entries_of_npc(connection, npcId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    
    # Query for all unprocessed entries for the given npcId
    query_all = """
    SELECT * FROM behavior_java_buffer 
    WHERE isProcessed = FALSE AND npcId = %s
    ORDER BY time ASC
    """
    cursor.execute(query_all, (npcId,))
    all_unprocessed_of_a_npc = cursor.fetchall()
    
    # Query for the latest unprocessed entry for the given npcId
    query_latest = """
    SELECT * FROM behavior_java_buffer 
    WHERE isProcessed = FALSE AND npcId = %s
    ORDER BY time DESC 
    LIMIT 1
    """
    cursor.execute(query_latest, (npcId,))
    latest_unprocessed_of_a_npc = cursor.fetchone()
    
    if all_unprocessed_of_a_npc:
        print(f"Found {len(all_unprocessed_of_a_npc)} unprocessed entries for npcId={npcId}.")
    else:
        print(f"No unprocessed entries found for npcId={npcId}.")
    
    if latest_unprocessed_of_a_npc:
        print(f"Latest unprocessed entry for npcId={npcId}: time={latest_unprocessed_of_a_npc[1]}")
    else:
        print(f"No latest unprocessed entry found for npcId={npcId}.")

    return all_unprocessed_of_a_npc, latest_unprocessed_of_a_npc

def get_all_unprocessed_entries(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    query = """
    SELECT * FROM behavior_java_buffer 
    WHERE isProcessed = FALSE
    ORDER BY time ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()
    if results:
        print("Unprocessed entries:")
        for result in results:
            print(f"time={result[1]}, npcId={result[2]}, content length={len(result[3])}")
        return results
    else:
        print("No unprocessed entries found.")
        return []

def mark_entry_as_processed_bynpctime(connection, time, npcId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    update_query = """
    UPDATE behavior_java_buffer
    SET isProcessed = TRUE
    WHERE time = %s AND npcId = %s
    """
    cursor.execute(update_query, (time, npcId))
    connection.commit()
    print(f"Entry with time={time} and npcId={npcId} marked as processed.")

def mark_entry_as_processed(connection, requestId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    update_query = """
    UPDATE behavior_java_buffer
    SET isProcessed = TRUE
    WHERE requestId = %s
    """
    cursor.execute(update_query, (requestId,))
    connection.commit()
    print(f"Entry with requestId={requestId} marked as processed.")

def mark_all_entries_as_processed(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    update_query = """
    UPDATE behavior_java_buffer
    SET isProcessed = TRUE
    """
    cursor.execute(update_query)
    connection.commit()
    print("All entries have been marked as processed, keeping 'isBeingProcessed' unchanged.")

def mark_entry_as_fullyprocessed(connection, requestId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    update_query = """
    UPDATE behavior_java_buffer
    SET isFullyProcessed = TRUE
    WHERE requestId = %s
    """
    cursor.execute(update_query, (requestId,))
    connection.commit()
    print(f"Entry with requestId={requestId} marked as fully processed.")