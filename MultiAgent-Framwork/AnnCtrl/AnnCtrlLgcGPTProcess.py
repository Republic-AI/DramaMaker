
import json
import copy
from datetime import datetime
import configparser
import os
from openai import OpenAI
import yaml

print("Current working directory:", os.getcwd())

config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

print("Config sections found:", config.sections())

if 'OpenAI' not in config:
    print("Error: 'OpenAI' section not found in config.ini")
openai_key = config['OpenAI']['key']
client = OpenAI(api_key=openai_key)


yaml_path = os.path.join(base_dir, 'char_config.yaml')

# Load the YAML file
if not os.path.exists(yaml_path):
    print(f"Error: {yaml_path} not found.")
else:
    with open(yaml_path, 'r', encoding='utf-8' ) as file:
        char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")


def generat_new_theme(npcId):
    # Find the NPC details by npcId
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']

    prompt = """
    You are {npc_name}, {npc_description}

    You are livestreaming in a simulated world. 
    
    
    Choose an intriguing topic for today's discussion, incorporating relevant details.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a knowledgeable thinker and inspiring speaker."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return completion.choices[0].message.content

def generate_new_Announcement(theme, npcId):
    # Find the NPC details by npcId
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']

    prompt = f"""
    You are {npc_name}, {npc_description}
    
    You are livestreaming in a simulated world about the topic: {theme}.
    Write an engaging and insightful speech.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a skilled and detail-oriented thinker, and an inspiring speech giver."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    speech = completion.choices[0].message.content

    prompt = f"""
    Transform the following speech into short sentences (each under 35 characters) formatted in JSON:
    
    Speech:
    {speech}
    
    Format:
    '["sentence 1", "sentence 2", "sentence 3"]'

    It is very important that your output can be loaded with json.loads()
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are skilled in concise and clear formatting."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    # Clean and validate the response
    result = completion.choices[0].message.content.strip("```json").strip("```")
    try:
        json_data = json.loads(result)  # Validate JSON
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        print("Returning empty list as fallback.")
        json_data = []  # Fallback to an empty list if JSON is invalid
    
    return json_data