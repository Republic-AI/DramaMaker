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
import ast

# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)


from DBConnect import DBCon 
from DBConnect import CmtRpyDBJavaBuffer
from DBConnect import CmtRpyDBInstruction
from DBConnect import CmtRpyDBMemStre


from BhrCtrl import BhrLgcGPTProcess
  
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule


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
    print("Config YAML content loaded successfully.")


event_path = os.path.join(base_dir, 'keyEvent.yaml')
# Load the YAML file
with open(event_path, 'r', encoding='utf-8' ) as file:
    event_config = yaml.safe_load(file)
    print("Event YAML content loaded successfully.")



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
    
    print("input_from_java: ", input_from_java)
    requestId = input_from_java[0]

    # Now all print statements go into f
    print('Processing the following input:')
    print(input_from_java)
    
    curTime = input_from_java[1]
    npcId = input_from_java[2]
    msgId = input_from_java[3]
    senderId = input_from_java[4]
    content = input_from_java[5]
    sender_name = input_from_java[7]

    print("Processing Request Id: ", requestId)

    # Get all comments for that npc
    all_comments = CmtRpyDBJavaBuffer.get_unprocessed_entrie_of_npc(db_conn, npcId)
    print("All comments to choose from:")
    print(all_comments)
    # Prepare data for DataFrame
    data = []
    requestIdtoMark = []
    for comment in all_comments:
        requestId_fromdb, time_fromdb, npcId_fromdb, msgId_fromdb, senderId_fromdb, content_fromdb, isProcessed_fromdb, sname_fromdb, isBeingProcessed_fromdb, privateMsg_fromdb = comment
        requestIdtoMark.append(requestId_fromdb)
        embedding = CmtRpyLgcGPTProcess.get_embedding(content_fromdb)
        # Deserialize the embedding back to a list
        data.append([requestId_fromdb, time_fromdb, npcId_fromdb, msgId_fromdb, senderId_fromdb, content_fromdb, embedding, sname_fromdb, isBeingProcessed_fromdb, privateMsg_fromdb])

    # Define DataFrame columns
    columns = ['requestId', 'time', 'npcId', 'msgId', 'senderId', 'content', 'embedding', 'sname', 'isBeingProcessed', 'privateMsg']

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)

    # Select one randomly
    comment_row_reply = df.sample(n=1)
    commet_to_reply = comment_row_reply['content']
    # Convert the pandas Series to a string
    
    npc_events_entry = next((item for item in event_config.get('npcEvents', []) if item.get('npcId') == npcId), None)
    print(npc_events_entry)
    if npc_events_entry:
        events_list = npc_events_entry.get('events', [])
        events_data = []
        for ev in events_list:
            ev_id = ev.get('id')
            ev_intro = ev.get('intro')
            ev_detail = str(ev.get('details'))
            ev_embedding = CmtRpyLgcGPTProcess.get_embedding(ev_intro)
            events_data.append([ev_id, ev_intro, ev_detail, ev_embedding])
        events_df = pd.DataFrame(events_data, columns=['eventId', 'intro', 'detail', 'embedding'])
    else:
        events_df = pd.DataFrame(columns=['eventId', 'intro', 'detail', 'embedding'])

    comment_str = str(commet_to_reply)
    comment_embedding = CmtRpyLgcGPTProcess.get_embedding(comment_str)

    def cosine_similarity(vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2)

    events_df['similary'] = events_df['embedding'].apply(lambda emb: cosine_similarity(emb, comment_embedding))

    threshold = 0.3
    selected_event = (
        events_df[events_df['similary'] > threshold]
        .sort_values(by='similary', ascending=False)
        .head(3)
    )
    paragraphs = []
    for _, row in selected_event.iterrows():
        # Parse the stringified list of details back into a Python list
        details_list = ast.literal_eval(row['detail'])
        # Join all detail items into a single string
        details_text = " ".join(details_list)
        # Form the paragraph: intro followed by details
        paragraph = f"{row['intro']} {details_text}"
        paragraphs.append(paragraph)


    relevent_event = "\n\n".join(
        f"relevent event {idx}: {para}"
        for idx, para in enumerate(paragraphs, start=1)
    )

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
    # reply_tosent = CmtRpyLgcGPTProcess.replyToComment(info_for_reply,  commet_to_reply, npcId)

    db_conn = DBCon.check_and_reconnect(db_conn)
    conv_rows_df = CmtRpyDBMemStre.retrieve_most_recent_entries(db_conn, npcId, time_fromdb, sender_name)
    if conv_rows_df is not None:
        conv_rows_df['Time'] = pd.to_datetime(conv_rows_df['Time'])
        conv_rows_df['TimeDifference'] = (conv_rows_df['Time'] - pd.to_datetime(time_fromdb)).dt.total_seconds()
        decay_rate = 0.001 
        conv_rows_df['recency'] = np.exp(decay_rate * conv_rows_df['TimeDifference'])

        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            return dot_product / (norm_vec1 * norm_vec2)

        conv_rows_df['cosine_similarity'] = conv_rows_df['Embedding'].apply(lambda x: cosine_similarity(BufferRowEmbedding, np.array(x)))

        a_recency = 0.2  # Adjust the weight for recency as needed
        a_importance = 0.2  # Adjust the weight for importance as needed
        a_similarity = 0.6  # Adjust the weight for similarity as needed

        conv_rows_df['retrieval_score'] = (
            a_recency * conv_rows_df['recency'] +
            a_importance * conv_rows_df['Importance'] + 
            a_similarity * conv_rows_df['cosine_similarity']
        )

        conv_rows_df_ranked = conv_rows_df.sort_values(by=['retrieval_score', 'Time'], ascending=[False, False]).head(20)
        conv_rows_df_ranked = conv_rows_df_ranked.sort_values(by='Time', ascending=False)
        paragraph = " ".join(conv_rows_df_ranked['Content'].astype(str).tolist())
        prior_conversation = paragraph
    else:
        prior_conversation = 'No conversation yet'

    reply_tosent = CmtRpyLgcGPTProcess.replyToUser(info_for_reply,  commet_to_reply, npcId, prior_conversation, relevent_event)
 
    # Sent Reply
    requestId_tosent = str(comment_row_reply['requestId'].iloc[0])
    npcId_tosent = str(comment_row_reply['npcId'].iloc[0])
    msgId_tosent = str(comment_row_reply['msgId'].iloc[0])
    senderId_tosent = str(comment_row_reply['senderId'].iloc[0])
    time_tosent = comment_row_reply['time'].iloc[0]  # Get the first value if `time` is a Series
    sname_tosent = str(comment_row_reply['sname'].iloc[0])
    privateMsg_tosent = comment_row_reply['privateMsg'].iloc[0]


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
                "barrage": 0,  # Assuming a static value for barrage; change if needed
                "privateMsg": str(bool(privateMsg_tosent))
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
    db_conn = DBCon.check_and_reconnect(db_conn)
    comment_in_db = sender_name + " said to you :" + commet_to_reply
    # Convert comment_in_db to string to ensure it's in the correct format
    comment_in_db = str(comment_in_db)
    CommentEmbedding = BhrLgcGPTProcess.get_embedding(comment_in_db)
    CmtRpyDBMemStre.insert_into_table(db_conn, npcId, curTime, 0, comment_in_db, 1, CommentEmbedding, sender_name)

    db_conn = DBCon.check_and_reconnect(db_conn)
    reply_in_db = "you said to " + sender_name + " :" + reply_tosent
    reply_in_db = str(reply_in_db)
    ReplyEmbedding = BhrLgcGPTProcess.get_embedding(reply_in_db)
    CmtRpyDBMemStre.insert_into_table(db_conn, npcId, curTime, 1, reply_in_db, 1, ReplyEmbedding, sender_name)


    return 0 
