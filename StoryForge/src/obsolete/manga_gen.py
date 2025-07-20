import os
import json
import openai

# Set your OpenAI API key
openai.api_key = "“

# Paths to reference assets
BASE_DIR = os.path.dirname(__file__)
MANGA_SAMPLE_DIR = os.path.join(BASE_DIR, '../manga_sample')
AVATAR = os.path.join(MANGA_SAMPLE_DIR, 'ryan_avatar.png')
ROOM = os.path.join(MANGA_SAMPLE_DIR, 'ryan_oid_room.png')
ROOM_JSON = os.path.join(MANGA_SAMPLE_DIR, 'ryan_oid_room.png.json')
ILLUSTRATION_SAMPLE1 = os.path.join(MANGA_SAMPLE_DIR, 'illustration_sample.jpg')

OUTPUT_DIR = os.path.join(BASE_DIR, '../output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEGMENTED_SCENES_PATH = os.path.join(OUTPUT_DIR, 'segmented_scenes.json')
OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, 'main_illustrations_output.json')

def load_room_objects():
    """Load room objects from the JSON file"""
    try:
        with open(ROOM_JSON, 'r', encoding='utf-8') as f:
            room_data = json.load(f)
        return room_data.get('objects', [])
    except Exception as e:
        print(f"Warning: Could not load room objects from {ROOM_JSON}: {e}")
        return []

def build_main_illustration_prompt(scene, previous_illustrations):
    """Build optimized prompt for manga illustration"""
    
    # Simplified room objects (just names)
    room_objects = load_room_objects()
    object_names = [obj.get('name', '') for obj in room_objects if obj.get('name')]
    objects_str = ", ".join(object_names) if object_names else ""
    
    # Style anchor from previous illustrations
    style_anchor = ILLUSTRATION_SAMPLE1
    if previous_illustrations:
        style_anchor = previous_illustrations[-1]  # Use most recent
    
    prompt = f"""
Create a full-color 1:1 high-resolution Korean romance manga illustration.

STYLE: in the exact style of Light and Night official character art, Korean romance manga with soft pastel palette, elegant line art, dreamy atmosphere

SCENE: {scene.get('short description', '')}
CHARACTER: perfectly centered, waist-up portrait, well-lit from front, soft romantic lighting, interacting with {scene.get('object', '')}
OBJECTS: {objects_str}

POSITIVE: soft elegant colors, dreamy atmosphere, young-female aesthetic, romantic lighting, Korean manga style, delicate line art, soft pastel palette
NEGATIVE: monochrome, grayscale, black and white, western cartoon, painterly brush, 3D render, off-center, corner placement, dark lighting

Story context: {scene.get('full_story', '')} ({scene.get('scene_position', '')})
"""
    return prompt

def call_image_api(prompt):
    """Call DALL-E 3 API for image generation"""
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        
        if response.data is None or len(response.data) == 0:
            raise Exception("No image data returned from DALL-E 3 API")
        
        image_url = response.data[0].url
        print("Successfully generated image using DALL-E 3")
        return image_url
        
    except Exception as e:
        print(f"Image generation failed: {e}")
        raise

def save_image(image_url, save_path):
    """Save image from URL to local file"""
    import requests
    try:
        r = requests.get(image_url)
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(r.content)
        print(f"Image saved: {save_path}")
        return True
    except Exception as e:
        print(f"Failed to save image: {e}")
        return False

def main():
    """Generate manga illustrations for segmented scenes"""
    
    # Load segmented scenes
    with open(SEGMENTED_SCENES_PATH, 'r', encoding='utf-8') as f:
        scenes = json.load(f)
    
    output_scenes = []
    previous_illustrations = []
    
    for scene in scenes:
        print(f"Generating illustration for scene {scene.get('sequence_id', '?')}...")
        
        # Build prompt
        prompt = build_main_illustration_prompt(scene, previous_illustrations)
        
        # Generate image
        image_url = call_image_api(prompt)
        
        # Save image
        image_filename = f"main_illustration_{scene.get('sequence_id', '?')}.png"
        image_path = os.path.join(OUTPUT_DIR, image_filename)
        save_image(image_url, image_path)
        
        # Add to previous illustrations for style consistency
        previous_illustrations.append(image_path)
        
        # Store results
        scene['main_illustration_path'] = image_path
        scene['main_illustration_prompt'] = prompt
        output_scenes.append(scene)
        
        print(f"Generated: {image_path}")
    
    # Save output
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_scenes, f, ensure_ascii=False, indent=2)
    
    print(f"All illustrations generated. Output saved to: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()
