import json
from datetime import datetime

def parse_npc_info(json_input):
    try:
        # Load the JSON data
        data = json.loads(json_input)

        # Extract world time and convert from milliseconds to a readable format
        world_time_ms = data['world']['time']
        world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')

        # Extract NPC information
        npc_info = data['npcs'][0]['info']
        first_name = npc_info['firstName']
        last_name = npc_info['lastName']
        learned = npc_info['learned']
        lifestyle = npc_info['lifestyle']
        living_area = npc_info['living_area']

        # Extract current action
        cur_action = data['npcs'][0]['curAction']
        action_name = cur_action['actionName']
        action_oid = cur_action['param']['oid']

        # Mapping of action identifiers to human-readable actions
        action_mapping = {
            'move': 'Moving',
            'zhongbencongType': 'Typing',
            'zhongbencongRead': 'Reading',
            'zhongbencongFix': 'Fixing',
            'zhongbencongThink': 'Thinking'
        }

        # Determine the readable action
        readable_action = action_mapping.get(action_oid, 'Unknown Action')

        # Compile the extracted information into a human-readable format
        # output_text = (
        #     f"Time: {world_time}\n"
        #     f"NPC First Name: {first_name}\n"
        #     f"NPC Last Name: {last_name}\n"
        #     f"NPC Learned: {learned}\n"
        #     f"NPC Lifestyle: {lifestyle}\n"
        #     f"NPC Living Area: {living_area}\n"
        #     f"NPC Current Action: {readable_action}"
        # )
        output_text = (
            f"Time: {world_time}\n"
            f"NPC Current Action: {readable_action}"
        )
        return output_text

    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        # Return a default message if any error occurs
        return "NPC Current Action: not available"

def talkingInstruction(npcId, words):
    toReturn = f'''
    {{
        "actionId": 110,
        "npcId": "{npcId}",
        "data": {{
            "content": "{words}"
        }}
    }}
    '''
    return toReturn

# # Example input
# example_input = '''
# {
#     "world": {"time": 1738753261700},
#     "mapObj": [
#         {"oid": "zhongbencongType", "objName": "zhongbencongType", "type": "", "X": 463, "Y": 722, "status": "DEFAULT", "availableActions": []},
#         {"oid": "zhongbencongRead", "objName": "zhongbencongRead", "type": "", "X": 240, "Y": 688, "status": "DEFAULT", "availableActions": []},
#         {"oid": "zhongbencongFix", "objName": "zhongbencongFix", "type": "", "X": 370, "Y": 304, "status": "DEFAULT", "availableActions": []},
#         {"oid": "zhongbencongThink", "objName": "zhongbencongThink", "type": "", "X": 336, "Y": 721, "status": "DEFAULT", "availableActions": []}
#     ],
#     "npcs": [
#         {
#             "npcId": 10006,
#             "status": "idle",
#             "info": {
#                 "name": "wSatoshi",
#                 "firstName": "wSatoshi",
#                 "lastName": "wSatoshi",
#                 "type": "Engineer",
#                 "age": 20,
#                 "height": 180,
#                 "weight": 60,
#                 "body_style": "fit and sturdy",
#                 "innate": "Visionary, Analytical, Persistent",
#                 "learned": "wSatoshi is a hardworking researcher and engineer who reading, thinking, and using computer all day long.",
#                 "lifestyle": "wSatoshi spends his days reading, typing, thinking, and repairing the Coinnie, and he enjoy going out to meet other characters.",
#                 "living_area": "house",
#                 "property": "house"
#             },
#             "selling": [],
#             "items": [],
#             "action": {"actionName": "move", "actionId": 112},
#             "curAction": {
#                 "actionName": "move",
#                 "actionId": 112,
#                 "param": {"oid": "zhongbencongType"}
#             },
#             "mapData": [],
#             "surroundings": {
#                 "people": [],
#                 "items": [
#                     {"oid": "zhongbencongType", "objName": "zhongbencongType", "type": ""},
#                     {"oid": "zhongbencongThink", "objName": "zhongbencongThink", "type": ""}
#                 ]
#             },
#             "talk": {"isTalking": false}
#         }
#     ]
# }
# '''

# # Parse and print the NPC information
# output = parse_npc_info(example_input)
# print(output)