import json
import mysql.connector
from mysql.connector import Error
import pickle  # To serialize and deserialize Python objects (like the embedding list)
import pandas as pd

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
    cursor.execute("USE AITown")  # Use the AITown database
    create_table_query = """
    CREATE TABLE IF NOT EXISTS comment_reply_memeory_stream (
        npcID VARCHAR(255) NOT NULL,
        Time DATETIME NOT NULL,
        isInstruction BOOLEAN DEFAULT FALSE,
        Content LONGTEXT,
        Importance INT CHECK (Importance BETWEEN 1 AND 10),
        Embedding BLOB,
        sname VARCHAR(255),
        isBeingProcessed BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (npcID, Time, isInstruction)
    )
    """
    cursor.execute(create_table_query)
    print("Table 'comment_reply_memeory_stream' checked/created successfully.")

def delete_table(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    delete_table_query = "DROP TABLE IF EXISTS comment_reply_memeory_stream"
    cursor.execute(delete_table_query)
    connection.commit()
    print("Table 'comment_reply_memeory_stream' has been deleted successfully.")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'comment_reply_memeory_stream'
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

def insert_into_table(connection, npcID, time, isInstruction, content, importance, embedding, sname):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    embedding_blob = pickle.dumps(embedding)
    insert_query = """
    INSERT INTO comment_reply_memeory_stream (npcID, Time, isInstruction, Content, Importance, Embedding, sname)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE Content = VALUES(Content), Importance = VALUES(Importance), Embedding = VALUES(Embedding), sname = VALUES(sname)
    """
    cursor.execute(insert_query, (npcID, time, isInstruction, content, importance, embedding_blob, sname))
    connection.commit()
    print(f"Data inserted successfully: npcID={npcID}, time={time}, isInstruction={isInstruction}, content length={len(content)}, importance={importance}")

def retrieve_entry(connection, npcID, time, isInstruction):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    select_query = "SELECT Content, Importance, Embedding, sname FROM comment_reply_memeory_stream WHERE npcID = %s AND Time = %s AND isInstruction = %s"
    cursor.execute(select_query, (npcID, time, isInstruction))
    result = cursor.fetchone()
    if result:
        content, importance, embedding_blob, sname = result
        embedding = pickle.loads(embedding_blob)
        print(f"Retrieved entry: content={content}, importance={importance}, embedding length={len(embedding)}, sname={sname}")
        return content, importance, embedding, sname
    else:
        print(f"No entry found for npcID={npcID}, time={time}, isInstruction={isInstruction}")
        return None

def delete_entry_in_buffer(connection, npcID, time, isInstruction):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    delete_query = "DELETE FROM comment_reply_memeory_stream WHERE npcID = %s AND Time = %s AND isInstruction = %s"
    cursor.execute(delete_query, (npcID, time, isInstruction))
    connection.commit()
    print(f"Entry with npcID={npcID}, time={time}, isInstruction={isInstruction} has been deleted successfully.")

def delete_all_content_in_buffer(connection):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    delete_query = "DELETE FROM comment_reply_memeory_stream"
    cursor.execute(delete_query)
    connection.commit()
    print("All content in the 'comment_reply_memeory_stream' table has been deleted successfully.")

def retrieve_most_recent_entries(connection, npcID, before_time, sname, limit=300):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    select_query = """
    SELECT npcID, Time, isInstruction, Content, Importance, Embedding, sname
    FROM comment_reply_memeory_stream
    WHERE npcID = %s AND Time < %s AND sname = %s
    ORDER BY Time DESC
    LIMIT %s
    """
    cursor.execute(select_query, (npcID, before_time, sname, limit))
    results = cursor.fetchall()

    data = []
    for result in results:
        npcID, time, isInstruction, content, importance, embedding_blob, sname = result
        embedding = pickle.loads(embedding_blob)
        data.append([npcID, time, isInstruction, content, importance, embedding, sname])

    columns = ['npcID', 'Time', 'isInstruction', 'Content', 'Importance', 'Embedding', 'sname']
    df = pd.DataFrame(data, columns=columns)
    
    print(f"Retrieved {len(df)} entries for npcID={npcID} before time={before_time}")
    return df

def retrieve_entries_between_time(connection, npcID, start_time, end_time, limit=300):
    cursor = connection.cursor()
    cursor.execute("USE AITown")
    select_query = """
    SELECT npcID, Time, isInstruction, Content, Importance, Embedding, sname
    FROM comment_reply_memeory_stream
    WHERE npcID = %s AND Time BETWEEN %s AND %s
    ORDER BY Time ASC
    LIMIT %s
    """
    cursor.execute(select_query, (npcID, start_time, end_time, limit))
    results = cursor.fetchall()

    data = []
    for result in results:
        npcID, time, isInstruction, content, importance, embedding_blob, sname = result
        embedding = pickle.loads(embedding_blob)
        data.append([npcID, time, isInstruction, content, importance, embedding, sname])

    columns = ['npcID', 'Time', 'isInstruction', 'Content', 'Importance', 'Embedding', 'sname']
    df = pd.DataFrame(data, columns=columns)
    
    print(f"Retrieved {len(df)} entries for npcID={npcID} between {start_time} and {end_time}")
    return df