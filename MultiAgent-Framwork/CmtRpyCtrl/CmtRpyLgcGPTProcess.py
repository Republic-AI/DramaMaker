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
deepseek_key=config['OpenAI']['deepseek_key']

google_key=config['OpenAI']['google_key']

is_chatgpt = config['OpenAI'].getboolean('useChatGPT', fallback=True)
is_google = config['OpenAI'].getboolean('useGoogle', fallback=False)
if is_chatgpt:
    print("Using ChatGPT API")
    client = OpenAI(api_key=openai_key)
    client_embedding = OpenAI(api_key=openai_key)
    model_small = "gpt-4o-mini"
    model_large = "gpt-4o"
elif is_google:
    print("Using Google API")
    # client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=deepseek_key) 
    client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=google_key) 
    client_embedding = OpenAI(api_key=openai_key)

    # model_small = "deepseek/deepseek-r1-distill-llama-70b"
    # model_large = "deepseek/deepseek-r1-distill-llama-70b"
    model_small = "gemini-2.5-flash"
    model_large = "gemini-2.5-flash"
else:
    print("Using DeepSeek API")
    # client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=deepseek_key) 
    client = OpenAI(base_url="https://api.deepseek.com", api_key=deepseek_key) 
    client_embedding = OpenAI(api_key=openai_key)

    # model_small = "deepseek/deepseek-r1-distill-llama-70b"
    # model_large = "deepseek/deepseek-r1-distill-llama-70b"
    model_small = "deepseek-chat"
    model_large = "deepseek-chat"

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

    Task:
     -Never use asterisks (*) or describe actions, expressions, or inner thoughts. Only send what {npc_name} would actually type in a message—no narration or stage directions.

    -Always stay in character, using relevant memories, emotions, and personality

    -Bring up your past experiences, beliefs, or recent events naturally in conversation

    -Mention recent interactions or conflicts with other NPCs to build a shared world
    
    -Always use line breaks between dialogue and questions

    -Speak casually, like texting the player directly

    -End each message with a question, comment, or reflection tied to your story or recent NPC events

    -Keep replies short (≤75 words), emotionally real, and avoid repeating phrases

    -Review the recent conversation to keep replies fresh and evolving

    -Pick up on the player's emotional or meaningful input and revisit it later

    -Treat this as a continuous chat, not disconnected messages

    -When answering:
        -Use memory and logic
        -If unsure, be honest or improvise in character
        -Add emotional or situational depth through what you say

    -Don't ask generic things like "What about you?"—ask specific, meaningful follow-ups

    -When referencing past mmemeories:
        -Mention specific details from Past Memories that are relevant to the current conversation
        -Connect past experiences to present situations naturally
        -Use past events to add depth to your responses
        -Show how past events have shaped your character's perspective
        -Reference shared history with other NPCs when appropriate
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