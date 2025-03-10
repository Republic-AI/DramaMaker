import yaml
import openai
import json

# ==============================
# 1. Configuration
# ==============================

openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your actual API key
CHAR_CONFIG_PATH = "char_config.yaml"

# Example embedded prompt
USER_PROMPT = """
Satoshi discovered a major bug in Robot-Coinnie, which stirred heated debates with Elon. 
Popcat organizes a fishing festival to de-stress the town. 
Pepe wants to sell 'Meme-themed bug patches,' and Pippin plans a comedic coffee menu inspired by Satoshi’s midnight fixes.
Update each NPC's description, schedule, announcements Format, Tone, and Talk accordingly.
"""


# ==============================
# 2. Helper Functions
# ==============================

def load_yaml(file_path):
    """Load the existing YAML configuration file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def save_yaml(data, file_path):
    """Save data back to the YAML file, preserving structure."""
    with open(file_path, "w", encoding="utf-8") as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True)

def generate_npc_updates_from_prompt(prompt):
    """
    We want the AI to return a JSON structure like:
    {
      "events": [
        {
          "npcId": 10006,
          "impact": {
            "description": "...",
            "schedule": [
              { "time": "...", "action": "...", "details": "..." }
            ],
            "announcements": {
              "Format": "...",
              "Tone": "...",
              "Talk": ["...", "..."]
            }
          }
        },
        ...
      ]
    }

    Where 'announcements' now includes Format, Tone, and Talk.
    """
    system_instructions = (
        "You are an expert in generating story-based updates for a YAML config of NPCs. "
        "For each NPC, you only provide new 'description', 'schedule', and 'announcements'. "
        "Inside 'announcements', update 'Format', 'Tone', and 'Talk'. "
        "For 'schedule', each item must have 'time', 'action', and 'details'. "
        "The 'action' field is just a short name like 'Think' or 'Fix'—do not include location or actionId. "
        "Return valid JSON only."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": f"Update NPC data based on this prompt: {prompt}"}
        ],
        temperature=0.7
    )

    ai_message = response["choices"][0]["message"]["content"].strip()
    npc_updates = json.loads(ai_message)  # parse the JSON
    return npc_updates

def map_schedule_actions(npc_schedule, npc_available_actions):
    """
    Map each item in npc_schedule to a valid action from npc_available_actions.
    The AI only gave us: { "time": "06:00-06:30", "action": "Think", "details": "..." }.
    We must find a matching availableAction (by some keyword) and create the final schedule line.

    Returns a list of strings in the format:
      "• 06:00-06:30 Think Deeply: Reflect on AI ethics."
    """
    final_schedule = []

    # Create a quick lookup from actionName to a dictionary of all relevant info
    action_lookup = {}
    for action_item in npc_available_actions:
        # e.g. action_item = {
        #   'actionName': 'Think Deeply',
        #   'description': 'You contemplate complex ideas...',
        #   'location': 'zhongbencongThink',
        #   'actionId': 115
        # }
        action_name_lower = action_item["actionName"].lower()
        action_lookup[action_name_lower] = action_item

    for entry in npc_schedule:
        time_str = entry.get("time", "??:??-??:??")
        user_action = entry.get("action", "")  # e.g. "Think"
        details = entry.get("details", "")

        # Attempt a naive approach: match user's action to a known availableAction by partial keyword
        matched_action = None
        user_action_lower = user_action.lower()

        # Direct exact match on action name
        if user_action_lower in action_lookup:
            matched_action = action_lookup[user_action_lower]
        else:
            # Fuzzy or partial match
            for a_name, a_obj in action_lookup.items():
                if user_action_lower in a_name:
                    matched_action = a_obj
                    break
        
        if matched_action:
            official_action_name = matched_action["actionName"]
            final_line = f"• {time_str} {official_action_name}: {details}"
        else:
            # If we can't match, fallback to the user's action
            final_line = f"• {time_str} {user_action}: {details} (Unmapped Action)"

        final_schedule.append(final_line)

    return final_schedule

def apply_npc_updates(char_config, updates):
    """
    For each event in updates, find matching npcId, then update:
      - description
      - schedule (mapped to availableActions)
      - announcements (Format, Tone, Talk)

    Preserves 'availableActions' and other fields.
    """
    for event in updates.get("events", []):
        npc_id = event.get("npcId")
        impact = event.get("impact", {})

        # Find NPC in char_config
        for npc in char_config["npcCharacters"]:
            if npc["npcId"] == npc_id:
                # 1) Update description
                if "description" in impact:
                    npc["description"] = impact["description"]

                # 2) Update schedule
                if "schedule" in impact:
                    npc_available_actions = npc.get("availableActions", [])
                    if not npc_available_actions:
                        # If no local actions, just convert schedule to plain text
                        new_schedule_list = []
                        for s in impact["schedule"]:
                            new_schedule_list.append(
                                f"• {s.get('time', '??:??')} {s.get('action', '')}: {s.get('details', '')}"
                            )
                        npc["schedule"] = "\n".join(new_schedule_list)
                    else:
                        mapped_schedule = map_schedule_actions(impact["schedule"], npc_available_actions)
                        npc["schedule"] = "\n".join(mapped_schedule)

                # 3) Update announcements (Format, Tone, Talk)
                if "announcements" in impact:
                    # Ensure announcements field exists
                    if "announcements" not in npc:
                        npc["announcements"] = {}

                    ann_impact = impact["announcements"]
                    if "Format" in ann_impact:
                        npc["announcements"]["Format"] = ann_impact["Format"]
                    if "Tone" in ann_impact:
                        npc["announcements"]["Tone"] = ann_impact["Tone"]
                    if "Talk" in ann_impact:
                        npc["announcements"]["Talk"] = ann_impact["Talk"]

                break  # Stop searching once the correct NPC is updated

# ==============================
# 3. Main Execution
# ==============================
def main():
    # 1) Load current YAML
    char_config = load_yaml(CHAR_CONFIG_PATH)

    # 2) Generate updates from AI
    npc_updates = generate_npc_updates_from_prompt(USER_PROMPT)

    # 3) Apply updates (description, schedule, announcements)
    apply_npc_updates(char_config, npc_updates)

    # 4) Save back to YAML
    save_yaml(char_config, CHAR_CONFIG_PATH)
    print(f"Updates applied and saved to {CHAR_CONFIG_PATH}.")

if __name__ == "__main__":
    main()