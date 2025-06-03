import mysql.connector
from mysql.connector import Error

# Connection health check
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

# Database management
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
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS AITown")
    print("Database 'AITown' checked/created successfully.")


def database_exists(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'AITown'")
    result = cursor.fetchone()
    if result:
        print("Database 'AITown' exists.")
        return True
    else:
        print("Database 'AITown' does not exist.")
        return False

# Table management
def create_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS behavior_java_buffer (
        requestId BIGINT NOT NULL,
        time DATETIME NOT NULL,
        npcId INT NOT NULL,
        content LONGTEXT,
        isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        isBeingProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        isFullyProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (requestId, time)
    )"""
    )
    print("Table 'behavior_java_buffer' checked/created successfully.")


def delete_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute("DROP TABLE IF EXISTS behavior_java_buffer")
    connection.commit()
    print("Table behavior_java_buffer has been deleted successfully.")


def table_exists(connection):
    cursor = connection.cursor()
    cursor.execute(
        """SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'AITown' AND TABLE_NAME = 'behavior_java_buffer'"""
    )
    result = cursor.fetchone()
    if result:
        print("Table 'behavior_java_buffer' exists in database 'AITown'.")
        return True
    else:
        print("Table 'behavior_java_buffer' does not exist in database 'AITown'.")
        return False

# Data operations
def insert_into_table(connection, requestId, time, npcId, content, isProcessed=False, isBeingProcessed=False):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """INSERT INTO behavior_java_buffer (requestId, time, npcId, content, isProcessed, isBeingProcessed)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content), isProcessed = VALUES(isProcessed)""",
        (requestId, time, npcId, content, isProcessed, isBeingProcessed),
    )
    connection.commit()
    print(f"Data inserted successfully: requestId={requestId}, time={time}, npcId={npcId}, content length={len(content)}, isProcessed={isProcessed}")


def delete_entry_in_buffer(connection, time, npcId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute("DELETE FROM behavior_java_buffer WHERE time = %s AND npcId = %s", (time, npcId))
    connection.commit()
    print(f"Entry with time={time} and npcId={npcId} has been deleted successfully.")


def delete_all_content_in_buffer(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute("DELETE FROM behavior_java_buffer")
    connection.commit()
    print("All content in the 'behavior_java_buffer' table has been deleted successfully.")

# Job queue operations without Python-level lock or pool

def get_earliest_unprocessed_entry(connection):
    """
    Atomically claim the earliest unprocessed job using
    SELECT ... FOR UPDATE SKIP LOCKED in a short transaction.
    """
    cursor = connection.cursor(dictionary=True)
    try:
        # start a transaction
        connection.start_transaction()
        cursor.execute("USE AITown")
        # lock and fetch one unclaimed job
        cursor.execute(
            """
            SELECT requestId, time, npcId, content
            FROM behavior_java_buffer
            WHERE isProcessed = FALSE AND isBeingProcessed = FALSE
            ORDER BY time ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        row = cursor.fetchone()

        if not row:
            connection.commit()
            print("No unprocessed entries found.")
            return None

        # mark as being processed
        cursor.execute(
            """
            UPDATE behavior_java_buffer
            SET isBeingProcessed = TRUE
            WHERE requestId = %s AND time = %s
            """,
            (row['requestId'], row['time']),
        )

        connection.commit()
        print(f"Claimed job: requestId={row['requestId']}, time={row['time']}")
        return (row['requestId'], row['time'], row['npcId'], row['content'], False, True)
    except Error as e:
        connection.rollback()
        print(f"Error claiming job: {e}")
        return None


def get_unprocessed_entries_of_npc(connection, npcId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """
        SELECT * FROM behavior_java_buffer
        WHERE isProcessed = FALSE AND npcId = %s
        ORDER BY time ASC
        """,
        (npcId,),
    )
    all_unprocessed = cursor.fetchall()

    cursor.execute(
        """
        SELECT * FROM behavior_java_buffer
        WHERE isProcessed = FALSE AND npcId = %s
        ORDER BY time DESC
        LIMIT 1
        """,
        (npcId,),
    )
    latest = cursor.fetchone()

    if all_unprocessed:
        print(f"Found {len(all_unprocessed)} unprocessed entries for npcId={npcId}.")
    else:
        print(f"No unprocessed entries found for npcId={npcId}.")

    if latest:
        print(f"Latest unprocessed entry for npcId={npcId}: time={latest[1]}")
    else:
        print(f"No latest unprocessed entry found for npcId={npcId}.")

    return all_unprocessed, latest


def get_all_unprocessed_entries(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """
        SELECT * FROM behavior_java_buffer
        WHERE isProcessed = FALSE
        ORDER BY time ASC
        """
    )
    results = cursor.fetchall()
    if results:
        print("Unprocessed entries:")
        for r in results:
            print(f"time={r[1]}, npcId={r[2]}, content length={len(r[3])}")
        return results
    else:
        print("No unprocessed entries found.")
        return []


def mark_entry_as_processed_bynpctime(connection, time, npcId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """
        UPDATE behavior_java_buffer
        SET isProcessed = TRUE
        WHERE time = %s AND npcId = %s
        """,
        (time, npcId),
    )
    connection.commit()
    print(f"Entry with time={time} and npcId={npcId} marked as processed.")


def mark_entry_as_processed(connection, requestId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """
        UPDATE behavior_java_buffer
        SET isProcessed = TRUE
        WHERE requestId = %s
        """,
        (requestId,),
    )
    connection.commit()
    print(f"Entry with requestId={requestId} marked as processed.")


def mark_all_entries_as_processed(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute("UPDATE behavior_java_buffer SET isProcessed = TRUE")
    connection.commit()
    print("All entries have been marked as processed, keeping 'isBeingProcessed' unchanged.")


def mark_entry_as_fullyprocessed(connection, requestId):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    cursor.execute(
        """
        UPDATE behavior_java_buffer
        SET isFullyProcessed = TRUE
        WHERE requestId = %s
        """,
        (requestId,),
    )
    connection.commit()
    print(f"Entry with requestId={requestId} marked as fully processed.")
