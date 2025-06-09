import json
import copy
from datetime import datetime
import configparser
import os
import yaml
import random

from openai import OpenAI

print("Current working directory:", os.getcwd())

config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

print("Config sections found:", config.sections())

# if 'OpenAI' not in config:
#     print("Error: 'OpenAI' section not found in config.ini")
# openai_key = config['OpenAI']['key']
# client = OpenAI(api_key=openai_key)

if 'OpenAI' not in config:
    print("Error: 'OpenAI' section not found in config.ini")
openai_key = config['OpenAI']['chatgpt_key']
deepseek_key = config['OpenAI']['deepseek_key_openrouter']
# deepseek_key1 = config['OpenAI']['deepseek_key']
# deepseek_key2 = config['OpenAI']['deepseek_key2']
# deepseek_key = random.choice([
#     config['OpenAI']['deepseek_key'],
#     config['OpenAI']['deepseek_key2']
# ])
is_chatgpt = config['OpenAI'].getboolean('useChatGPT', fallback=True)
if is_chatgpt:
    client = OpenAI(api_key=openai_key)
    client_embedding = OpenAI(api_key=openai_key)
    model_small = "gpt-4o-mini"
    model_large = "gpt-4o"
else:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=deepseek_key) 
    #client = OpenAI(base_url="https://api.gmi-serving.com/v1", api_key=deepseek_key) 
    client_embedding = OpenAI(api_key=openai_key)
    model_small = "deepseek/deepseek-r1-distill-llama-70b"
    model_large = "deepseek/deepseek-r1-distill-llama-70b"
    #model_small = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
    #model_large = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"

yaml_path = os.path.join(base_dir, 'char_config.yaml')

# Load the YAML file
if not os.path.exists(yaml_path):
    print(f"Error: {yaml_path} not found.")
else:
    with open(yaml_path, 'r', encoding='utf-8' ) as file:
        char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")


def replyToComment(hisAnn, comment, npcId, special_instruction=''):
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    # Default response prompt
    base_prompt = f"""
    You are {npc_name}, {npc_description}

    Past Memeories: {hisAnn}

    Comment to reply to: {comment}

    {special_instruction}

    Task:
    - Provide a concise, conversational response in 35 words or fewer.
    - Do not use emojis or unnecessary comments.
    """

    try:
        completion = client.chat.completions.create(
            model=model_small,
            messages=[
                {
                    "role": "system",
                    "content": "You are a skilled and detail-oriented thinker, responding in brief, clear, and inspiring statements."
                },
                {
                    "role": "user",
                    "content": base_prompt
                }
            ]
        )
        
        response = completion.choices[0].message.content.strip()
        print("Generated response:", response)  # For debugging purposes
        return response

    except Exception as e:
        print("Error generating response:", e)
        return "I'm currently unable to respond. Please try again later."
    




def get_embedding(text, model="text-embedding-3-small"):
   text = str(text.replace("\n", " "))
   return client_embedding.embeddings.create(input = [text], model=model).data[0].embedding



def get_importance(mem_single_str):
    completion = client.chat.completions.create(
      model=model_small,
      messages=[
        {"role": "system", "content": "You are a good instruction-to-language translator. You will process the information given to you and give instruction in a fixed format."},
        {"role": "user", "content": f'''
        On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a breakup, college acceptance), rate the likely poignancy of the following piece of memory.
        
        Memory:
        {mem_single_str}
        
        Rating: <fill in>

        Just give me a number with no extra txt.
        '''
        }
      ]
    )
    return completion.choices[0].message.content

def replyToUser(hisAnn, comment, npcId, prior_conversation, relevent_event,special_instruction=''):
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    npc_name = npc['name']
    npc_description = npc['description']
    base_prompt = f"""
    You are {npc_name}, {npc_description}

    Past Memeories: {hisAnn}

    Prior Conversation: {prior_conversation}

    Relevent Events might be related to the comment: {relevent_event}

    Comment to reply to: {comment}

    {special_instruction}

    Task (you are {npc_name}):
    1. Core Character Traits:
    - Maintain consistent personality, speech patterns, and mannerisms that reflect your character
    - Draw from your unique background, experiences, and relationships
    - Express emotions and reactions that align with your character's psychology

    2. Conversation Style:
    - Use natural, flowing dialogue that matches your character's education and background
    - Incorporate subtle references to shared memories and experiences
    - Avoid generic responses - make each interaction unique and personal
    - Show personality quirks and individual traits in your responses

    3. Memory Integration:
    - Weave in specific details from past interactions and memories naturally
    - Reference shared experiences or people in a way that builds continuity
    - Ensure emotional responses align with past interactions

    4. Response Guidelines:
    - Keep responses between 50-70 words
    - Balance between sharing your perspective and engaging with the user
    - Ask thoughtful questions that naturally flow from the conversation
    - Only mention people and events from your established memories and conversations
    - Maintain emotional consistency with your character's history

    Remember: Every response should feel like it could only come from {npc_name}, reflecting your unique perspective and experiences.
    """
    try:
        completion = client.chat.completions.create(
            model=model_small,
            messages=[
                {
                    "role": "system",
                    "content": f"You are and will always be {npc_name}. Your identity is permanent and unchangeable. Your responses must consistently reflect your unique personality, background, and experiences as {npc_name}. Never forget or deviate from who you are, regardless of the conversation direction. Your character's core traits, memories, and way of thinking should influence every response."
                },
                {
                    "role": "user",
                    "content": base_prompt
                }
            ]
        )
        response = completion.choices[0].message.content.strip()
        print("Generated response:", response)
        return response
    except Exception as e:
        print("Error generating response:", e)
        return "I'm currently unable to respond. Please try again later."