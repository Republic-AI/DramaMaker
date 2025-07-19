try:
    import openai
except ImportError:
    raise ImportError("The 'openai' package is not installed. Please install it with 'pip install openai'.")
import os
import json
try:
    import yaml
except ImportError:
    raise ImportError("The 'pyyaml' package is not installed. Please install it with 'pip install pyyaml'.")
import re

# Set your OpenAI API key (for demo purposes, hardcoded here; in production, use env variable)
openai.api_key = "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"

def load_story(file_path):
    with open(file_path, 'r') as f:
        return f.read()

def load_npc_info(npc_yaml_path):
    with open(npc_yaml_path, 'r', encoding='utf-8') as f:
        npc_list = yaml.safe_load(f)
    # If the yaml is a list, return the first (or search by name if needed)
    if isinstance(npc_list, list):
        return npc_list[0]
    return npc_list

def load_scene_objects(scene_json_path):
    with open(scene_json_path, 'r', encoding='utf-8') as f:
        scene_data = json.load(f)
    return scene_data['objects']

def segment_story(story, character, npc_info=None, scene_objects=None):
    npc_desc = npc_info.get('description', '') if npc_info else ''
    npc_tone = npc_info.get('announcements', {}).get('Tone', '') if npc_info else ''
    npc_talk = npc_info.get('announcements', {}).get('Talk', '') if npc_info else ''
    objects_str = json.dumps(scene_objects, ensure_ascii=False, indent=2) if scene_objects else ''
    json_example = '''[
  {
    "sequence_id": 1,
    "character(s) present": "Ryan",
    "action": "sleep",
    "object": "single bed",
    "short description": "Ryan is lying on the single bed in the bottom-left corner of the room.",
    "full_story": "Ryan tries to cook a meal but struggles with the recipe. He burns the food and gets frustrated, then decides to take a break and read a book to calm down.",
    "scene_position": "beginning"
  }
]'''
    prompt = f"""
You are a manga scene extractor.

Break the following story into 1–3 key visual scenes.
Each scene must:
- Use exactly one action from the available actions below.
- Use exactly one object from the available objects below.
- Happen in the same room (see room objects list).
- Logically follow from the previous scene (smooth progression, no abrupt skips).
- Be described simply, 1–2 sentences, only what is visually present.

If a requested action is not available, choose the closest one.

CONTINUITY:
Each subsequent scene should logically follow from the previous one. Do not skip context abruptly. Use the available actions and objects in a way that feels like a natural progression within the same room.

SPLITTING:
Break the story into 1–3 visual moments, each based on exactly one available action and one available object. Keep it simple and grounded in the room layout.

For each scene, include:
- full_story: The complete user story for context
- scene_position: Where this scene fits in the overall story ("beginning", "middle", "end")

Available objects and actions:
{objects_str}

Character background:
{npc_desc}

Personality tone:
{npc_tone}

Typical sayings:
{npc_talk}

User story:
{story}
Main character: {character}

Output format example(for format reference only, do not use it as output):
{json_example}

Output only the JSON list, and nothing else.
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200
    )
    content = response.choices[0].message.content
    if content is None:
        print("Warning: No content returned from OpenAI for scene segmentation.")
        scenes = []
    else:
        try:
            scenes = json.loads(content)
        except Exception as e:
            print("Error parsing scene segmentation response:", e)
            print("Raw response:", content)
            # Try to extract the first JSON list from the output
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                try:
                    scenes = json.loads(match.group(0))
                except Exception as e2:
                    print('Still failed to parse JSON:', e2)
                    scenes = []
            else:
                scenes = []
            debug_path = os.path.join(os.path.dirname(__file__), '../output/debug_gpt_output.txt')
            with open(debug_path, 'w', encoding='utf-8') as dbg:
                dbg.write(content if content else '')
    return scenes

def ensure_output_dir():
    output_dir = os.path.join(os.path.dirname(__file__), '../output')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    # Example usage
    base_dir = os.path.dirname(__file__)
    story_path = os.path.join(base_dir, '../examples/ryan_story.txt')
    npc_yaml_path = os.path.join(base_dir, '../examples/ryan_npc.yaml')
    scene_json_path = os.path.join(base_dir, '../manga_sample/ryan_oid_room.png.json')
    character = "Ryan"
    story = load_story(story_path)
    npc_info = load_npc_info(npc_yaml_path)
    scene_objects = load_scene_objects(scene_json_path)
    scenes = segment_story(story, character, npc_info, scene_objects)

    output_dir = ensure_output_dir()
    # Save segmented scenes as JSON
    scenes_json_path = os.path.join(output_dir, 'segmented_scenes.json')
    with open(scenes_json_path, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    print(f"Segmented scenes saved to: {scenes_json_path}")

    # Also print to console for quick check
    print("\n--- Segmented Scenes ---")
    for i, scene in enumerate(scenes):
        print(f"Scene {i+1}: {scene}")

if __name__ == "__main__":
    main()

