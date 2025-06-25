import sys
import os

# Add the DBmanipulation folder to the Python path

import DBConnect.DBCon as DBCon

from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflectionTracer

import json
import re

import pickle

import BhrLgcGPTProcess
import BhrLgcManualProcess

# memstre_db_connection = DBCon.establish_sql_connection()

def InstToMemStreDB(input_from_java, memeory_input_str):
    # output_str = BhrLgcGPTProcess.InstructionToHumanString(instruction)
    output_str = memeory_input_str
    insert_npcId = input_from_java[2]
    insert_time = input_from_java[1]
    
    insert_content = output_str
    while True:
        try:
            # Attempt to get the importance value
            insert_importance = int(BhrLgcGPTProcess.get_importance(output_str))
            break  # Exit the loop if successful
        except (ValueError, TypeError):
            # Handle cases where the result is not convertible to an integer
            print("Importance is not an integer. Retrying...")
    insert_embedding = BhrLgcGPTProcess.get_embedding(output_str)
    insert_isInstruction = 1

    BhrDBMemStre.insert_into_table(DBCon.establish_sql_connection(), insert_npcId, insert_time, insert_isInstruction, insert_content, insert_importance, insert_embedding)
    return 0

def InputToMemStreDB(input_from_java, memeory_input_str):
    # output_str = BhrLgcGPTProcess.InstructionToHumanString(instruction)
    output_str = memeory_input_str
    insert_npcId = input_from_java[2]
    insert_time = input_from_java[1]
    
    insert_content = output_str
    while True:
        try:
            # Attempt to get the importance value
            insert_importance = int(BhrLgcGPTProcess.get_importance(output_str))
            break  # Exit the loop if successful
        except (ValueError, TypeError):
            # Handle cases where the result is not convertible to an integer
            print("Importance is not an integer. Retrying...")
    insert_embedding = BhrLgcGPTProcess.get_embedding(output_str)
    insert_isInstruction = 0

    BhrDBMemStre.insert_into_table(DBCon.establish_sql_connection(), insert_npcId, insert_time, insert_isInstruction, insert_content, insert_importance, insert_embedding)
    return 0



# 
def InstImportancetoReflectionTracer(input_from_java, words_to_say):
    ReflectionTracer_db_conection = DBCon.establish_sql_connection()
    if not BhrDBReflectionTracer.table_exists(ReflectionTracer_db_conection):
        BhrDBReflectionTracer.create_table(ReflectionTracer_db_conection)

    input_from_java_string = input_from_java[3]
    output_str = words_to_say
    insert_npcId = input_from_java[2]
    insert_time = input_from_java[1]

    while True:
        try:
            # Attempt to get the importance and convert it to an integer
            insert_importance = int(BhrLgcGPTProcess.get_importance(output_str))
            # Break the loop if no exception occurs
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")
        
    output = BhrDBReflectionTracer.retrieve_entry(ReflectionTracer_db_conection, insert_npcId)

    if output is None:
        BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, insert_importance, insert_time, insert_time)
        return 0
    total_importance, start_time, end_time = output[0], output[1], output[2]
    BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, total_importance + insert_importance, start_time, insert_time)

    return 0





# # Need to See other people's actions as well.
# def inputImportancetoReflectionTracer(java_input):
#     row_dict_string = java_input[2]
#     ReflectionTracer_db_conection = DBCon.establish_sql_connection()
#     if not BhrDBReflectionTracer.table_exists(ReflectionTracer_db_conection):
#         BhrDBReflectionTracer.create_table(ReflectionTracer_db_conection)
#     row_dict = json.loads(row_dict_string)
#     if row_dict['npc']['talk']['isTalking'] == 'true':
#         MemString = BhrLgcGPTProcess.parse_npc_info(row_dict['npc']['talk'])
#         insert_npcId = row_dict['npc']['npcId']
#         insert_time = row_dict['time']
#         insert_importance = int(BhrLgcGPTProcess.get_importance(MemString))
#         output = BhrDBReflectionTracer.retrieve_entry(ReflectionTracer_db_conection, insert_npcId)
#         if output is None:
#             BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, insert_importance, insert_time, insert_time)
#             return 0
#         total_importance, start_time, end_time = output[0], output[1], output[2]
#         BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, total_importance + insert_importance, start_time, insert_time)

#     return 0