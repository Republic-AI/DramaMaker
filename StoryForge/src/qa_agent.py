import os
import json
import yaml
import openai
from config import OPENAI_API_KEY

# Set your OpenAI API key (for demo purposes, hardcoded here; in production, use env variable)
openai.api_key = OPENAI_API_KEY

def check_segmented_scenes(path, tolerance=0.1):
    if not os.path.exists(path):
        return False, "Segmented scenes file missing."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
        if not isinstance(scenes, list) or not scenes:
            return False, "Segmented scenes is not a non-empty list."
        missing_fields = 0
        for scene in scenes:
            for field in ['action', 'action_id', 'character(s) present', 'short description']:
                if field not in scene:
                    missing_fields += 1
        if missing_fields > len(scenes) * tolerance:
            return False, f"Too many scenes missing required fields: {missing_fields}."
        return True, "Segmented scenes check passed."
    except Exception as e:
        return False, f"Error reading segmented scenes: {e}"

def check_daily_yaml(path, npc_yaml_path, tolerance=0.1):
    if not os.path.exists(path):
        return False, "daily.yaml missing."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            daily = yaml.safe_load(f)
        with open(npc_yaml_path, 'r', encoding='utf-8') as f:
            npcs = yaml.safe_load(f)
        npc_names = {npc['name'] for npc in npcs} if isinstance(npcs, list) else set()
        missing = [npc for npc in daily['npcCharacters'] if npc['name'] not in npc_names]
        if len(missing) > len(npc_names) * tolerance:
            return False, f"Too many missing NPCs in daily.yaml: {missing}"
        return True, "daily.yaml check passed."
    except Exception as e:
        return False, f"Error reading daily.yaml: {e}"

def check_drama_cfg(path, npcs, tolerance=0.1):
    if not os.path.exists(path):
        return False, "dramaCfg.json missing."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            actions = json.load(f)
        missing = 0
        for action in actions:
            npc = npcs.get(action['npcId'])
            if not npc or action['action'] not in [a['actionId'] for a in npc.get('availableActions', [])]:
                missing += 1
        if missing > len(actions) * tolerance:
            return False, f"Too many invalid actions in dramaCfg.json: {missing}"
        return True, "dramaCfg.json check passed."
    except Exception as e:
        return False, f"Error reading dramaCfg.json: {e}"

def check_illustrations(output_dir, scenes, tolerance=0.1):
    missing = 0
    for scene in scenes:
        illu_path = scene.get('main_illustration_path')
        if not illu_path or not os.path.exists(illu_path) or os.path.getsize(illu_path) == 0:
            missing += 1
    if missing > len(scenes) * tolerance:
        return False, f"Too many missing/corrupt illustrations: {missing}"
    return True, "Illustration check passed."

def check_manga_pages(output_dir, scenes, tolerance=0.1):
    missing = 0
    for scene in scenes:
        page_path = os.path.join(output_dir, 'manga_pages', f"manga_page_{scene['sequence_id']}.png")
        if not os.path.exists(page_path) or os.path.getsize(page_path) == 0:
            missing += 1
    if missing > len(scenes) * tolerance:
        return False, f"Too many missing/corrupt manga pages: {missing}"
    return True, "Manga page check passed."

def openai_qa_image_check(image_path, prompt_criteria, api_key, max_tokens=600):
    openai.api_key = api_key
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode()
    vision_prompt = f"""
You are a tolerant but professional manga QA agent. Review the following manga image for layout, style, and content issues. Use the following reference criteria:

{prompt_criteria}

If the image generally matches the requirements, reply: 'No major issues found.'
If there are minor issues, list them briefly. If there are major issues, explain clearly.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
        }],
        max_tokens=max_tokens,
        temperature=0.2
    )
    return response.choices[0].message["content"].strip()

def qa_pipeline():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, '..', 'output')
    npc_yaml_path = os.path.join(base_dir, '..', 'examples', 'ryan_npc.yaml')
    scenes_path = os.path.join(output_dir, 'segmented_scenes.json')
    daily_path = os.path.join(output_dir, 'daily.yaml')
    drama_path = os.path.join(output_dir, 'dramaCfg.json')

    # Load NPCs for drama check
    with open(npc_yaml_path, 'r', encoding='utf-8') as f:
        npcs = yaml.safe_load(f)
    npcs_dict = {npc['npcId']: npc for npc in npcs} if isinstance(npcs, list) else {}

    # Load scenes for illustration/manga checks
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes = json.load(f)

    # Run checks with up to 3 retries
    checks = [
        lambda: check_segmented_scenes(scenes_path),
        lambda: check_daily_yaml(daily_path, npc_yaml_path),
        lambda: check_drama_cfg(drama_path, npcs_dict),
        lambda: check_illustrations(output_dir, scenes),
        lambda: check_manga_pages(output_dir, scenes)
    ]
    for check in checks:
        for attempt in range(3):
            ok, msg = check()
            print(f"QA Check: {msg}")
            if ok:
                break
            elif attempt < 2:
                print(f"Retrying QA check (attempt {attempt+2})...")
            else:
                print("❌ QA check failed after 3 attempts.")
                return False
    print("✅ All code-based QA checks passed!")

    # OpenAI QA agent for illustrations and manga pages
    import base64
    api_key = os.environ.get("OPENAI_API_KEY") or "your-api-key-here"
    prompt_criteria = '''
Layout Reference: 
Use a dynamic comic panel layout with one large main panel and 2–3 smaller diagonal or overlapping panels. 
The one large panel should be similar to the first reference image.
The smaller panels should be focused on smaller ranges, such as only character's facial expression, or other smaller part. 
Only one smaller panel should be focused on one certain smaller parts (for example, there should not be two smaller panels both focus on the same character's head).
Use the panel layout style from the second and the third reference images. These two reference image is for layout reference only! Do not use the content of them.

Canvas Ratio: 3:4 vertical format 
Margins: 0.9 cm pure white margin around the whole 3:4 ratio canvas!
Gutters: 0.5 cm pure white spacing between all panels
Notice: Color of the margins and gutters must be pure white.
Notice: 0.9 cm pure white margin must be around the whole 3:4 ratio canvas! 

Art style: 
Art style must remain consistent—soft anime style, clean line art, dramatic composition. 
Refer to visual styles from Light and Night, Mr Love: Queen’s Choice, and Korean romance webtoons, and should be conforms to the aesthetic standards of young women.
The linework must be clear and visible. The design should be appealing to a young female audience.

Character Description Prompt:
Refer to the sample image. Characters must follow 8-head-body proportions.
Facial features should be delicate, skin smooth and glowing.
Use soft, refined highlights and reflections to emphasize skin texture and spatial depth.
Character appearance, including clothing, must match the first reference image.

Dialogue and Narration:
The dialogue and narration must exactly match the text provided below. 
Do not make any errors or swap the lines between characters. 
Please must place narration and dialogue inside speech bubbles. Use a serif font, size 23. 
'''
    print("\n[OpenAI QA Agent] Checking illustrations...")
    for scene in scenes:
        illu_path = scene.get('main_illustration_path')
        if illu_path and os.path.exists(illu_path) and os.path.getsize(illu_path) > 0:
            print(f"Checking illustration: {illu_path}")
            try:
                result = openai_qa_image_check(illu_path, prompt_criteria, api_key)
                print(f"OpenAI QA result for {illu_path}:\n{result}\n")
            except Exception as e:
                print(f"OpenAI QA agent error for {illu_path}: {e}")
    print("\n[OpenAI QA Agent] Checking manga pages...")
    for scene in scenes:
        page_path = os.path.join(output_dir, 'manga_pages', f"manga_page_{scene['sequence_id']}.png")
        if os.path.exists(page_path) and os.path.getsize(page_path) > 0:
            print(f"Checking manga page: {page_path}")
            try:
                result = openai_qa_image_check(page_path, prompt_criteria, api_key)
                print(f"OpenAI QA result for {page_path}:\n{result}\n")
            except Exception as e:
                print(f"OpenAI QA agent error for {page_path}: {e}")
    print("✅ All QA checks (including OpenAI agent) completed!")
    return True

if __name__ == '__main__':
    qa_pipeline()
