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

memstre_db_connection = DBCon.establish_sql_connection()

def InstToMemStreDB(input_from_java, memeory_input_str):
    # output_str = BhrLgcGPTProcess.InstructionToHumanString(instruction)
    output_str = memeory_input_str
    insert_npcId = input_from_java[1]
    insert_time = input_from_java[0]
    
    insert_content = output_str
    insert_importance = BhrLgcGPTProcess.get_importance(output_str)
    insert_embedding = BhrLgcGPTProcess.get_embedding(output_str)
    insert_isInstruction = 1

    BhrDBMemStre.insert_into_table(memstre_db_connection, insert_npcId, insert_time, insert_isInstruction, insert_content, insert_importance, insert_embedding)
    return 0

def InstToMemStreSatoshiDB(input_from_java, words):
    insert_npcId = input_from_java[2]
    insert_time = input_from_java[1]
    
    insert_content = words
    insert_importance = BhrLgcGPTProcess.get_importance(words)
    insert_embedding = BhrLgcGPTProcess.get_embedding(words)
    insert_isInstruction = 1

    BhrDBMemStre.insert_into_table(memstre_db_connection, insert_npcId, insert_time, insert_isInstruction, insert_content, insert_importance, insert_embedding)
    return 0

def InstImportancetoReflectionTracer(input_from_java, instruction, words_to_say):
    ReflectionTracer_db_conection = DBCon.establish_sql_connection()
    if not BhrDBReflectionTracer.table_exists(ReflectionTracer_db_conection):
        BhrDBReflectionTracer.create_table(ReflectionTracer_db_conection)

    input_from_java_string = input_from_java[3]
    output_str = 'Satoshi says' + words_to_say
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