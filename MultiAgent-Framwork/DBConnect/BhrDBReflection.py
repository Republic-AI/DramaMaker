import mysql.connector
from mysql.connector import Error
import configparser
import os
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

def create_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")  # Use the AITown database
    create_table_query = """
    CREATE TABLE IF NOT EXISTS behavior_reflection_stream (
        npcID VARCHAR(255) NOT NULL,
        Time DATETIME NOT NULL,
        Content LONGTEXT,
        PRIMARY KEY (npcID, Time)
    )
    """
    cursor.execute(create_table_query)
    print("Table 'behavior_reflection_stream' checked/created successfully.")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'behavior_reflection_stream'
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

def insert_into_table(connection, npcID, time, content):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    insert_query = """
    INSERT INTO behavior_reflection_stream (npcID, Time, Content)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE Content = VALUES(Content)
    """
    cursor.execute(insert_query, (npcID, time, content))
    connection.commit()
    print(f"Data inserted successfully: npcID={npcID}, time={time}, content length={len(content)}")

def retrieve_entry(connection, npcID, time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = "SELECT Content FROM behavior_reflection_stream WHERE npcID = %s AND Time = %s"
    cursor.execute(select_query, (npcID, time))
    result = cursor.fetchone()
    if result:
        content = result[0]
        print(f"Retrieved entry: content={content}")
        return content
    else:
        print(f"No entry found for npcID={npcID}, time={time}")
        return None

def delete_entry(connection, npcID, time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_query = "DELETE FROM behavior_reflection_stream WHERE npcID = %s AND Time = %s"
    cursor.execute(delete_query, (npcID, time))
    connection.commit()
    print(f"Entry with npcID={npcID}, time={time} has been deleted successfully.")

def delete_all_content(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_query = "DELETE FROM behavior_reflection_stream"
    cursor.execute(delete_query)
    connection.commit()
    print("All content in the 'behavior_reflection_stream' table has been deleted successfully.")

def retrieve_entries_between_time(connection, npcID, start_time, end_time, limit=300):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = """
    SELECT npcID, Time, Content
    FROM behavior_reflection_stream
    WHERE npcID = %s AND Time BETWEEN %s AND %s
    ORDER BY Time ASC
    LIMIT %s
    """
    cursor.execute(select_query, (npcID, start_time, end_time, limit))
    results = cursor.fetchall()

    data = []
    for result in results:
        npcID, time, content = result
        data.append([npcID, time, content])

    columns = ['npcID', 'Time', 'Content']
    df = pd.DataFrame(data, columns=columns)
    
    print(f"Retrieved {len(df)} entries for npcID={npcID} between {start_time} and {end_time}")
    return df

def retrieve_last_entry_before_time(connection, npcID, before_time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = """
    SELECT npcID, Time, Content
    FROM behavior_reflection_stream
    WHERE npcID = %s AND Time < %s
    ORDER BY Time DESC
    LIMIT 1
    """
    cursor.execute(select_query, (npcID, before_time))
    result = cursor.fetchone()

    if result:
        npcID, time, content = result
        print(f"Retrieved last entry before {before_time}: npcID={npcID}, time={time}, content={content}")
        return npcID, time, content
    else:
        print(f"No entries found for npcID={npcID} before {before_time}")
        return None