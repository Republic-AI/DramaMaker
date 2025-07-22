import os
import json
import tempfile
from PIL import Image, ImageDraw, ImageFont
import requests
import base64
import mimetypes
import openai
import logging
import time
from config import OPENAI_API_KEY

# API Keys (direct configuration)
# OPENAI_API_KEY should be set via environment variable or config for security
OPENAI_API_KEY = OPENAI_API_KEY
# Paths
BASE_DIR = os.path.dirname(__file__)
MANGA_SAMPLE_DIR = os.path.join(BASE_DIR, '../manga_sample')
OUTPUT_DIR = os.path.join(BASE_DIR, '../output')
SEGMENTED_SCENES_PATH = os.path.join(OUTPUT_DIR, 'segmented_scenes_illustration.json')

# Frame templates and character reference
FRAME_TEMPLATE_1 = os.path.join(MANGA_SAMPLE_DIR, 'frame_template1.png')
FRAME_TEMPLATE_2 = os.path.join(MANGA_SAMPLE_DIR, 'frame_template2.png')
RYAN_AVATAR = os.path.join(MANGA_SAMPLE_DIR, 'ryan_avatar.png')
SAMPLE_MANGA_STYLE = os.path.join(MANGA_SAMPLE_DIR, 'sample_manga_style.jpg')

def load_segmented_scenes():
    """Load the segmented scenes with illustrations"""
    try:
        print(f"Loading segmented scenes from: {SEGMENTED_SCENES_PATH}")
        with open(SEGMENTED_SCENES_PATH, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
        print(f"Loaded {len(scenes)} scenes")
        
        # Sort scenes by sequence_id to ensure proper order
        scenes.sort(key=lambda x: x.get('sequence_id', 0))
        
        # Print story continuity information
        if scenes:
            print("\n=== Story Continuity Information ===")
            full_story = scenes[0].get('full_story', '')
            print(f"Full Story: {full_story}")
            print("\nScene Order:")
            for scene in scenes:
                scene_id = scene.get('sequence_id', '?')
                position = scene.get('scene_position', 'unknown')
                desc = scene.get('short description', 'No description')
                print(f"  Scene {scene_id} ({position}): {desc}")
            print()
        
        return scenes
    except FileNotFoundError:
        print(f"Error: Could not find {SEGMENTED_SCENES_PATH}")
        print("Please run illustration_gen_runway.py first to generate the segmented scenes with illustrations")
        return None
    except Exception as e:
        print(f"Error loading scenes: {e}")
        return None

def create_placeholder_image(text="Placeholder"):
    """Create a placeholder image when API is not available"""
    print(f"Creating placeholder image with text: {text}")
    img = Image.new('RGB', (1024, 1024), color='#E3F2FD')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
    
    lines = text.split('\n')
    y_offset = 400
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1024 - text_width) // 2
        draw.text((x, y_offset), line, fill='#1976D2', font=font)
        y_offset += 60
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    temp_file.close()
    
    print(f"Placeholder image created: {temp_file.name}")
    return temp_file.name

def generate_panel_analysis(scene, frame_template_path, output_path):
    """Generate a professional, coherent manga panel analysis (分镜分析) as JSON and save as intermediate output, using both story and illustration content. Includes logging and timing."""
    import base64
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    scene_desc = scene.get('short description', '')
    scene_mood = scene.get('scene_mood', '')
    dialogue_lines = scene.get('dialogue', [])
    narration = scene.get('narration', '')
    full_story = scene.get('full_story', '')
    scene_position = scene.get('scene_position', '')
    dialogue_text = ""
    if dialogue_lines:
        dialogue_text = " ".join([f"{d.get('character', '')}: {d.get('text', '')}" for d in dialogue_lines])

    # Vision: get illustration description if available
    illustration_path = scene.get('main_illustration_path', '')
    illustration_desc = ""
    if illustration_path and os.path.exists(illustration_path):
        print("\n[分镜分析] Generating vision-based description of the main illustration...")
        with open(illustration_path, "rb") as img_file:
            vision_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": "Please briefly describe the content, characters, actions, atmosphere, and setting of this illustration in English."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"}}
                    ]}
                ],
                max_tokens=256
            )
            illustration_desc = vision_response.choices[0].message.content.strip()
        print(f"[Illustration description]: {illustration_desc}")

    analysis_prompt = f"""
You are a professional manga storyboard artist. Carefully read the following story context and illustration details, and output a high‑quality storyboard analysis in JSON format.

For each panel, provide the following information:
- description: main content of the panel
- composition: camera composition (wide shot / medium shot / close-up, top view / low angle, arrangement of foreground / midground / background)
- is_key_panel: whether this panel is the key panel on the page
- panel_function: setup / climax / transition
- characters: characters appearing in this panel
- actions: specific actions performed by each character
- emotion: emotional atmosphere
- dialogue: lines spoken in this panel (if any)
- narration: narration text in this panel (if any)
- visual_guidance: how the reader’s eye should flow through this panel

In addition, add a field at the top level of the JSON:
- `recommended_pages`: an integer indicating how many manga pages are recommended to represent this part of the story
- `recommended_pages_reason`: a brief explanation for the recommended number of pages

Output format example:
{
  "recommended_pages": 1,
  "recommended_pages_reason": "The scene is short and can be expressed in three panels on a single page.",
  "panels": [
    {
      "description": "...",
      "composition": "...",
      "is_key_panel": true,
      "panel_function": "climax",
      "characters": ["Ryan"],
      "actions": "...",
      "emotion": "...",
      "dialogue": ["..."],
      "narration": "...",
      "visual_guidance": "..."
    }
  ]
}

Story background: {full_story}
Scene position: {scene_position}
Scene description: {scene_desc}
Emotional atmosphere: {scene_mood}
Dialogue: {dialogue_text}
Narration: {narration}
Illustration description: {illustration_desc}

Output JSON only. Do not output any additional text.
"""
    print("\n[分镜分析 Prompt]:\n" + analysis_prompt)
    print("[分镜分析] Starting panel analysis generation with OpenAI...")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1200
        )
        elapsed = time.time() - start_time
        print(f"[分镜分析] Panel analysis generated in {elapsed:.2f}s.")
        analysis_json = response.choices[0].message.content.strip()
        analysis_path = output_path.replace('.png', '_openai_analysis.txt')
        with open(analysis_path, 'w', encoding='utf-8') as f:
            f.write(analysis_json)
        print(f"[分镜分析已保存]: {analysis_path}")
        return analysis_json
    except Exception as e:
        print(f"[分镜分析] Error during panel analysis generation: {e}")
        import traceback
        traceback.print_exc()
        return None

def call_gpt_image_1_with_references(scene, frame_template_path, output_path):
    """Use OpenAI gpt-image-1 to generate manga page with illustration and frame template as input images, including analysis as JSON if available. Includes logging, timeout, and retries."""
    import base64
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Generate 分镜分析 if not already present
    analysis_path = output_path.replace('.png', '_openai_analysis.txt')
    if not os.path.exists(analysis_path):
        generate_panel_analysis(scene, frame_template_path, output_path)

    # Prepare prompt
    scene_desc = scene.get('short description', '')
    scene_mood = scene.get('scene_mood', '')
    dialogue_lines = scene.get('dialogue', [])
    narration = scene.get('narration', '')
    full_story = scene.get('full_story', '')
    scene_position = scene.get('scene_position', '')
    dialogue_text = ""
    if dialogue_lines:
        dialogue_text = "\n".join([f"{d.get('character', '')}: {d.get('text', '')}" for d in dialogue_lines])

    openai_analysis = None
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r', encoding='utf-8') as f:
            openai_analysis = f.read().strip()

    prompt = f"""
You are a professional manga layout artist. 
Generate a high-quality manga page following ALL the rules below. 
**Strictly follow every requirement. Do not ignore any instruction.**

===== INPUTS =====
• First reference image: the main full-scene illustration. 
• Second reference image: ONLY for panel layout reference (NOT for content).
• Texts: Scene description, narration, and dialogue provided below.

===== LAYOUT RULES =====
Canvas ratio: 3:4 vertical format.  
Margins: 0.9 cm pure white margin around the whole canvas.  
Gutters: 0.5 cm pure white spacing between all panels.  
Color of margins and gutters: pure white.

Use a dynamic comic panel layout with:
- ONE large main panel (must closely replicate the composition and content of the first reference image).
- TWO or THREE smaller panels arranged diagonally or overlapping.
- Each smaller panel must zoom in on a distinct detail of the large scene:
    • e.g. a character’s face, a hand holding something, or a background item.
    • Do NOT repeat the same focus twice.
    • If there are multiple characters, different small panels can focus on different characters.

Follow the layout style of the second reference image (for panel arrangement only).

===== ART STYLE =====
Soft anime style, clean line art, dramatic composition.  
Visual style must match “Light and Night”, “Mr Love: Queen’s Choice”, and Korean romance webtoons.  
Appealing to a young female audience:
- 8-head-body proportions.
- Delicate facial features, smooth glowing skin.
- Soft refined highlights and reflections to show depth.
- Character appearance and clothing MUST match the first reference image.

===== TEXT REQUIREMENTS =====
All dialogue and narration must match the given text below exactly.  
Each line appears once, no duplication, no missing lines.  
Ensure each line is assigned to the correct character.  
Place dialogue and narration in speech bubbles:
- Font: serif
- Size: 23

===== OUTPUT =====
Output a final manga page image with the above layout and style, integrating the dialogue and narration exactly.

===== TEXTS =====
Scene description: {scene_desc}
Narration: {narration}
Dialogue:
{dialogue_text}
"""
    print("\n[漫画生成 Prompt]:\n" + prompt)

    illustration_path = scene.get('main_illustration_path', '')
    if not (illustration_path and os.path.exists(illustration_path)):
        print("No main illustration found, cannot use gpt-image-1 edit API.")
        return None
    if not (frame_template_path and os.path.exists(frame_template_path)):
        print("No frame template found, cannot use gpt-image-1 edit API.")
        return None

    max_retries = 3
    timeout = 120  # seconds
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n=== CALLING OPENAI gpt-image-1 EDIT FOR MANGA GENERATION (Attempt {attempt}) ===")
            start_time = time.time()
            with open(illustration_path, "rb") as img1, open(frame_template_path, "rb") as img2:
                result = client.images.edit(
                    model="gpt-image-1",
                    image=[img1, img2],
                    prompt=prompt,
                    input_fidelity="high",
                    n=1,
                    size="1024x1536",
                    quality="high",
                    timeout=timeout
                )
            elapsed = time.time() - start_time
            print(f"✓ gpt-image-1 manga page created in {elapsed:.2f}s: {output_path}")
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            return output_path
        except Exception as e:
            print(f"gpt-image-1 error (attempt {attempt}): {e}")
            if attempt < max_retries:
                print(f"Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                print("All retries failed. Giving up on this manga page.")
                import traceback
                traceback.print_exc()
                return None


def create_manga_page(scene, frame_template_path, output_path, use_openai=False, use_runway=False):
    """Create a complete manga page using frame template and scene data"""
    
    print(f"\n=== CREATING MANGA PAGE FOR SCENE {scene.get('sequence_id', '?')} ===")
    
    # Check if frame template exists
    if not os.path.exists(frame_template_path):
        print(f"Error: Frame template not found: {frame_template_path}")
        return None
    
    # Get existing illustration path
    existing_illustration = scene.get('main_illustration_path', '')
    
    # Use gpt-image-1 if illustration exists
    if existing_illustration and os.path.exists(existing_illustration):
        result = call_gpt_image_1_with_references(scene, frame_template_path, output_path)
        if result:
            print(f"✓ Manga page created: {result}")
            return result
        else:
            print("gpt-image-1 failed, falling back to simple composition...")
    
    # Fallback: simple composition
    result = create_simple_manga_page(scene, frame_template_path, output_path)
    
    if result:
        print(f"✓ Manga page created: {result}")
        return result
    
    return None

def create_simple_manga_page(scene, frame_template_path, output_path):
    """Create a simple manga page by compositing existing illustration with frame template"""
    
    print(f"\n=== CREATING SIMPLE MANGA PAGE FOR SCENE {scene.get('sequence_id', '?')} ===")
    
    try:
        # Load frame template
        if not os.path.exists(frame_template_path):
            print(f"Error: Frame template not found: {frame_template_path}")
            return None
        
        frame_template = Image.open(frame_template_path)
        print(f"Loaded frame template: {frame_template.size}")
        
        # Load existing illustration if available
        existing_illustration = scene.get('main_illustration_path', '')
        if existing_illustration and os.path.exists(existing_illustration):
            print(f"Using existing illustration: {existing_illustration}")
            illustration = Image.open(existing_illustration)
            
            # Create a new image with frame template as background
            manga_page = frame_template.copy()
            
            # Calculate panel areas based on frame template
            # Assuming the frame template has transparent areas for panels
            # We'll try to detect panel areas or use predefined positions
            
            # For now, let's use a simple approach: resize illustration to fit in the main area
            # Calculate available space (assuming 10% margin on each side)
            margin = int(manga_page.width * 0.1)
            available_width = manga_page.width - (2 * margin)
            available_height = manga_page.height - (2 * margin)
            
            # Resize illustration to fit in available space
            illustration = illustration.resize((available_width, available_height), Image.Resampling.LANCZOS)
            
            # Position illustration in the center
            x = margin
            y = margin
            
            # Paste illustration onto the frame
            manga_page.paste(illustration, (x, y))
            
            # Add dialogue and narration text
            draw = ImageDraw.Draw(manga_page)
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
            
            # Add dialogue text in speech bubbles
            dialogue_lines = scene.get('dialogue', [])
            if dialogue_lines:
                y_offset = manga_page.height - 150
                for dialogue in dialogue_lines:
                    text = f"{dialogue.get('character', '')}: {dialogue.get('text', '')}"
                    # Draw a simple speech bubble background
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # Draw speech bubble
                    bubble_x = 50
                    bubble_y = y_offset
                    bubble_width = text_width + 20
                    bubble_height = text_height + 10
                    
                    # Draw white background for speech bubble
                    draw.rectangle([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                 fill='white', outline='black', width=2)
                    
                    # Draw text
                    draw.text((bubble_x + 10, bubble_y + 5), text, fill='black', font=font)
                    y_offset += bubble_height + 10
            
            # Add narration text
            narration = scene.get('narration', '')
            if narration:
                # Draw narration box at the top
                draw.rectangle([50, 50, manga_page.width - 50, 100], fill='white', outline='black', width=2)
                draw.text((60, 60), narration, fill='black', font=font)
            
            # Save the manga page
            manga_page.save(output_path)
            print(f"✓ Simple manga page created: {output_path}")
            return output_path
            
        else:
            print("No existing illustration found, creating placeholder")
            placeholder_text = f"Scene {scene.get('sequence_id', '?')}\n{scene.get('short description', 'No description')}"
            return create_placeholder_image(placeholder_text)
            
    except Exception as e:
        print(f"Error creating simple manga page: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Generate complete manga pages from segmented scenes"""
    
    print("=== Manga Page Generator ===")
    print(f"OpenAI API Key: {'✓ Configured' if OPENAI_API_KEY and OPENAI_API_KEY != 'your_openai_api_key_here' else '✗ Not configured'}")
    print()
    
    # Load segmented scenes
    scenes = load_segmented_scenes()
    if not scenes:
        return
    
    # Create output directory for manga pages
    manga_pages_dir = os.path.join(OUTPUT_DIR, 'manga_pages')
    os.makedirs(manga_pages_dir, exist_ok=True)
    
    # Automatically use OpenAI analysis for manga generation
    use_openai = True
    print("Automatically using OpenAI 4o for layout analysis and gpt-image-1 for manga generation")
    
    # Process each scene
    for i, scene in enumerate(scenes):
        scene_id = scene.get('sequence_id', i + 1)
        print(f"\n--- Processing Scene {scene_id} ---")
        
        # Choose frame template (alternate between templates)
        frame_template = FRAME_TEMPLATE_1 if i % 2 == 0 else FRAME_TEMPLATE_2
        
        # Output path for manga page
        manga_page_filename = f"manga_page_{scene_id}.png"
        manga_page_path = os.path.join(manga_pages_dir, manga_page_filename)
        
        # Create manga page
        result = create_manga_page(scene, frame_template, manga_page_path, use_openai=use_openai)
        
        if result:
            print(f"✓ Successfully created manga page: {result}")
        else:
            print(f"✗ Failed to create manga page for scene {scene_id}")
    
    print(f"\n=== Generation Complete ===")
    print(f"Manga pages saved in: {manga_pages_dir}")
    
    if use_openai:
        print("\n✓ OpenAI 4o analysis completed. Check the generated .txt files for layout guidance.")

if __name__ == "__main__":
    main() 