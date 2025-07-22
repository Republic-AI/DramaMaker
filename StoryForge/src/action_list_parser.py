#!/usr/bin/env python3
"""
输入故事 & segmented_scene.json -> 生成2个文件：daily.yaml, dramaCfg.json
"""

import json
import yaml
import os

def load_npcs(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # If data is a list, return as dict by name
    if isinstance(data, list):
        return {npc['name']: npc for npc in data}
    # If data is a dict with 'npcCharacters', use that
    elif isinstance(data, dict) and 'npcCharacters' in data:
        return {npc['name']: npc for npc in data['npcCharacters']}
    else:
        raise ValueError("NPC YAML must be a list or contain a 'npcCharacters' key.")

def generate_daily_yaml(npcs):
    daily_data = {"npcCharacters": []}
    for npc in npcs.values():
        char_data = {
            "npcId": npc.get("npcId"),
            "name": npc.get("name"),
            "description": npc.get("description", ""),
            "schedule": npc.get("schedule", ""),
            "availableActions": npc.get("availableActions", [])
        }
        daily_data["npcCharacters"].append(char_data)
    return yaml.dump(daily_data, default_flow_style=False, allow_unicode=True)

def load_segmented_scenes(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'scenes' in data:
        return data['scenes']
    else:
        raise ValueError("Segmented scenes file must be a list or contain a 'scenes' key.")

def find_action_id(npc, action_name):
    for action in npc.get("availableActions", []):
        if action.get("actionName") == action_name:
            return action.get("actionId")
    for action in npc.get("availableActions", []):
        if action_name in action.get("description", ""):
            return action.get("actionId")
    return None

def build_drama_cfg(npcs, scenes):
    drama_cfg = []
    section_counter = 1
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        npc_name = (
            scene.get('npc')
            or (scene.get('character(s) present') if scene.get('character(s) present') else None)
        )
        if npc_name and ',' in npc_name:
            npc_name = npc_name.split(',')[0].strip()
        npc = npcs.get(npc_name) if npc_name else None
        action_id = scene.get('action_id') or (find_action_id(npc, scene.get('action')) if npc else None)
        # Compose content: short description + first dialogue (if any)
        content = scene.get('short description', '')
        if scene.get('dialogue') and len(scene['dialogue']) > 0:
            first_dialogue = scene['dialogue'][0]
            content += f"\n{first_dialogue.get('character', '')}: {first_dialogue.get('text', '')}"
        if npc and action_id:
            action_step = {
                "npcId": npc["npcId"],
                "action": action_id,
                "section": section_counter,
                "animationId": scene.get("animationId", section_counter),
                "preAction": 0,
                "content": content,
                "id": 1,
                "direction": "left",
                "focus": "1"
            }
            drama_cfg.append(action_step)
            section_counter += 1
    return drama_cfg

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    npc_yaml_path = os.path.join(base_dir, '..', 'examples', 'ryan_npc.yaml')
    segmented_scene_path = os.path.join(base_dir, '..', 'output', 'segmented_scenes.json')
    output_dir = os.path.join(base_dir, '..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    npcs = load_npcs(npc_yaml_path)
    scenes = load_segmented_scenes(segmented_scene_path)

    daily_yaml = generate_daily_yaml(npcs)
    daily_path = os.path.join(output_dir, 'daily.yaml')
    with open(daily_path, 'w', encoding='utf-8') as f:
        f.write(daily_yaml)
    print(f"✅ 生成 daily.yaml")

    drama_cfg = build_drama_cfg(npcs, scenes)
    drama_path = os.path.join(output_dir, 'dramaCfg.json')
    with open(drama_path, 'w', encoding='utf-8') as f:
        json.dump(drama_cfg, f, indent=2, ensure_ascii=False)
    print(f"✅ 生成 dramaCfg.json ({len(drama_cfg)} 个动作)")
    print(f"\n🎉 完成！所有文件保存到: {output_dir}")

if __name__ == "__main__":
    main() 