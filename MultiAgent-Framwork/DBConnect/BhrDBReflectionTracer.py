import mysql.connector
from mysql.connector import Error
import configparser
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

def create_database(connection, db_name):
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
    cursor.execute("USE Dramai")  # Use the AITown database
    create_table_query = """
    CREATE TABLE IF NOT EXISTS behavior_reflection_tracer (
        npcID VARCHAR(255) NOT NULL,
        total_importance INT CHECK (total_importance >= 0),
        start_Time DATETIME NOT NULL,
        end_Time DATETIME NOT NULL,
        PRIMARY KEY (npcID)
    )
    """
    cursor.execute(create_table_query)
    print("Table 'behavior_reflection_tracer' checked/created successfully.")

def delete_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_table_query = "DROP TABLE IF EXISTS behavior_reflection_tracer"
    cursor.execute(delete_table_query)
    connection.commit()
    print("Table 'behavior_reflection_tracer' has been deleted successfully.")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'behavior_reflection_tracer'
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

def insert_into_table(connection, npcID, total_importance, start_time, end_time):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    insert_query = """
    INSERT INTO behavior_reflection_tracer (npcID, total_importance, start_Time, end_Time)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE total_importance = VALUES(total_importance), start_Time = VALUES(start_Time), end_Time = VALUES(end_Time)
    """
    cursor.execute(insert_query, (npcID, total_importance, start_time, end_time))
    connection.commit()
    print(f"Data inserted successfully: npcID={npcID}, total_importance={total_importance}, start_time={start_time}, end_time={end_time}")

def retrieve_entry(connection, npcID):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    select_query = "SELECT total_importance, start_Time, end_Time FROM behavior_reflection_tracer WHERE npcID = %s"
    cursor.execute(select_query, (npcID,))
    result = cursor.fetchone()
    if result:
        total_importance, start_time, end_time = result
        print(f"Retrieved entry: npcID={npcID}, total_importance={total_importance}, start_time={start_time}, end_time={end_time}")
        return total_importance, start_time, end_time
    else:
        print(f"No entry found for npcID={npcID}")
        return None

def delete_entry_in_table(connection, npcID):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_query = "DELETE FROM behavior_reflection_tracer WHERE npcID = %s"
    cursor.execute(delete_query, (npcID,))
    connection.commit()
    print(f"Entry with npcID={npcID} has been deleted successfully.")

def delete_all_entries(connection):
    cursor = connection.cursor()
    cursor.execute("USE Dramai")
    delete_query = "DELETE FROM behavior_reflection_tracer"
    cursor.execute(delete_query)
    connection.commit()
    print("All entries in the 'behavior_reflection_tracer' table have been deleted successfully.")