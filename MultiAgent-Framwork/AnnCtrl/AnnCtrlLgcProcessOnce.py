

import sys
import os
import pandas as pd
import numpy as np
import json
import re
import pickle

# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

import DBConnect.DBCon as DBCon
import DBConnect.AnnDBJavaBuffer as AnnDBJavaBuffer
import DBConnect.AnnDBAnnBuffer as AnnDBAnnBuffer
import DBConnect.AnnDBInstruction as AnnDBInstruction

import AnnCtrlLgcGPTProcess
import AnnCtrlLgcManualProcess

def makeAnAnnouncement():
    db_conn = DBCon.establish_sql_connection()
    input_from_java = AnnDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)
    if input_from_java is None:
        print('Nothing to Announce so far')
        print()
        print()
        return 0

    # requestId, time, npcId, content, isProcessed
    requestId = input_from_java[0]
    time = input_from_java[1]
    npcId = input_from_java[2]
    content = input_from_java[3]

    # Get remaining announcement from the announcement_buffer
    annData = AnnDBAnnBuffer.get_earliest_order_announcement(db_conn, npcId)
    # If no remaining ones, generate new one
    if annData is None:
        # Generate a new theme
        newTheme = AnnCtrlLgcGPTProcess.generat_new_theme(npcId)
        # Write a new paragraph, Separate into pieces and put in announcement buffer
        newAnns = AnnCtrlLgcGPTProcess.generate_new_Announcement(newTheme, npcId)

        if not newAnns:
            print("Error: Failed to generate valid announcements")
            return

        counter = 0
        for newAnn in newAnns:
            AnnDBAnnBuffer.insert_into_announce_table(db_conn, npcId, newTheme, counter, newAnn, time)
            counter += 1

        # Again, get announcement from the buffer
        annData = AnnDBAnnBuffer.get_earliest_order_announcement(db_conn, npcId)

    # Send to the instruction buffer
    themeSent, orderId, AnnSent = annData[1], annData[2], annData[3]
    instruction_to_give = AnnCtrlLgcManualProcess.talkingInstruction(npcId, AnnSent)

    AnnDBInstruction.insert_into_instruction_table(db_conn, time, npcId, instruction_to_give)

    # Mark the AnnDBJavaBuffer as processed
    AnnDBJavaBuffer.mark_entry_as_processed(db_conn, requestId)
    # Mark the announcement_buffer as processed
    AnnDBAnnBuffer.mark_announcement_as_sent(db_conn, npcId, orderId)