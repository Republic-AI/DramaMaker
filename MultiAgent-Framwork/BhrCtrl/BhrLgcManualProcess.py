import json
from datetime import datetime

############################################
# General Parsing Functions
############################################
import sys
import os
import configparser
import yaml
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

def parse_npc_info_for_nextaction(json_input):
    """
    Parses NPC info for the next action from the given JSON input.
    Extracts the current world time and any ongoing conversation details.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_npc_info_for_nextaction | Description: Parses NPC info for next action and world time | Result:", result, "\n")
        return result
    
    # Extract world time
    world_time_ms = data.get('world', {}).get('time', 0)
    try:
        world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    except (OSError, ValueError):
        world_time = "Invalid world time"
    talk_info, is_talking = parse_talking_from_java(json_input)
    output_text = f'''
    Now is {world_time}.
    {talk_info}
    '''
    print("Method: parse_npc_info_for_nextaction | Description: Parses NPC info for next action and world time | Result:", output_text, "\n")
    return output_text


def parse_npc_info_formemory(json_input):
    """
    Parses NPC info suitable for memory logs.
    Extracts world time and any ongoing conversation details.
    Returns a string describing the situation.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_npc_info_formemory | Description: Parses NPC info for memory | Result:", result, "\n")
        return result
    
    world_time_ms = data.get('world', {}).get('time', 0)
    try:
        world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    except (OSError, ValueError):
        world_time = "Invalid world time"

    npcs = data.get('npcs', [])
    if not npcs:
        result = "No NPCs found in the data."
        print("Method: parse_npc_info_formemory | Description: Parses NPC info for memory | Result:", result, "\n")
        return result

    npc = npcs[0]
    # npc_names = {
    #     10006: "Satoshi",
    #     10007: "Popcat",
    #     10008: "Pepe",
    #     10009: "Musk",
    #     10010: "Pippin",
    #     10011: "Eliza",
    #     10012: "Trump",
    #     10013: "Morpheus",
    #     10014: "AVA",
    # }
    npc_names = {npc['npcId']: npc['name'] for npc in char_config.get('npcCharacters', [])}

    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    talk_contents = talk_info.get('contents', [])

    if is_talking and talk_contents:
        talk_summary = "\n".join([
            f"{npc_names.get(content.get('sender'), 'Unknown')} said to {npc_names.get(content.get('target'), 'Unknown')}: {content.get('content', 'None')} \n"
            for content in talk_contents
        ])
    else:
        talk_summary = "No ongoing conversation."

    output_text = f"At {world_time}, {talk_summary}"
    print("Method: parse_npc_info_formemory | Description: Parses NPC info for memory | Result:", output_text, "\n")
    return output_text


def parse_talking_from_java(json_input):
    """
    Parses talking information from the input.
    Returns a summary of the conversation and whether the NPC is talking.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_talking_from_java | Description: Parses talking info from JSON | Result:", (result, False), "\n")
        return result, False
    
    npcs = data.get('npcs', [])
    if not npcs:
        result = "No NPCs found in the data."
        print("Method: parse_talking_from_java | Description: Parses talking info from JSON | Result:", (result, False), "\n")
        return result, False
    
    npc = npcs[0]
    # npc_names = {
    #     10006: "Satoshi",
    #     10007: "Popcat",
    #     10008: "Pepe",
    #     10009: "Musk",
    #     10010: "Pippin",
    #     10011: "Eliza",
    #     10012: "Trump",
    #     10013: "Morpheus",
    #     10014: "AVA",
    # }
    npc_names = {npc['npcId']: npc['name'] for npc in char_config.get('npcCharacters', [])}

    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    talk_contents = talk_info.get('contents', [])
    
    if is_talking and talk_contents:
        talk_summary = "\n".join([
            f"{npc_names.get(content.get('sender'), 'Unknown')} said to {npc_names.get(content.get('target'), 'Unknown')}: {content.get('content', 'None')} \n"
            for content in talk_contents
        ])
    else:
        talk_summary = "No ongoing conversation."
    result = (talk_summary, is_talking)
    print("Method: parse_talking_from_java | Description: Parses talking info from JSON | Result:", result, "\n")
    return talk_summary, is_talking


############################################
# Status Checking Functions
############################################

def parse_isTalking(json_input):
    """
    Checks if the NPC is currently talking.
    Returns True if talking, False otherwise.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_isTalking | Description: Checks if NPC is currently talking | Result:", result, "\n")
        return False
    
    npcs = data.get('npcs', [])
    if not npcs:
        result = False
        print("Method: parse_isTalking | Description: Checks if NPC is currently talking | Result:", result, "\n")
        return result

    npc = npcs[0]
    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    return is_talking

def parse_getInnerVoice(json_input):
    """
    Checks if the NPC is currently talking.
    Returns True if talking, False otherwise.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_getInnerVoice | Description: Checks if NPC needs to follow inner voice| Result:", result, "\n")
        return False
    
    inner_voice = data.get("innverVoice", "")
    if not inner_voice:
        result = ""
        print("Method: parse_getInnerVoice | Description: Checks if NPC needs to follow inner voice| Result:", result, "\n")
        return result
 
    return inner_voice
        
    

def parse_is_talk_target(json_input):
    """
    Checks if the needs to response now.
    Returns True if need to response, False otherwise.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_isTalking | Description: Checks if NPC is currently talking | Result:", result, "\n")
        return False
    
    npcs = data.get('npcs', [])
    if not npcs:
        result = False
        print("Method: parse_isTalking | Description: Checks if NPC is currently talking | Result:", result, "\n")
        return result

    npc = npcs[0]
    npcId = npc.get('npcId', 'Unknown')
    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    if is_talking:
        talk_contents = talk_info.get('contents', [])
        content = talk_contents[0] if talk_contents else {}
        target_id = content.get('target', None)
        if target_id != npcId:
            is_talking = False
    print("Method: parse_isTalking | Description: Checks if NPC is currently talking | Result:", is_talking, "\n")
    return is_talking



def parse_isBuying(json_input):
    """
    Checks if the NPC is currently performing a 'buy' action (actionId == 103).
    Returns True if buying, False otherwise.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_isBuying | Description: Checks if NPC is currently buying | Result:", result, "\n")
        return result, None
    
    npcs = data.get('npcs', [])
    if not npcs:
        result = False
        print("Method: parse_isBuying | Description: Checks if NPC is currently buying | Result:", result, "\n")
        return result, None
    
    npc = npcs[0]
    cur_action = npc.get('action', {})
    action_id = cur_action.get('actionId', '0')
    result = (int(action_id) == 103)
    targetShopOid = cur_action.get('param', {}).get('oid', None)
    counter_to_owner = {
        "popcatBuy": 10007,
        "pepeBuy": 10008,
        "pippinBuy": 10010,
    }
    
    targetNPCId = counter_to_owner.get(targetShopOid, None)
    print("Method: parse_isBuying | Description: Checks if NPC is currently buying (actionId=103) | Result:", result, "\n")
    return result, targetNPCId


def parse_isFindingPeopletoTalk(json_input):
    """
    Checks if the NPC is currently performing actionId = 127 (finding people to talk).
    Returns True if yes, False otherwise.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_isFindingPeopletoTalk | Description: Checks if NPC is looking for people to talk (actionId=127) | Result:", result, "\n")
        return result, None
    
    npcs = data.get('npcs', [])
    if not npcs:
        result = False
        print("Method: parse_isFindingPeopletoTalk | Description: Checks if NPC is looking for people to talk | Result:", result, "\n")
        return result, None
    
    npc = npcs[0]
    cur_action = npc.get('action', {})
    action_id = cur_action.get('actionId', '0')
    targetNPCId = cur_action.get('param', {}).get('npcId', None)
    if targetNPCId:
        result = (int(action_id) == 127)
    else:
        result = False
    print("Method: parse_isFindingPeopletoTalk | Description: Checks if NPC is looking for people to talk | Result:", result, "\n")

    # Only able to start converstation when status is free
    idling = npc.get('status', '')
    result = (result  and idling == "free")

    return result, targetNPCId


def parse_isIdling(json_input):
    """
    Checks if the NPC is currently in 'free' status (idling).
    Returns True if free, False otherwise.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        result = f"Error parsing JSON: {e}"
        print("Method: parse_isIdling | Description: Checks if NPC is idling | Result:", result, "\n")
        return result
    
    npcs = data.get('npcs', [])
    if not npcs:
        result = False
        print("Method: parse_isIdling | Description: Checks if NPC is idling | Result:", result, "\n")
        return result
    
    npc = npcs[0]
    idling = npc.get('status', '')
    result = (idling == "free")
    print("Method: parse_isIdling | Description: Checks if NPC is idling | Result:", result, "\n")
    return result


############################################
# Target NPC State Checking Functions
############################################

def parse_target_sleeping(json_input):
    """
    Checks if the target NPC in the NPC's current action is sleeping.
    Returns a tuple (bool, target_name). bool = True if sleeping, False otherwise.
    target_name = Name of the target NPC if found, else None.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print("Method: parse_target_sleeping | Description: Checks if target NPC is sleeping | Result:", (False, None), "\n")
        return False, None

    npcs = data.get('npcs', [])
    if not npcs:
        print("Method: parse_target_sleeping | Description: Checks if target NPC is sleeping | Result:", (False, None), "\n")
        return False, None

    npc = npcs[0]
    action = npc.get('action', {})
    params = action.get('param', None)
    if not params:
        print("Method: parse_target_sleeping | Description: Checks if target NPC is sleeping | Result:", (False, None), "\n")
        return False, None

    target_npc_id = params.get('npcId', None)
    if not target_npc_id:
        print("Method: parse_target_sleeping | Description: Checks if target NPC is sleeping | Result:", (False, None), "\n")
        return False, None

    # npc_names = {
    #     10006: "Satoshi",
    #     10007: "Popcat",
    #     10008: "Pepe",
    #     10009: "Musk",
    #     10010: "Pippin",
    #     10011: "Eliza",
    #     10012: "Trump",
    #     10013: "Morpheus",
    #     10014: "AVA",
    # }
    npc_names = {npc['npcId']: npc['name'] for npc in char_config.get('npcCharacters', [])}

    surrounding_npcs = npc.get('surroundings', {}).get('people', [])
    for surrounding_npc in surrounding_npcs:
        if surrounding_npc.get('npcId') == int(target_npc_id):
            is_sleeping = (surrounding_npc.get('status') == 'sleep')
            result = (is_sleeping, npc_names.get(target_npc_id, "Unknown"))
            print("Method: parse_target_sleeping | Description: Checks if target NPC is sleeping | Result:", result, "\n")
            return result

    print("Method: parse_target_sleeping | Description: Checks if target NPC is sleeping | Result:", (False, None), "\n")
    return False, None


def parse_target_talking(json_input):
    """
    Checks if the target NPC in the current action is talking.
    Returns a tuple (bool, target_name). bool = True if talking, False otherwise.
    target_name = Name of the target NPC if found, else None.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print("Method: parse_target_talking | Description: Checks if target NPC is talking | Result:", (False, None), "\n")
        return False, None
    npcs = data.get('npcs', [])
    if not npcs:
        print("Method: parse_target_talking | Description: Checks if target NPC is talking | Result:", (False, None), "\n")
        return False, None

    npc = npcs[0]
    action = npc.get('action', {})
    params = action.get('param', None)
    if not params:
        print("Method: parse_target_talking | Description: Checks if target NPC is talking | Result:", (False, None), "\n")
        return False, None

    target_npc_id = params.get('npcId', None)
    if not target_npc_id:
        print("Method: parse_target_talking | Description: Checks if target NPC is talking | Result:", (False, None), "\n")
        return False, None

    # npc_names = {
    #     10006: "Satoshi",
    #     10007: "Popcat",
    #     10008: "Pepe",
    #     10009: "Musk",
    #     10010: "Pippin",
    #     10011: "Eliza",
    #     10012: "Trump",
    #     10013: "Morpheus",
    #     10014: "AVA",
    # }
    npc_names = {npc['npcId']: npc['name'] for npc in char_config.get('npcCharacters', [])}

    surrounding_npcs = npc.get('surroundings', {}).get('people', [])
    for surrounding_npc in surrounding_npcs:
        if surrounding_npc.get('npcId') == int(target_npc_id):
            is_talking = (surrounding_npc.get('status') == 'talk')
            result = (is_talking, npc_names.get(target_npc_id, "Unknown"))
            print("Method: parse_target_talking | Description: Checks if target NPC is talking | Result:", result, "\n")
            return result

    print("Method: parse_target_talking | Description: Checks if target NPC is talking | Result:", (False, None), "\n")
    return False, None

def parse_target_oid_owner_at_shop(json_input):
    """
    Checks if the owner NPC of a given OID (store) is present and in 'sale' status.
    Returns (bool, owner_name) indicating if the owner is at the shop and their name.
    """
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    npcs = data.get('npcs', [])
    if not npcs:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    npc = npcs[0]
    action = npc.get('action', {})
    params = action.get('param', None)
    if not params:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    target_oid = params.get('oid', None)
    if not target_oid:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    store_to_owner = {
        "popcatBuy": 10007,
        "pepeBuy": 10008,
        "pippinBuy": 10010,
    }

    target_npc_id = store_to_owner.get(target_oid, None)
    print('target_npc_id:', target_npc_id)
    if not target_npc_id:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    # npc_names = {
    #     10006: "Satoshi",
    #     10007: "Popcat",
    #     10008: "Pepe",
    #     10009: "Musk",
    #     10010: "Pippin",
    #     10011: "Eliza",
    #     10012: "Trump",
    #     10013: "Morpheus",
    #     10014: "AVA",
    # }
    npc_names = {npc['npcId']: npc['name'] for npc in char_config.get('npcCharacters', [])}

    surrounding_npcs = npc.get('surroundings', {}).get('people', [])
    for surrounding_npc in surrounding_npcs:
        if surrounding_npc.get('npcId') == target_npc_id:
            is_at_shop = (surrounding_npc.get('status') == 'sale')
            result = (is_at_shop, npc_names.get(target_npc_id, "Unknown"))
            print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", result, "\n")
            return result

    print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
    return False, None

def parse_current_converstation(json_input):
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    npcs = data.get('npcs', [])
    if not npcs:
        print("Method: parse_target_oid_owner_at_shop | Description: Checks if OID owner NPC is at shop | Result:", (False, None), "\n")
        return False, None

    npc = npcs[0]

    talk_info = npc.get('talk', {})
    contents = talk_info.get('contents', [])
    content = contents[0] if contents else {}
    senderId = content.get('sender', None)
    # npcId_to_Name = {
    #         10006: 'Satoshi',
    #         10007: 'Popcat',
    #         10008: 'Pepe',
    #         10009: 'Elon Musk',
    #         10010: 'Pippin',
    #         10011: "Eliza",
    #         10012: "Trump",
    #         10013: "Morpheus",
    #         10014: "AVA",
    #     }
    npcId_to_Name = {npc['npcId']: npc['name'] for npc in char_config.get('npcCharacters', [])}
    if senderId:
        senderName = npcId_to_Name.get(senderId, 'Unknown')
        return senderName, senderId
    else:
        return None, None
   
############################################
# Utility Function
############################################

def talkingInstruction(npcId, words):
    """
    Generate a JSON instruction for an NPC to talk.
    npcId: string representing NPC ID
    words: string representing what NPC says
    Returns a JSON string.
    """
    if not isinstance(npcId, str) or not isinstance(words, str):
        raise ValueError("Both npcId and words must be strings.")
    
    words = words.replace('"', '\\"')
    instruction = {
        "actionId": 110,
        "npcId": npcId,
        "data": {
            "content": words
        }
    }
    result = json.dumps(instruction, indent=4)
    print("Method: talkingInstruction | Description: Generates JSON instruction for NPC to talk | Result:", result, "\n")
    return result