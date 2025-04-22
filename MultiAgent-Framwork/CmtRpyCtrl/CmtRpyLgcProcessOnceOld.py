import sys
import os

import pandas as pd
import numpy as np
import json
import re
import pickle
import hashlib
import configparser
import yaml
import traceback

# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)


from DBConnect import DBCon 
from DBConnect import CmtRpyDBJavaBuffer
from DBConnect import CmtRpyDBInstruction
from DBConnect import BhrDBSchedule

from BhrCtrl import BhrLgcGPTProcess
  


from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection


import CmtRpyLgcGPTProcess
# import CmtRpyManualProcess
# import CmtRpyInstToMemStre
# import CmtRpyInputToMemStre


config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

yaml_path = os.path.join(base_dir, 'char_config.yaml')

# Load the YAML file
with open(yaml_path, 'r', encoding='utf-8' ) as file:
    char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")

def choiceOneToReply():
    db_conn = DBCon.establish_sql_connection()
    db_conn = DBCon.check_and_reconnect(db_conn)

    input_from_java = CmtRpyDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)

    print(input_from_java)

    if input_from_java is None:
        print('Nothing to process so far')
        return 0
    else:
        print('Processing the following input:')
        print(input_from_java)
    
   
    requestId = input_from_java[0]

    # Now all print statements go into f
    print('Processing the following input:')
    print(input_from_java)
    
    curTime = input_from_java[1]
    npcId = input_from_java[2]
    msgId = input_from_java[3]
    senderId = input_from_java[4]
    content = input_from_java[5]

    print("Processing Request Id: ", requestId)

    # Get all comments for that npc
    all_comments = CmtRpyDBJavaBuffer.get_unprocessed_entries_of_npc(db_conn, npcId)
    print("All comments to choose from:")
    print(all_comments)
    # Prepare data for DataFrame
    data = []
    requestIdtoMark = []
    for comment in all_comments:
        requestId_fromdb, time_fromdb, npcId_fromdb, msgId_fromdb, senderId_fromdb, content_fromdb, isProcessed_fromdb, sname_fromdb = comment
        requestIdtoMark.append(requestId_fromdb)
        embedding = CmtRpyLgcGPTProcess.get_embedding(content_fromdb)
        # Deserialize the embedding back to a list
        data.append([requestId_fromdb, time_fromdb, npcId_fromdb, msgId_fromdb, senderId_fromdb, content_fromdb, embedding, sname_fromdb])

    # Define DataFrame columns
    columns = ['requestId', 'time', 'npcId', 'msgId', 'senderId', 'content', 'embedding', 'sname']

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)

    # Select one randomly
    comment_row_reply = df.sample(n=1)
    commet_to_reply = comment_row_reply['content']

    info_for_reply = ''
    # Get memeory stream 
    BufferRowEmbedding = BhrLgcGPTProcess.get_embedding(commet_to_reply)
    rows_df = BhrDBMemStre.retrieve_most_recent_entries(db_conn, npcId, time_fromdb)
    if rows_df is not None:
        rows_df['Time'] = pd.to_datetime(rows_df['Time'])
        rows_df['TimeDifference'] = (rows_df['Time'] - pd.to_datetime(time_fromdb)).dt.total_seconds()
        decay_rate = 0.001 
        rows_df['recency'] = np.exp(decay_rate * rows_df['TimeDifference'])

        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            return dot_product / (norm_vec1 * norm_vec2)

        rows_df['cosine_similarity'] = rows_df['Embedding'].apply(lambda x: cosine_similarity(BufferRowEmbedding, np.array(x)))

        a_recency = 0.2  # Adjust the weight for recency as needed
        a_importance = 0.2  # Adjust the weight for importance as needed
        a_similarity = 0.6  # Adjust the weight for similarity as needed

        rows_df['retrieval_score'] = (
            a_recency * rows_df['recency'] +
            a_importance * rows_df['Importance'] + 
            a_similarity * rows_df['cosine_similarity']
        )

        rows_df_ranked = rows_df.sort_values(by=['retrieval_score', 'Time'], ascending=[False, False]).head(20)
        rows_df_ranked = rows_df_ranked.sort_values(by='Time', ascending=False)
        paragraph = " ".join(rows_df_ranked['Content'].astype(str).tolist())
        memories_str = paragraph
    else:
        memories_str = 'No memory yet'
    info_for_reply += f'This is your prior memeories: {memories_str}\n\n'

    # Get reflect 
    prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, time_fromdb)
    if prior_reflection is not None:
        prior_reflection_str = str(prior_reflection[2])
    else:
        prior_reflection_str = 'No prior reflection yet!'
    info_for_reply += f'This is prior reflection: {prior_reflection_str}\n\n'

    # Get daily schedule 
    cur_schedule = BhrDBSchedule.retrieve_latest_schedule(db_conn, npcId)
    if cur_schedule is not None:
        cur_schedule_str = str(cur_schedule['schedule'])
    else:
        cur_schedule_str = 'No schedule yet!'
    info_for_reply += f'This is schedule of the day: {cur_schedule_str}\n\n'
    
    
    


    #Creating Reply
    reply_tosent = CmtRpyLgcGPTProcess.replyToComment(info_for_reply,  commet_to_reply, npcId)

    # Sent Reply
    requestId_tosent = str(comment_row_reply['requestId'].iloc[0])
    npcId_tosent = str(comment_row_reply['npcId'].iloc[0])
    msgId_tosent = str(comment_row_reply['msgId'].iloc[0])
    senderId_tosent = str(comment_row_reply['senderId'].iloc[0])
    time_tosent = comment_row_reply['time'].iloc[0]  # Get the first value if `time` is a Series
    sname_tosent = str(comment_row_reply['sname'].iloc[0])


    instruction_to_give = json.dumps({
        "actionId": 117,
        "npcId": str(npcId),
        "data": {
            "content": str(reply_tosent),
            "chatData": {
                "msgId": str(msgId_tosent),
                "sname": str(sname_tosent),  # Assuming `sname` can use `senderId` as a string
                "sender": str(senderId_tosent),
                "type": 0,  # Assuming a static value for type; change if needed
                "content": str(reply_tosent),
                "time": str(int(time_tosent.timestamp() * 1000)),  # Convert datetime to milliseconds
                "barrage": 0  # Assuming a static value for barrage; change if needed
            }
        }
    }, ensure_ascii=False)

    print('Instruction for replying user:')
    print(instruction_to_give)
    CmtRpyDBInstruction.insert_into_instruction_table(db_conn, requestId_tosent, time_tosent, npcId_tosent, msgId_tosent, instruction_to_give, isProcessed=False)
    

    for rid in requestIdtoMark:
        CmtRpyDBJavaBuffer.mark_entry_as_processed(db_conn, rid )
    # Example instruction.
    # {
    # "actionId": 117,
    # "npcId": 10002,
    # "data": {
    #     "playerId": "123132131",
    #     "content": "123132131",
    #     "msgId": "123132131",
    # }
    # }
    
    #Mark as Processed.


    return 0 
