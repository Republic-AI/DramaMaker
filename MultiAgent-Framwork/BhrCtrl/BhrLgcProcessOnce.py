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

# Add the base directory (one level up from the current directory)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

from DBConnect import DBCon
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule

import BhrLgcGPTProcess
import BhrLgcManualProcess
import BhrLgcToMemStre

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


def processOneInputGiveOneInstruction():
    """
    Process one input from the Java buffer and generate one instruction for the NPC.
    """
    # log_file = os.path.join(os.path.dirname(__file__), 'BhrCtrl', 'printout', 'output.txt')
    # with open(log_file, 'w') as f:
    try:
        db_conn = DBCon.establish_sql_connection()

        db_conn = DBCon.check_and_reconnect(db_conn)
        input_from_java = BhrDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)

        if input_from_java is None:
            print('Nothing to process so far')
            return 0
        
        request_id = input_from_java[0]
        
        

        # Now all print statements go into f
        print('Processing the following input:')
        print(input_from_java)

        curTime = input_from_java[1]
        npcId = input_from_java[2]
        java_json = input_from_java[3]

        print("Processing Request Id: ", request_id)

        # Parse talking and idling info
        talkingInfo, is_talking = BhrLgcManualProcess.parse_talking_from_java(java_json)
        is_idling = BhrLgcManualProcess.parse_isIdling(java_json)

        # Parse NPC info for next action
        inputInHumanString = BhrLgcManualProcess.parse_npc_info_for_nextaction(java_json)

        # Get relevant memories
        BufferRowEmbedding = BhrLgcGPTProcess.get_embedding(inputInHumanString)
        db_conn = DBCon.check_and_reconnect(db_conn)
        rows_df = BhrDBMemStre.retrieve_most_recent_entries(db_conn, npcId, curTime)

        if rows_df is not None:
            rows_df['Time'] = pd.to_datetime(rows_df['Time'])
            rows_df['TimeDifference'] = (rows_df['Time'] - pd.to_datetime(curTime)).dt.total_seconds()
            decay_rate = 0.001
            rows_df['recency'] = np.exp(decay_rate * rows_df['TimeDifference'])

            def cosine_similarity(vec1, vec2):
                dot_product = np.dot(vec1, vec2)
                norm_vec1 = np.linalg.norm(vec1)
                norm_vec2 = np.linalg.norm(vec2)
                return dot_product / (norm_vec1 * norm_vec2)

            rows_df['cosine_similarity'] = rows_df['Embedding'].apply(
                lambda x: cosine_similarity(BufferRowEmbedding, np.array(x))
            )

            # Adjusting weights for retrieval score
            a_recency = 0.2
            a_importance = 0.2
            a_similarity = 0.6

            rows_df['retrieval_score'] = (
                a_recency * rows_df['recency'] +
                a_importance * rows_df['Importance'] +
                a_similarity * rows_df['cosine_similarity']
            )

            rows_df_ranked = rows_df.sort_values(
                by=['retrieval_score', 'Time'], ascending=[False, False]
            ).head(30)
            rows_df_ranked = rows_df_ranked.sort_values(by='Time', ascending=False)
            paragraph = "\n".join(rows_df_ranked['Content'].astype(str).tolist())
            memories_str = paragraph
        else:
            memories_str = 'No memory yet'

        if memories_str == '':
            memories_str = 'No memory yet'

        print('Relevent Memeories:')
        print(memories_str)
        print()

        # Retrieve latest reflection
        db_conn = DBCon.check_and_reconnect(db_conn)
        prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, curTime)
        if prior_reflection is not None:
            prior_reflection_str = str(prior_reflection[2])
        else:
            prior_reflection_str = 'No prior reflection yet!'

        print('Prior Reflection:')
        print(prior_reflection_str)
        print()

        # Retrieve latest Schedule
        db_conn = DBCon.check_and_reconnect(db_conn)
        cur_schedule = BhrDBSchedule.retrieve_latest_schedule(db_conn, npcId)
        if cur_schedule is not None:
            cur_schedule_str = str(cur_schedule['schedule'])
        else:
            # If no schedule is found in DB, fallback to char_config.yaml
            npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
            if not npc:
                raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")
            cur_schedule_str = npc['schedule']

        instruction_in_human = ''

        # Check states: finding people to talk, idling, talking, buying
        is_findingToTalk, FindTalktargetNPCId = BhrLgcManualProcess.parse_isFindingPeopletoTalk(java_json)
        is_idling = BhrLgcManualProcess.parse_isIdling(java_json)
        is_talking = BhrLgcManualProcess.parse_isTalking(java_json)
        is_buying, shopownerNPCId = BhrLgcManualProcess.parse_isBuying(java_json)
        is_talk_target = BhrLgcManualProcess.parse_is_talk_target(java_json)

        is_talk_instruction = False
        talkInst_target_npcid = None

        npcId_to_Name = {
            10006: 'Satoshi',
            10007: 'Popcat',
            10008: 'Pepe',
            10009: 'Elon Musk',
            10010: 'Pippin',
            10011: 'Eliza',
            10012: 'Trump',
            10013: 'Morpheus',
            10014: 'AVA',
        }

        # Determine next action based on current states
        if is_findingToTalk and is_idling and (not is_talking): 
            print('Last action is finding people to talk, next action should be talking')
            target_sleeping, sleep_target_name = BhrLgcManualProcess.parse_target_sleeping(java_json)
            target_talking, talk_target_name = BhrLgcManualProcess.parse_target_talking(java_json)

            if target_sleeping or target_talking:
                # Target is not available for conversation
                print('Target is sleeping or talking, choose another action')
                instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, "Your next action can't be go find him to talk again, the target is not available"
                )
                if BhrLgcGPTProcess.needDeepTalk(
                    memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                ):
                    theme_for_generation = BhrLgcGPTProcess.generateTheme(
                        memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                    )
                    words_to_say = BhrLgcGPTProcess.generate_new_Announcement(
                        memories_str, prior_reflection_str, theme_for_generation, npcId
                    )
                else:
                    words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(
                        memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId
                    )
                target_name = sleep_target_name if sleep_target_name else (talk_target_name if talk_target_name else 'Unknown')
                instruction_in_human += f" I went to the {target_name} but he is not available, going to do something else now."
                is_talk_instruction = False
            else:
                print('Start Talking to the person')
                FindTalktargetNPCName= npcId_to_Name[FindTalktargetNPCId]
                talkInst_target_npcid = FindTalktargetNPCId
                instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, FindTalktargetNPCName
                )
                shouldConversationEnd = BhrLgcGPTProcess.shoudConversationEnd(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, FindTalktargetNPCName, instruction_in_human
                )
                instruction_in_human +=  ". " + shouldConversationEnd
                words_to_say = ''
                is_talk_instruction = True

        elif is_buying and is_idling and (not is_talking): 
            print('I am buying something, next action should be talking for buying stuff')
            shop_target_present, shopowner_target_name = BhrLgcManualProcess.parse_target_oid_owner_at_shop(java_json)

            if not shop_target_present: # Shop owner will have status sale, if he is not talking, so this also indicate that shop owner is not talking
                # Shop owner not present
                print('Shop owner not present, choose another action')
                instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, "Your next action can't be buying, the shop owner is not present"
                )
                if BhrLgcGPTProcess.needDeepTalk(
                    memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                ):
                    theme_for_generation = BhrLgcGPTProcess.generateTheme(
                        memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                    )
                    words_to_say = BhrLgcGPTProcess.generate_new_Announcement(
                        memories_str, prior_reflection_str, theme_for_generation, npcId
                    )
                else:
                    words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(
                        memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId
                    )
                instruction_in_human += f" I went to {shopowner_target_name}'s store to buy but he is not there, purchase failed, doing something else now."
                is_talk_instruction = False
            else:
                print('Start Talking to the shop owner')
                shopownerNPCname = npcId_to_Name[shopownerNPCId]
                talkInst_target_npcid = shopownerNPCId
                instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, shopownerNPCname
                )
                shouldConversationEnd = BhrLgcGPTProcess.shoudConversationEnd(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, shopownerNPCname, instruction_in_human
                )
                instruction_in_human +=  ". " + shouldConversationEnd
                words_to_say = ''
                is_talk_instruction = True

        elif is_talking and is_talk_target:
            # NPC currently talking
            talk_target_name, talk_target_npcid =  BhrLgcManualProcess.parse_current_converstation(java_json)
            talkInst_target_npcid = talk_target_npcid
            instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, talk_target_name
            )
            shouldConversationEnd = BhrLgcGPTProcess.shoudConversationEnd(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, talk_target_name, instruction_in_human
                )
            instruction_in_human +=  ". " + shouldConversationEnd
            words_to_say = ''
            is_talk_instruction = True

        elif is_idling and (not is_talking): 
            # NPC is idling, decide next action
            print('Is idling, decide next action')
            instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
            )
            if BhrLgcGPTProcess.needDeepTalk(
                memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
            ):
                theme_for_generation = BhrLgcGPTProcess.generateTheme(
                    memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                )
                words_to_say = BhrLgcGPTProcess.generate_new_Announcement(
                    memories_str, prior_reflection_str, theme_for_generation, npcId
                )
            else:
                words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(
                    memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId
                )
            is_talk_instruction = False

        # Generate final instruction JSON
        instruction_to_give = None
        if instruction_in_human != '':
            retry = 0
            while retry < 3:
                try:
                    if is_talk_instruction:
                        instruction_to_give = BhrLgcGPTProcess.humanInstToJava_talk(
                            instruction_in_human, words_to_say, npcId, talkInst_target_npcid
                        ).strip("```json").strip("```")
                    else:
                        instruction_to_give = BhrLgcGPTProcess.humanInstToJava_action(
                            instruction_in_human, words_to_say, npcId
                        ).strip("```json").strip("```")
                    instruction_json = json.loads(instruction_to_give)
                    instruction_json['requestId'] = request_id
                    # Re-serialize the JSON after adding requestId
                    instruction_to_give = json.dumps(instruction_json)
                    break
                except Exception as e:
                    print(f"Error occurred: {e}. Retrying...")
                    retry += 1
                    if retry == 3:
                        return 0

        if instruction_to_give is not None:
            print('Instruction to give:')
            print(instruction_json)
            print()

            # Add to instruction db
            db_conn = DBCon.check_and_reconnect(db_conn)
            BhrDBInstruction.insert_into_instruction_table(db_conn, curTime, npcId, instruction_to_give, request_id)

        # Mark the buffer as processed
        db_conn = DBCon.check_and_reconnect(db_conn)
        BhrDBJavaBuffer.mark_entry_as_processed(db_conn, request_id)

        # If we produced an instruction
        if instruction_to_give is not None:
            # Check if a new schedule is needed
            if BhrLgcGPTProcess.need_new_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId):
                cur_schedule_str = BhrLgcGPTProcess.generate_schedule(
                    cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId
                )
                db_conn = DBCon.check_and_reconnect(db_conn)
                BhrDBSchedule.insert_into_table(db_conn, npcId, curTime, cur_schedule_str)

            print('Current Schedule:')
            print(cur_schedule)
            print()

            data = json.loads(java_json)
            npcs = data.get('npcs', [])
            if len(npcs) > 0:
                npc = npcs[0]
                talk_info = npc.get('talk', {})
                is_talking = talk_info.get('isTalking', False)
                if is_talking:
                    input_for_mem = BhrLgcManualProcess.parse_npc_info_formemory(java_json)
                    BhrLgcToMemStre.InputToMemStreDB(input_from_java, input_for_mem)
                    BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, input_for_mem)

            # Insert instruction to Memory Stream
            BhrLgcToMemStre.InstToMemStreDB(input_from_java, "At "+str(curTime) + " ," + instruction_in_human)
            BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, instruction_in_human)

            # Check reflection importance
            db_conn = DBCon.check_and_reconnect(db_conn)
            output = BhrDBReflectionTracer.retrieve_entry(db_conn, npcId)
            if output:
                output_importance, output_starttime, output_endtime = output[0], output[1], output[2]
                if output_importance > 100:
                    # Time for reflection
                    db_conn = DBCon.check_and_reconnect(db_conn)
                    memories = BhrDBMemStre.retrieve_entries_between_time(db_conn, npcId, output_starttime, output_endtime)
                    db_conn = DBCon.check_and_reconnect(db_conn)
                    prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, output_endtime)
                    if prior_reflection is not None:
                        prior_reflection_str = prior_reflection[2]
                    else:
                        prior_reflection_str = 'No prior reflections'
                    memories_str = str(memories['Content']) if memories is not None else 'No prior memories'

                    new_reflection = BhrLgcGPTProcess.generate_reflection_new(prior_reflection_str, memories_str, inputInHumanString, npcId)
                    print("New Reflection: ", new_reflection)
                    db_conn = DBCon.check_and_reconnect(db_conn)
                    BhrDBReflection.insert_into_table(db_conn, npcId, curTime, new_reflection)
                    # Reset the importance tracer
                    db_conn = DBCon.check_and_reconnect(db_conn)
                    BhrDBReflectionTracer.insert_into_table(db_conn, npcId, 0, curTime, curTime)

        db_conn = DBCon.check_and_reconnect(db_conn)
        BhrDBJavaBuffer.mark_entry_as_fullyprocessed(db_conn, request_id)

        db_conn = DBCon.check_and_reconnect(db_conn)
        DBCon.close_sql_connection(db_conn)
        return 1

    except Exception as e:
        # If the function throws an error, print the traceback as well
        traceback.print_exc()
        return 0
    
    finally:
        # Ensure the connection is closed regardless of success or exception
        if db_conn and DBCon.is_connected(db_conn):
            print("Closing the connection in the finally block due to exception or completion.")
            DBCon.close_sql_connection(db_conn)