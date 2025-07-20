import os
import json
import requests
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont
import base64
import mimetypes

# Try to import Runway API components
try:
    from runwayml import RunwayML, TaskFailedError
    RUNWAY_AVAILABLE = True
    print("✓ RunwayML SDK available")
except ImportError:
    RUNWAY_AVAILABLE = False
    print("⚠️ RunwayML SDK not available, will use placeholder images")

# Set your API credentials
RUNWAY_API_KEY = "key_536cfd03902f0448624e34cddf7be4cfaf04ca75f5920ac5098fef3fd158cb1deb1cf1e4fef7e73c6f18faf74b3c0c1b218af61a607c1b0813c3039dda886330"

# Paths to reference assets - FIXED PATHS
BASE_DIR = os.path.dirname(__file__)
MANGA_SAMPLE_DIR = os.path.join(BASE_DIR, '../manga_sample')
AVATAR = os.path.join(MANGA_SAMPLE_DIR, 'ryan_avatar.png')
ROOM = os.path.join(MANGA_SAMPLE_DIR, 'ryan_oid_room.png')
ROOM_JSON = os.path.join(MANGA_SAMPLE_DIR, 'ryan_oid_room.png.json')
ILLUSTRATION_SAMPLE1 = os.path.join(MANGA_SAMPLE_DIR, 'illustration_sample.jpg')

# FIXED OUTPUT DIRECTORY
OUTPUT_DIR = os.path.join(BASE_DIR, '../output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEGMENTED_SCENES_PATH = os.path.join(OUTPUT_DIR, 'segmented_scenes.json')
OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, 'segmented_scenes_illustration.json')

def debug_file_access():
    """Debug function to check if all reference files are accessible"""
    print("\n=== DEBUGGING FILE ACCESS ===")
    
    files_to_check = [
        ("Avatar", AVATAR),
        ("Room", ROOM),
        ("Room JSON", ROOM_JSON),
        ("Style Reference", ILLUSTRATION_SAMPLE1),
        ("Segmented Scenes", SEGMENTED_SCENES_PATH),
        ("Output Directory", OUTPUT_DIR)
    ]
    
    for name, path in files_to_check:
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"{name}: {path}")
        print(f"  Exists: {'✓' if exists else '✗'}")
        if exists:
            print(f"  Size: {size} bytes")
            if path.endswith('.json'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"  JSON Keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                except Exception as e:
                    print(f"  JSON Error: {e}")
        print()

def load_room_objects():
    """Load room objects from the JSON file"""
    try:
        print(f"Loading room objects from: {ROOM_JSON}")
        with open(ROOM_JSON, 'r', encoding='utf-8') as f:
            room_data = json.load(f)
        objects = room_data.get('objects', [])
        print(f"Loaded {len(objects)} room objects")
        for obj in objects:
            print(f"  - {obj.get('name', 'Unknown')}")
        return objects
    except Exception as e:
        print(f"Warning: Could not load room objects from {ROOM_JSON}: {e}")
        return []

def build_main_illustration_prompt(scene, previous_illustrations):
    """Build optimized prompt for manga illustration with all reference assets"""
    
    print(f"\n=== BUILDING PROMPT FOR SCENE {scene.get('sequence_id', '?')} ===")
    
    # Load room objects for context
    room_objects = load_room_objects()
    object_names = [obj.get('name', '') for obj in room_objects if obj.get('name')]
    objects_str = ", ".join(object_names) if object_names else ""
    print(f"Room objects: {objects_str}")
    
    # Enhanced prompt with ALL reference assets
    scene_desc = scene.get('short description', '')
    character_action = f"interacting with {scene.get('object', '')}" if scene.get('object') else ""
    
    # Get scene mood for context (removed dialogue)
    scene_mood = scene.get('scene_mood', '')
    
    print(f"Scene description: {scene_desc}")
    print(f"Character action: {character_action}")
    print(f"Scene mood: {scene_mood}")
    
    # SIMPLIFIED PROMPT for Runway API compatibility
    prompt = f"""
Korean romance manga illustration, soft pastel colors, elegant line art, dreamy atmosphere.

Character: young male with gentle features, soft expression, emotional depth
Setting: cozy room with warm lighting
Scene: {scene_desc}
Action: {character_action}
Objects: {objects_str}

Style: Light and Night official character art, Korean manga aesthetic
Mood: {scene_mood}

Soft elegant colors, dreamy atmosphere, romantic lighting, delicate line art, beautiful composition.
"""
    
    # Clean up the prompt
    prompt = ' '.join(prompt.split())
    prompt = prompt.replace(', ,', ',').replace(',,', ',')
    
    print(f"Generated prompt length: {len(prompt)} characters")
    print("Prompt preview (first 200 chars):", prompt[:200] + "..." if len(prompt) > 200 else prompt)
    
    return prompt

def get_image_as_data_uri(image_path):
    """Convert local image to data URI for Runway API"""
    try:
        print(f"Converting image to data URI: {image_path}")
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        content_type = mimetypes.guess_type(image_path)[0]
        if not content_type:
            content_type = "image/png"  # Default
        
        data_uri = f"data:{content_type};base64,{base64_image}"
        print(f"Successfully converted to data URI (length: {len(data_uri)} chars)")
        return data_uri
    except Exception as e:
        print(f"Error converting image to data URI: {e}")
        return None

def call_runway_gen4_image_api(prompt, reference_images=None):
    """Call Runway Gen-4 Image API for manga illustration generation"""
    
    if not RUNWAY_AVAILABLE:
        print("RunwayML SDK not available, creating placeholder image")
        return create_placeholder_image("Runway API not available")
    
    try:
        print("\n=== CALLING RUNWAY GEN-4 IMAGE API ===")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Reference images: {len(reference_images) if reference_images else 0}")
        
        # Initialize the Runway client with API key
        print("Initializing Runway client...")
        client = RunwayML(api_key=RUNWAY_API_KEY)
        
        # Prepare reference images - use ALL available references
        reference_images_list = []
        if reference_images:
            print("Processing reference images...")
            for idx, ref_image in enumerate(reference_images):
                print(f"  Processing reference {idx + 1}: {ref_image}")
                if os.path.exists(ref_image):
                    # Convert local file to data URI
                    data_uri = get_image_as_data_uri(ref_image)
                    if data_uri:
                        reference_images_list.append({
                            'uri': data_uri,
                            'tag': f'ref{idx}'
                        })
                        # Update prompt to reference the image
                        prompt = f"@ref{idx} style, {prompt}"
                        print(f"  ✓ Added reference {idx + 1} to prompt")
                    else:
                        print(f"  ✗ Failed to convert reference {idx + 1}")
                else:
                    print(f"  ✗ Reference file not found: {ref_image}")
        else:
            print("No reference images provided")
        
        print(f"Final prompt length: {len(prompt)} characters")
        print("Creating text-to-image task...")
        
        # Create the task using the official SDK
        # If no reference images, use a simpler approach
        if reference_images_list:
            print("Creating task with reference images...")
            task = client.text_to_image.create(
                model='gen4_image',
                ratio='1920:1080',
                prompt_text=prompt,
                reference_images=reference_images_list
            )
        else:
            print("Creating task without reference images...")
            # Try using the basic text-to-image endpoint
            task = client.text_to_image.create(
                model='gen4_image',
                ratio='1920:1080',
                prompt_text=prompt
            )
        
        print("Waiting for task completion...")
        
        # Wait for the task to complete
        result = task.wait_for_task_output()
        
        print("Task completed successfully!")
        
        # Get the image URL from the result
        if result.output and len(result.output) > 0:
            image_url = result.output[0]
            print(f"Image URL: {image_url}")
            
            # Download the image
            print("Downloading image...")
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(img_response.content)
                temp_file.close()
                print("Image downloaded successfully")
                return temp_file.name
            else:
                print(f"Failed to download image: {img_response.status_code}")
                return None
        else:
            print("No image URL in output")
            return None
            
    except Exception as e:
        print(f"Runway API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_placeholder_image(text="Placeholder"):
    """Create a placeholder image when API is not available"""
    print(f"Creating placeholder image with text: {text}")
    # Create a 1024x1024 image with a light blue background
    img = Image.new('RGB', (1024, 1024), color='#E3F2FD')
    draw = ImageDraw.Draw(img)
    
    # Add text to indicate this is a placeholder
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
    
    # Draw text in the center
    lines = text.split('\n')
    y_offset = 400
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1024 - text_width) // 2
        draw.text((x, y_offset), line, fill='#1976D2', font=font)
        y_offset += 60
    
    # Save the placeholder image to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    temp_file.close()
    
    print(f"Placeholder image created: {temp_file.name}")
    return temp_file.name

def save_image(image_source, save_path):
    """Save image from URL or local file to local file"""
    try:
        import shutil
        
        print(f"Saving image from {image_source} to {save_path}")
        
        # Check if image_source is a local file path
        if os.path.exists(image_source):
            # Copy local file
            shutil.copy2(image_source, save_path)
            print(f"Image saved: {save_path}")
            return True
        else:
            # Try to download from URL
            r = requests.get(image_source)
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
    
    print("=== Manga Illustration Generator ===")
    print(f"RunwayML Available: {RUNWAY_AVAILABLE}")
    print()
    
    # Debug file access first
    debug_file_access()
    
    # Check all reference assets
    print("=== Checking Reference Assets ===")
    print(f"Avatar: {AVATAR} - {'✓' if os.path.exists(AVATAR) else '✗'}")
    print(f"Room: {ROOM} - {'✓' if os.path.exists(ROOM) else '✗'}")
    print(f"Room JSON: {ROOM_JSON} - {'✓' if os.path.exists(ROOM_JSON) else '✗'}")
    print(f"Style Reference: {ILLUSTRATION_SAMPLE1} - {'✓' if os.path.exists(ILLUSTRATION_SAMPLE1) else '✗'}")
    print(f"Output Directory: {OUTPUT_DIR} - {'✓' if os.path.exists(OUTPUT_DIR) else '✗'}")
    print()
    
    # Load segmented scenes
    try:
        print(f"Loading segmented scenes from: {SEGMENTED_SCENES_PATH}")
        with open(SEGMENTED_SCENES_PATH, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
        print(f"Loaded {len(scenes)} scenes from {SEGMENTED_SCENES_PATH}")
        
        # Debug scene content
        for i, scene in enumerate(scenes):
            print(f"Scene {i+1}: {scene.get('short description', 'No description')}")
            print(f"  Dialogue lines: {len(scene.get('dialogue', []))}")
            print(f"  Mood: {scene.get('scene_mood', 'No mood')}")
        
    except FileNotFoundError:
        print(f"\nError: Could not find {SEGMENTED_SCENES_PATH}")
        print("Please run manga_sty_parser.py first to generate segmented scenes")
        return
    
    output_scenes = []
    previous_illustrations = []
    
    # Use ALL available reference images for style consistency
    reference_images = []
    if os.path.exists(ILLUSTRATION_SAMPLE1):
        print(f"Using style reference: {ILLUSTRATION_SAMPLE1}")
        reference_images.append(ILLUSTRATION_SAMPLE1)
    
    if os.path.exists(AVATAR):
        print(f"Using character reference: {AVATAR}")
        reference_images.append(AVATAR)
    
    if os.path.exists(ROOM):
        print(f"Using setting reference: {ROOM}")
        reference_images.append(ROOM)
    
    print(f"Total reference images: {len(reference_images)}")
    
    for scene in scenes:
        scene_id = scene.get('sequence_id', '?')
        print(f"\n--- Generating illustration for scene {scene_id} ---")
        print(f"Scene: {scene.get('short description', 'No description')}")
        print(f"Dialogue: {len(scene.get('dialogue', []))} lines")
        print(f"Mood: {scene.get('scene_mood', 'No mood')}")
        
        # Build prompt
        prompt = build_main_illustration_prompt(scene, previous_illustrations)
        
        # Generate image with Runway Gen-4 Image
        image_path = call_runway_gen4_image_api(prompt, reference_images)
        
        if not image_path:
            print("Runway API failed, creating placeholder...")
            placeholder_text = f"Scene {scene_id}\n{scene.get('short description', 'No description')}"
            image_path = create_placeholder_image(placeholder_text)
        
        # Save image
        image_filename = f"main_illustration_{scene_id}_runway.png"
        final_image_path = os.path.join(OUTPUT_DIR, image_filename)
        save_image(image_path, final_image_path)
        
        # Clean up temp file
        if os.path.exists(image_path) and image_path != final_image_path:
            os.remove(image_path)
        
        # Add to previous illustrations for potential style consistency
        if os.path.exists(final_image_path):
            previous_illustrations.append(final_image_path)
        
        # Store results
        scene['main_illustration_path'] = final_image_path
        scene['main_illustration_prompt'] = prompt
        output_scenes.append(scene)
        
        print(f"✓ Generated: {final_image_path}")
    
    # Save output
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_scenes, f, ensure_ascii=False, indent=2)
    
    # Save the prompts for reference
    prompts_file = os.path.join(OUTPUT_DIR, 'api_prompts_runway.txt')
    with open(prompts_file, 'w', encoding='utf-8') as f:
        f.write("Prompts sent to Runway Gen-4 Image API:\n")
        f.write("=" * 50 + "\n\n")
        for i, scene in enumerate(output_scenes, 1):
            f.write(f"Scene {i} (ID: {scene.get('sequence_id', '?')}):\n")
            f.write("-" * 30 + "\n")
            f.write(scene.get('main_illustration_prompt', 'No prompt found'))
            f.write("\n\n")
    
    print(f"\n=== Generation Complete ===")
    print(f"Output saved to: {OUTPUT_JSON_PATH}")
    print(f"Prompts saved to: {prompts_file}")
    print(f"Images saved in: {OUTPUT_DIR}")
    
    if not RUNWAY_AVAILABLE:
        print("\n⚠️ Note: RunwayML SDK not available, placeholder images were generated.")
        print("To use the full Runway API, install the SDK: pip install runwayml")

if __name__ == "__main__":
    main()
