import sys
import os
import socket
import struct
import configparser
import time
import json
import copy
import traceback
import datetime
import threading

# Add the base directory (one level up from the current directory)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

from DBConnect.DBCon import establish_sql_connection, close_sql_connection
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import CmtRpyDBJavaBuffer
from DBConnect import CmtRpyDBInstruction
from DBConnect import AnnDBJavaBuffer
from DBConnect import AnnDBInstruction

import header_pb2
import Message_pb2
import server_node_pb2

# Define sock and config as global variables
sock = None
config = None

# Load config.ini once at the beginning
def load_config():
    config = configparser.ConfigParser()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config.ini')
    
    if os.path.exists(config_path):
        config.read(config_path)
        print("Config sections found:", config.sections())
    else:
        print(f"Error: config.ini not found at {config_path}")
        exit(1)
    
    # Check required sections
    if 'NetworkSocket' not in config:
        print("Error: 'NetworkSocket' section not found in config.ini")
        exit(1)
    if 'mysql' not in config:
        print("Error: 'mysql' section not found in config.ini")
        exit(1)

    return config

def build_packet_buffer(header_data, message_data):
    header_length = len(header_data)
    message_length = len(message_data)
    
    # Construct the byte buffer by writing header length, header data, message length, and message data
    byte_buffer = struct.pack('>I', header_length) + header_data + struct.pack('>I', message_length) + message_data
    return byte_buffer

def wrap_packet_buffer(byte_buffer_data):
    length = len(byte_buffer_data)
    # Construct a new byte buffer with total length and the byte buffer data
    new_raw_data = struct.pack('>I', length) + byte_buffer_data
    return new_raw_data

def make_header(command, config):
    header = header_pb2.Header()
    header.rtype = "!"
    header.command = command
    # header.source = config['DEFAULT']['source']
    header.source = "app.z1.s2.A1"
    header.destination = "app.z1.s2.P1"
    header.code = 0
    header.dstScope = 0
    header.cmd = 0
    return header.SerializeToString()

def make_message(input_text):
    message = Message_pb2.Message()
    message.content = bytes(input_text, 'utf-8')
    return message.SerializeToString()

def ip_to_int(ip_address):
    packed_ip = socket.inet_aton(ip_address)
    return struct.unpack("!I", packed_ip)[0]

def make_node_message():
    node = server_node_pb2.server_node()
    # Node ID
    node.node_id = "app.z1.s2.A1"
    # IP Address converted to int type
    node.ip_lan = 1111111
    # Port
    node.port_lan = 2528
    # Fixed value: connection channel mode
    node.channel = 0
    # Node type: fixed value, 'A' represents Python AI service
    node.type = "A"

    message = Message_pb2.Message()
    message.content = node.SerializeToString()
    return message.SerializeToString()

def parse_response(response, is_iterative=True): 
    if is_iterative:
        total_length = struct.unpack('>I', response[:4])[0]
        packet_data = response[4:4 + total_length]
    else:
        packet_data = response

    # Parse Header length
    header_length = struct.unpack('>I', packet_data[:4])[0]
    header_data = packet_data[4:4 + header_length]
    header = header_pb2.Header()
    header.ParseFromString(header_data)

    # Parse Message length
    message_length_start = 4 + header_length
    message_length = struct.unpack('>I', packet_data[message_length_start:message_length_start + 4])[0]
    message_data_start = message_length_start + 4
    message_data = packet_data[message_data_start:message_data_start + message_length]
    message = Message_pb2.Message()
    message.ParseFromString(message_data)

    return header, message

def receive_input():
    global sock
    response = sock.recv(4096)
    # print(response)
    # print('Received response (receiving):')

    header, message = parse_response(response, is_iterative=True)
    # print(f'Header: {header}')
    # print(f'Message: {message.content.decode("utf-8")}')
    response_from_java = message.content.decode("utf-8")
    return response_from_java

def receive_input_long():
    global sock
    while True:
        try:
            length_bytes = sock.recv(4)
            
            if not length_bytes:
                print("Detected lost connection. Attempting to reconnect.")
                reconnect_and_replace_socket(ip_java, port_java)
                continue  # Retry receiving data with the new connection
            
            data_length = int.from_bytes(length_bytes, 'big')
            total_data_length = data_length
            received_data = b""
            
            while len(received_data) < total_data_length:
                data = sock.recv(min(4096, total_data_length - len(received_data)))
                if not data:
                    print("Connection closed by peer before sending all data. Reconnecting...")
                    reconnect_and_replace_socket(ip_java, port_java)
                    break
                received_data += data
            
            response = received_data
            # print('Received responses
            header, message = parse_response(response, is_iterative=False)
            print(f'Header: {header}')
            print(f'Message: {message.content.decode("utf-8")}')
            output = message.content.decode("utf-8")
            return output
        
        except Exception as e:
            print(f"Error in receive_input_long: {e}")
            traceback.print_exc()
            reconnect_and_replace_socket(ip_java, port_java)

def execute_instruction(instruction, head_num):
    global sock, config
    try:
        header_data = make_header(head_num, config)
        message_data = make_message(instruction)
        packet_data = build_packet_buffer(header_data, message_data)
        wrapped_packet_data = wrap_packet_buffer(packet_data)

        sock.sendall(wrapped_packet_data)
    except Exception as e:
        print(f"Error sending instruction: {e}")
        traceback.print_exc()
        reconnect_and_replace_socket(ip_java, port_java)

def create_socket(ip_txt, port_int):
    global sock, config
    # Read configuration
    config = configparser.ConfigParser()
    config.read('config.properties')

    # Register node data with Java service
    node_header_data = make_header(-1, config)
    node_message_data = make_node_message()
    packet_node_data = build_packet_buffer(node_header_data, node_message_data)
    wrapped_packet_node_data = wrap_packet_buffer(packet_node_data)

    # Create a connection with the Java service
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip_txt, port_int)
    print(f'Connecting to {server_address[0]} port {server_address[1]}')
    sock.connect(server_address)

    # Now 'sock' is assigned globally

    # Register current server node information: send node registration message
    sock.sendall(wrapped_packet_node_data)
    initial_back = receive_input()
    # No need to return 'sock'

def is_socket_connected():
    global sock
    if not sock:
        return False
    try:
        # Use getsockopt to check for socket errors
        error_code = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        return error_code == 0  # If error_code is 0, the socket is connected
    except socket.error as e:
        print(f'Socket error: {e}')
        return False

def reconnect_socket(ip_txt, port_int, max_retries = 100000000000000000):
    attempt = 0
    while True:
        # try:
        # Create and connect the socket
        create_socket(ip_txt, port_int)

        # Check if the socket is connected
        if is_socket_connected():
            print("Socket is connected.")
            return
        else:
            print("Socket not connected. Reconnecting...")
        # except Exception as e:
        #     print(f"Error connecting socket: {e}")
        
        # Wait before attempting to reconnect
        time.sleep(5)  # Wait 5 seconds before retrying
        attempt += 1
        if attempt >= max_retries:
            print(f"Reconnection attempt {attempt} of {max_retries} failed.")
            break

    # If all attempts fail, exit or handle as needed
    print("Max reconnection attempts reached. Unable to connect.")
    exit(1)

# Function to handle reconnection and update the global socket
def reconnect_and_replace_socket(ip_txt, port_int):
    print("Reconnecting socket...")
    reconnect_socket(ip_txt, port_int)
    print("Reconnection successful.")

def receive_data():
    global sock
    while True:
        try:
            print("Waiting to receive data...")
            input_from_java = receive_input_long()
            print("Received input from Java")

            # Parse input
            data = json.loads(input_from_java)
            print("Command Type is: ", data['command'])
            print("Parsed input successfully:", data)

            db_connection = None

            # if data['command'] == 10106:
            #     # NPC Announcement
            #     try:
            #         requestId = data['requestId']
            #         npcInputSingle = data['data']
            #         dt_object = datetime.datetime.fromtimestamp(npcInputSingle['world']['time'] / 1000.0)
            #         time_stamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')  # Format to MySQL datetime format
            #         npcId = npcInputSingle['npcs'][0]['npcId']
                    
            #         content = json.dumps(npcInputSingle)  # Convert the content to JSON format
            #         db_connection = establish_sql_connection()
            #         # Insert into table using formatted datetime string
            #         AnnDBJavaBuffer.insert_into_table(db_connection, requestId, time_stamp, int(npcId), content)
            #     except Exception as e:
            #         print(f"Failed to insert into Announcement Java Buffer for requestId {requestId} npcId {npcId}: {e}")
            #         traceback.print_exc()
            #     else:
            #         print(f"Insertion into Announcement for requestId {requestId} npcId {npcId} inserted successfully.")

            if data['command'] == 10101:
                # NPC Behavior
                try:
                    requestId = data['requestId']
                    npcInputSingle = data['data']
                    if "mapObj" in npcInputSingle:
                        del npcInputSingle["mapObj"] # No need for data mapObj now, distraction
                    dt_object = datetime.datetime.fromtimestamp(npcInputSingle['world']['time'] / 1000.0)
                    time_stamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')  # Format to MySQL datetime format
                    npcId = npcInputSingle['npcs'][0]['npcId']
                    
                    content = json.dumps(npcInputSingle)  # Convert the content to JSON format
                    db_connection = establish_sql_connection()
                    # Insert into table using formatted datetime string
                    print(requestId, time_stamp, npcId, content)
                    BhrDBJavaBuffer.insert_into_table(db_connection, requestId, time_stamp, int(npcId), content)
                except Exception as e:
                    print(f"Failed to insert into Behavior Java Buffer for requestId {requestId}: {e}")
                    traceback.print_exc()

            if data['command'] == 10103:
                # NPC reply to comment from player
                try:
                    playerCommentData = data['data']
                    npcId = playerCommentData['npcId']
                    requestId = data['requestId']
                    senderId = playerCommentData['chatData']['sender']
                    msgId = playerCommentData['chatData']['msgId']
                    content = playerCommentData['chatData']['content']
                    sname = playerCommentData['chatData']['sname']
                    privateMsg = playerCommentData['chatData']['privateMsg']
                    dt_object = datetime.datetime.fromtimestamp(playerCommentData['chatData']['time'] / 1000.0)
                    time_stamp = dt_object.strftime('%Y-%m-%d %H:%M:%S') 
                    db_connection = establish_sql_connection()

                    CmtRpyDBJavaBuffer.insert_into_table(db_connection, requestId, time_stamp, npcId, msgId, senderId, content, sname, False, False, privateMsg)
                except Exception as e:
                    print(f"Failed to insert into CommentReply Java Buffer for requestId {requestId} npcId {npcId}: {e}")
                    traceback.print_exc()

                if db_connection:
                    close_sql_connection(db_connection)
            else:
                print('Unknown case')
                print(data)
            print("\n")
            
        except Exception as e:
            print(f"Error in receive_data: {e}")
            traceback.print_exc()

def send_data():
    global sock, config
    while True:
        print("Checking for unprocessed instructions...")
        try:
            db_conn = establish_sql_connection()


            # instruction_from_db = AnnDBInstruction.get_earliest_unprocessed_instruction(db_conn)
            # print(f"Instruction from DB: {instruction_from_db}")
            # if instruction_from_db is not None:
            #     curTime, npcId, instruction_str = instruction_from_db[0], instruction_from_db[1], instruction_from_db[2]
            #     head_num = 10100  # Set the appropriate head_num or pull dynamically if needed
            #     print('Sending instruction:', instruction_str)
            #     # Execute the instruction and mark it as processed
            #     execute_instruction(instruction_str, head_num)
            #     AnnDBInstruction.mark_instruction_as_processed(db_conn, curTime, npcId)
            #     print(f"Sent instruction: {instruction_str} for npcId {npcId} and marked as processed.")
            # else:
            #     print("No unprocessed instructions found.")
            #     time.sleep(1)  # Sleep for 5 seconds before checking again

            behavior_instruction_from_db = BhrDBInstruction.get_earliest_unprocessed_instruction(db_conn)
            print(f"Behavior Instruction from DB: {behavior_instruction_from_db}")
            if behavior_instruction_from_db is not None:
                curTime, npcId, instruction_str = behavior_instruction_from_db[0], behavior_instruction_from_db[1], behavior_instruction_from_db[2]
                head_num = 10100  # Set the appropriate head_num or pull dynamically if needed
                print('Sending Behavior instruction:', instruction_str)
                # Execute the instruction and mark it as processed
                execute_instruction(instruction_str, head_num)
                BhrDBInstruction.mark_instruction_as_processed(db_conn, curTime, npcId)
                print(f"Sent Behavior instruction: {instruction_str} for npcId {npcId} and marked as processed.")
            else:
                print("No unprocessed Behavior instructions found.")

            comment_instruction_from_db = CmtRpyDBInstruction.get_earliest_unprocessed_instruction(db_conn)
            print(f"Comment CommentReply Instruction from DB: {comment_instruction_from_db}")
            if comment_instruction_from_db is not None:
                requestId, instruction_str = comment_instruction_from_db[0], comment_instruction_from_db[4]
                head_num = 10100  # Set the appropriate head_num or pull dynamically if needed
                print('Sending CommentReply instruction:', instruction_str)
                # Execute the instruction and mark it as processed
                execute_instruction(instruction_str, head_num)
                CmtRpyDBInstruction.mark_instruction_as_processed(db_conn, requestId)
                print(f"Sent CommentReply instruction: {instruction_str} for requestId {requestId} and marked as processed.")
            else:
                print("No unprocessed CommentReply instructions found.")
            close_sql_connection(db_conn)
            time.sleep(1) 
        except Exception as e:
            print(f"Error in send_data: {e}")
            traceback.print_exc()
            time.sleep(1)

if __name__ == "__main__":
    config = load_config()

    # Check if the required sections are in config.ini
    if 'NetworkSocket' not in config:
        print("Error: 'NetworkSocket' section not found in config.ini")
        exit(1)
    if 'mysql' not in config:
        print("Error: 'mysql' section not found in config.ini")
        exit(1)
    
    # Access the config values
    ip_java = config['NetworkSocket']['ip_java']
    port_java = int(config['NetworkSocket']['port_java'])

    # Create socket and set to blocking mode (default mode)
    reconnect_socket(ip_java, port_java)

    db_conn_temp = establish_sql_connection()
    BhrDBJavaBuffer.mark_all_entries_as_processed(db_conn_temp)
    close_sql_connection(db_conn_temp)
    
    # Initial command to execute before starting threads
    init_command = '''
    {"command": 10102, "data": {"init": true}}
    '''
    header_number = 10102

    # Execute the initial instruction with the init_command and header_number 10102
    print("Executing initial command before starting threads...")
    execute_instruction(init_command, header_number)

    # Start the receiving and sending threads
    receive_thread = threading.Thread(target=receive_data)
    send_thread = threading.Thread(target=send_data)

    # Set threads as daemons so they exit when the main program exits
    receive_thread.daemon = True
    send_thread.daemon = True

    # Start both threads
    print('Starting receiving data...')
    receive_thread.start()
    print('Starting sending data...')
    send_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(45)
            # time.sleep(300) 
            db_conn_temp = establish_sql_connection()
            BhrDBJavaBuffer.mark_all_entries_as_processed(db_conn_temp)
            close_sql_connection(db_conn_temp)
            init_command = '''
            {"command": 10102, "data": {"init": false}}
            '''
            header_number = 10102
            execute_instruction(init_command, header_number)
            
            # time.sleep(1)# Keep main thread alive to allow threads to run
    except KeyboardInterrupt:
        print("Interrupted, closing socket.")
        if sock:
            sock.close()


