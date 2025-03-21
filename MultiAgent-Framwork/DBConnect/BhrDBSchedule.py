import mysql.connector
from mysql.connector import Error
import pandas as pd

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
            
def table_exists(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    check_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'AITown' AND TABLE_NAME = 'behavior_schedule_stream'
    """
    cursor.execute(check_query)
    result = cursor.fetchone()

    if result:
        print("Table 'behavior_schedule_stream' exists in database 'AITown'.")
        return True
    else:
        print("Table 'behavior_schedule_stream' does not exist in database 'AITown'.")
        return False

def create_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")  # Use the AITown database
    create_table_query = """
    CREATE TABLE IF NOT EXISTS behavior_schedule_stream (
        npcID VARCHAR(255) NOT NULL,
        Time DATETIME NOT NULL,
        Schedule LONGTEXT,
        PRIMARY KEY (npcID, Time)
    )
    """
    cursor.execute(create_table_query)
    print("Table 'behavior_schedule_stream' checked/created successfully.")

def insert_into_table(connection, npcID, time, schedule):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    insert_query = """
    INSERT INTO behavior_schedule_stream (npcID, Time, Schedule)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE Schedule = VALUES(Schedule)
    """
    cursor.execute(insert_query, (npcID, time, schedule))
    connection.commit()
    print(f"Data inserted successfully: npcID={npcID}, time={time}, schedule length={len(schedule)}")

def retrieve_entry(connection, npcID, time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = "SELECT Schedule FROM behavior_schedule_stream WHERE npcID = %s AND Time = %s"
    cursor.execute(select_query, (npcID, time))
    result = cursor.fetchone()
    if result:
        schedule = result[0]
        print(f"Retrieved entry: schedule={schedule}")
        return schedule
    else:
        print(f"No entry found for npcID={npcID}, time={time}")
        return None

def delete_entry(connection, npcID, time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_query = "DELETE FROM behavior_schedule_stream WHERE npcID = %s AND Time = %s"
    cursor.execute(delete_query, (npcID, time))
    connection.commit()
    print(f"Entry with npcID={npcID}, time={time} has been deleted successfully.")

def delete_all_content(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_query = "DELETE FROM behavior_schedule_stream"
    cursor.execute(delete_query)
    connection.commit()
    print("All content in the 'behavior_schedule_stream' table has been deleted successfully.")

def retrieve_entries_between_time(connection, npcID, start_time, end_time, limit=300):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = """
    SELECT npcID, Time, Schedule
    FROM behavior_schedule_stream
    WHERE npcID = %s AND Time BETWEEN %s AND %s
    ORDER BY Time ASC
    LIMIT %s
    """
    cursor.execute(select_query, (npcID, start_time, end_time, limit))
    results = cursor.fetchall()

    # Prepare data for DataFrame
    data = []
    for result in results:
        npcID, time, schedule = result
        data.append([npcID, time, schedule])

    # Define DataFrame columns
    columns = ['npcID', 'Time', 'Schedule']

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    print(f"Retrieved {len(df)} entries for npcID={npcID} between {start_time} and {end_time}")
    return df

def retrieve_last_entry_before_time(connection, npcID, before_time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = """
    SELECT npcID, Time, Schedule
    FROM behavior_schedule_stream
    WHERE npcID = %s AND Time < %s
    ORDER BY Time DESC
    LIMIT 1
    """
    cursor.execute(select_query, (npcID, before_time))
    result = cursor.fetchone()

    if result:
        npcID, time, schedule = result
        print(f"Retrieved last entry before {before_time}: npcID={npcID}, time={time}, schedule={schedule}")
        return npcID, time, schedule
    else:
        print(f"No entries found for npcID={npcID} before {before_time}")
        return None

def retrieve_latest_schedule(connection, npcID):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    
    # Query to get the latest schedule
    select_query = """
    SELECT npcID, Time, Schedule
    FROM behavior_schedule_stream
    WHERE npcID = %s
    ORDER BY Time DESC
    LIMIT 1
    """
    cursor.execute(select_query, (npcID,))
    result = cursor.fetchone()

    if result:
        npcID, time, schedule = result
        print(f"Latest schedule retrieved: npcID={npcID}, time={time}, schedule={schedule}")
        return {
            "npcID": npcID,
            "time": time,
            "schedule": schedule
        }
    else:
        print(f"No schedule found for npcID={npcID}")
        return None