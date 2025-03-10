import mysql.connector
from mysql.connector import Error
import configparser
import os

def establish_sql_connection():
    # Print the current working directory for debugging
    print("Current working directory:", os.getcwd())
    
    config = configparser.ConfigParser()
    # Adjust the path to locate config.ini one level above this file's directory
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"Error: config.ini not found at {config_path}")
        return None
    
    config.read(config_path)
    
    print("Config sections found:", config.sections())
    
    if 'mysql' not in config:
        print("Error: 'mysql' section not found in config.ini")
        return None
    

    connection = mysql.connector.connect(
        host=config['mysql']['host'],
        user=config['mysql']['user'],
        password=config['mysql']['password']
    )
    if connection.is_connected():
        print("Connected to MySQL server successfully")
    return connection

def close_sql_connection(connection):
    if connection.is_connected():
        connection.close()
        print("Connection closed successfully.")
    else:
        print("Connection was already closed.")

def check_and_reconnect(connection):
    """
    Check if the connection is active, and reconnect if it is broken.
    """
    try:
        if connection is None or not connection.is_connected():
            print("Connection is not active. Attempting to reconnect...")
            connection = establish_sql_connection()
        else:
            # Ping the server to ensure the connection is still valid
            connection.ping(reconnect=True, attempts=3, delay=2)
            print("Connection is active.")
    except Error as e:
        print(f"Error during connection check/reconnection: {e}")
        connection = establish_sql_connection()
    
    return connection



def is_connected(connection):
    """
    Check if the given MySQL connection is active.
    """
    try:
        if connection is not None:
            # Use ping to check if the connection is still valid
            connection.ping(reconnect=False, attempts=1, delay=0)
            return True
        else:
            return False
    except:
        return False