import sys
import os

# Add the DBmanipulation folder to the Python path

import DBConnect.DBCon as DBCon
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflectionTracer

import json
import re
import pickle

import BhrCtrl.BhrLgcGPTProcess as BhrLgcGPTProcess


def inputToMemStre(java_input):
    # Establish a connection to the database
    row_dict_str = java_input[2]
    row_dict = json.loads(row_dict_str)
    memstre_db_connection = DBCon.establish_sql_connection()
    if row_dict['npc']['talk']['isTalking'] == True:
        print('conversation received')
        MemString = BhrLgcGPTProcess.javaConvInputtoHumanString(row_dict['npc']['talk'])
        insert_npcId = java_input[1]
        insert_time = java_input[0]
        insert_content = MemString
        insert_importance = BhrLgcGPTProcess.get_importance(MemString)
        insert_embedding = BhrLgcGPTProcess.get_embedding(MemString)
        insert_isInstruction = 0
        BhrDBMemStre.insert_into_table(memstre_db_connection, insert_npcId, insert_time, insert_isInstruction, insert_content, insert_importance, insert_embedding)

    return 0


# Need to See other people's actions as well.
def inputImportancetoReflectionTracer(java_input):
    row_dict_string = java_input[2]
    ReflectionTracer_db_conection = DBCon.establish_sql_connection()
    if not BhrDBReflectionTracer.table_exists(ReflectionTracer_db_conection):
        BhrDBReflectionTracer.create_table(ReflectionTracer_db_conection)
    row_dict = json.loads(row_dict_string)
    if row_dict['npc']['talk']['isTalking'] == 'true':
        MemString = BhrLgcGPTProcess.parse_npc_info(row_dict['npc']['talk'])
        insert_npcId = row_dict['npc']['npcId']
        insert_time = row_dict['time']
        insert_importance = int(BhrLgcGPTProcess.get_importance(MemString))
        output = BhrDBReflectionTracer.retrieve_entry(ReflectionTracer_db_conection, insert_npcId)
        if output is None:
            BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, insert_importance, insert_time, insert_time)
            return 0
        total_importance, start_time, end_time = output[0], output[1], output[2]
        BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, total_importance + insert_importance, start_time, insert_time)

    return 0