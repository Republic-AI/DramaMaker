import os
import json
import tempfile
from PIL import Image, ImageDraw, ImageFont
import requests
import base64
import mimetypes
import openai

# API Keys (direct configuration)
OPENAI_API_KEY = "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"
RUNWAY_API_KEY = "key_536cfd03902f0448624e34cddf7be4cfaf04ca75f5920ac5098fef3fd158cb1deb1cf1e4fef7e73c6f18faf74b3c0c1b218af61a607c1b0813c3039dda886330"

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

def get_image_as_data_uri(image_path):
    """Convert local image to data URI for API calls"""
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

def check_character_consistency(scenes):
    """Check character consistency across scenes"""
    print("\n=== Character Consistency Check ===")
    
    character_refs = {}
    for scene in scenes:
        scene_id = scene.get('sequence_id', '?')
        characters = scene.get('character(s) present', '')
        illustration_path = scene.get('main_illustration_path', '')
        
        if characters and illustration_path:
            if characters not in character_refs:
                character_refs[characters] = {
                    'first_scene': scene_id,
                    'illustration_path': illustration_path,
                    'appearances': []
                }
            
            character_refs[characters]['appearances'].append({
                'scene_id': scene_id,
                'description': scene.get('short description', ''),
                'mood': scene.get('scene_mood', ''),
                'illustration_path': illustration_path
            })
    
    # Print consistency report
    for character, info in character_refs.items():
        print(f"\nCharacter: {character}")
        print(f"  First appearance: Scene {info['first_scene']}")
        print(f"  Total appearances: {len(info['appearances'])}")
        print(f"  Reference illustration: {info['illustration_path']}")
        
        for appearance in info['appearances']:
            print(f"    Scene {appearance['scene_id']}: {appearance['description']} ({appearance['mood']})")
    
    return character_refs

def call_openai_4o_vision_api(scene, illustration_path, frame_template_path):
    """Use OpenAI 4o Vision API to create manga panel layout"""
    
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        print("OpenAI API key not configured")
        return None
    
    try:
        print("\n=== CALLING OPENAI 4O VISION API ===")
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Prepare the prompt for OpenAI
        scene_desc = scene.get('short description', '')
        scene_mood = scene.get('scene_mood', '')
        dialogue_lines = scene.get('dialogue', [])
        narration = scene.get('narration', '')
        full_story = scene.get('full_story', '')
        scene_position = scene.get('scene_position', '')
        
        # Extract dialogue text
        dialogue_text = ""
        if dialogue_lines:
            dialogue_text = " ".join([f"{d.get('character', '')}: {d.get('text', '')}" for d in dialogue_lines])
        
        prompt = f"""
Generate the comics based on the first reference image and use this layout:

CRITICAL CHARACTER CONSISTENCY: The first reference image contains the EXACT character design that must be used throughout the manga. Every visual detail of the character - face shape, eye style, hair color and style, clothing, body proportions, skin tone, and facial features - must be IDENTICAL to the reference image. Do not modify, stylize, or change any aspect of the character's appearance.

Story Context:
Full Story: {full_story}
Scene Position: {scene_position}
This scene is part of a larger narrative. Ensure the visual storytelling flows naturally and maintains narrative continuity.

Layout Reference:
Use a dynamic comic panel layout with one large main panel and 2-3 smaller panels arranged diagonally or overlapping.
The large panel should use the first reference image as the main scene - this illustration IS the content that goes into the manga.
The smaller panels must zoom in on distinct localized details from the main illustration — such as a character's expression, hand movement, or a specific environmental object.
Each smaller panel must focus on a different part of the main illustration. Do not repeat the same content across multiple small panels.
Use the panel layout style from the second and the third reference images. These two reference images are for layout reference only! Do not use the content of them.

Canvas Ratio: 3:4 vertical format 
Margins: 0.9 cm pure white margin around the whole 3:4 ratio canvas!
Gutters: 0.5 cm pure white spacing between all panels
Notice: Color of the margins and gutters must be pure white.

Art style:
Art style must remain consistent—soft anime style, clean line art, dramatic composition. 
Refer to visual styles from Light and Night, Mr Love: Queen's Choice, and Korean romance webtoons, and should be conforms to the aesthetic standards of young women.
The linework must be clear and visible. The design should be appealing to a young female audience.

Character Consistency Rules:
1. Copy the EXACT character design from the first reference image
2. Maintain identical facial features, hair style, and clothing
3. Keep the same skin tone and body proportions
4. Preserve all visual details including accessories and clothing patterns
5. Do not stylize or modify the character's appearance in any way

Dialogue and Narration:
The dialogue and narration must exactly match the text provided below. Make sure the correct character speaks the correct words.
Do not make any errors or swap the lines between characters. 
Please must place narration and dialogue inside speech bubbles. Use a serif font, size 23. 。

Scene: {scene_desc}
Mood: {scene_mood}
Dialogue: {dialogue_text}
Narration: {narration}
"""
        
        # Prepare images for OpenAI Vision API
        images = []
        
        # Add illustration (first reference - main content)
        if os.path.exists(illustration_path):
            with open(illustration_path, "rb") as f:
                images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
                    }
                })
        
        # Add frame template (second reference - layout)
        if os.path.exists(frame_template_path):
            with open(frame_template_path, "rb") as f:
                images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
                    }
                })
        
        # Add sample manga style (third reference - style)
        if os.path.exists(SAMPLE_MANGA_STYLE):
            with open(SAMPLE_MANGA_STYLE, "rb") as f:
                images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
                    }
                })
        
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Images: {len(images)}")
        
        # Call OpenAI 4o Vision API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ] + images
                }
            ],
            max_tokens=2000
        )
        
        print("OpenAI 4o Vision API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        
        # For now, return the response text
        # In a full implementation, you might want to parse this response
        # and use it to guide the image generation or layout creation
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI 4o Vision API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def call_dalle3_with_analysis(scene, openai_analysis, output_path):
    """Use DALL-E 3 to generate manga page based on OpenAI analysis"""
    
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        print("OpenAI API key not configured")
        return None
    
    try:
        print("\n=== CALLING DALL-E 3 FOR MANGA GENERATION ===")
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Create DALL-E 3 prompt based on OpenAI analysis
        scene_desc = scene.get('short description', '')
        scene_mood = scene.get('scene_mood', '')
        dialogue_lines = scene.get('dialogue', [])
        narration = scene.get('narration', '')
        
        # Extract dialogue text
        dialogue_text = ""
        if dialogue_lines:
            dialogue_text = " ".join([f"{d.get('character', '')}: {d.get('text', '')}" for d in dialogue_lines])
        
        # Create a more focused DALL-E 3 prompt based on the analysis
        scene_desc = scene.get('short description', '')
        scene_mood = scene.get('scene_mood', '')
        dialogue_lines = scene.get('dialogue', [])
        narration = scene.get('narration', '')
        full_story = scene.get('full_story', '')
        scene_position = scene.get('scene_position', '')
        
        # Extract dialogue text
        dialogue_text = ""
        if dialogue_lines:
            dialogue_text = " ".join([f"{d.get('character', '')}: {d.get('text', '')}" for d in dialogue_lines])
        
        dalle_prompt = f"""
Create a Korean romance manga page based on this detailed analysis:

{openai_analysis}

IMPORTANT: The first reference image is the MAIN ILLUSTRATION that will be used in the manga. Character's appearance, clothing, pose, and all visual details must EXACTLY match the illustration.

Story Context:
Full Story: {full_story}
Scene Position: {scene_position}
This scene is part of a larger narrative. Ensure the visual storytelling flows naturally and maintains narrative continuity.

Key Requirements:
- Follow the exact panel layout described in the analysis
- Use the specific details mentioned for each panel
- The main panel should use the first reference image as the main scene - this illustration IS the content that goes into the manga
- Character appearance, including clothing, pose, and all visual details must EXACTLY match the first reference image
- Maintain the 3:4 vertical format with proper margins and gutters
- Apply the Korean romance webtoon aesthetic
- Include all dialogue and narration in speech bubbles with serif font
- Ensure narrative continuity and visual storytelling flow

Scene: {scene_desc}
Mood: {scene_mood}
Dialogue: {dialogue_text}
Narration: {narration}

Style: Soft anime style, clean line art, dramatic composition, appealing to young women.
"""
        
        print(f"DALL-E 3 prompt length: {len(dalle_prompt)} characters")
        print("DALL-E 3 prompt preview (first 300 chars):", dalle_prompt[:300] + "..." if len(dalle_prompt) > 300 else dalle_prompt)
        
        # Call DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        print("DALL-E 3 generation successful!")
        
        # Download the generated image
        image_url = response.data[0].url
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            # Save the image
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            print(f"✓ DALL-E 3 manga page created: {output_path}")
            return output_path
        else:
            print(f"Failed to download DALL-E 3 image: {img_response.status_code}")
            return None
            
    except Exception as e:
        print(f"DALL-E 3 error: {e}")
        import traceback
        traceback.print_exc()
        return None

def call_runway_with_openai_analysis(scene, openai_analysis, output_path):
    """Use Runway Gen-4 with OpenAI 4o analysis as guidance"""
    
    # Extract key information from OpenAI analysis
    scene_desc = scene.get('short description', '')
    scene_mood = scene.get('scene_mood', '')
    dialogue_lines = scene.get('dialogue', [])
    narration = scene.get('narration', '')
    full_story = scene.get('full_story', '')
    scene_position = scene.get('scene_position', '')
    
    # Extract dialogue text
    dialogue_text = ""
    if dialogue_lines:
        dialogue_text = " ".join([f"{d.get('character', '')}: {d.get('text', '')}" for d in dialogue_lines])
    
    # Create a simplified Runway prompt based on OpenAI analysis
    runway_prompt = f"""
Korean romance manga page, 3:4 vertical format, soft anime style, clean line art.

Scene: {scene_desc}
Mood: {scene_mood}

Character: Young male with gentle features, soft expression, emotional depth.

Style: Korean romance webtoon aesthetic, appealing to young women, soft pastel colors, elegant line art.

Dialogue: {dialogue_text}

Layout: Dynamic comic panel layout with one large main panel and 2-3 smaller panels arranged diagonally or overlapping.
"""
    
    if not RUNWAY_API_KEY:
        print("Runway API key not configured")
        return None
    
    try:
        print("\n=== CALLING RUNWAY WITH OPENAI ANALYSIS ===")
        
        print(f"Runway prompt length: {len(runway_prompt)} characters")
        print("Runway prompt preview (first 300 chars):", runway_prompt[:300] + "..." if len(runway_prompt) > 300 else runway_prompt)
        
        # Use Runway SDK
        from runwayml import RunwayML, TaskFailedError
        
        # Set API key as environment variable
        import os
        os.environ['RUNWAYML_API_SECRET'] = RUNWAY_API_KEY
        
        client = RunwayML()
        
        # Get reference illustration
        illustration_path = scene.get('main_illustration_path', '')
        reference_images = []
        
        if illustration_path and os.path.exists(illustration_path):
            # Convert illustration to data URI
            with open(illustration_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")
            content_type = mimetypes.guess_type(illustration_path)[0] or "image/png"
            data_uri = f"data:{content_type};base64,{base64_image}"
            
            reference_images.append({
                'uri': data_uri,
                'tag': 'character'
            })
        
        # Create Runway task
        try:
            task = client.text_to_image.create(
                model='gen4_image',
                ratio='1080:1440',  # 3:4 aspect ratio
                prompt_text=runway_prompt,
                reference_images=reference_images
            ).wait_for_task_output()
            
            print('✓ Runway task completed successfully!')
            print('Image URL:', task.output[0])
            
            # Download the generated image
            import requests
            img_response = requests.get(task.output[0], timeout=60)
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"✓ Runway manga page created: {output_path}")
                return output_path
            else:
                print(f"Failed to download image: {img_response.status_code}")
                return None
                
        except TaskFailedError as e:
            print('The image failed to generate.')
            print(e.task_details)
            return None
            
    except Exception as e:
        print(f"Runway with OpenAI analysis error: {e}")
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
    
    if use_openai and existing_illustration and os.path.exists(existing_illustration):
        print("Using OpenAI 4o Vision API for layout analysis...")
        openai_response = call_openai_4o_vision_api(scene, existing_illustration, frame_template_path)
        
        if openai_response:
            print("OpenAI 4o analysis completed.")
            # Save OpenAI response for reference
            response_file = output_path.replace('.png', '_openai_analysis.txt')
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(openai_response)
            print(f"OpenAI analysis saved to: {response_file}")
            
            # Use Runway with OpenAI analysis if requested
            if use_runway:
                print("Using Runway with OpenAI analysis to generate manga page...")
                runway_result = call_runway_with_openai_analysis(scene, openai_response, output_path)
                if runway_result:
                    print(f"✓ Runway manga page created: {output_path}")
                    return output_path
                else:
                    print("Runway failed, falling back to simple composition...")
    
    # Use simple composition method as fallback
    result = create_simple_manga_page(scene, frame_template_path, output_path)
    
    if result:
        print(f"✓ Manga page created: {output_path}")
        return output_path
    
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
    
    # Check character consistency
    character_refs = check_character_consistency(scenes)
    
    # Create output directory for manga pages
    manga_pages_dir = os.path.join(OUTPUT_DIR, 'manga_pages')
    os.makedirs(manga_pages_dir, exist_ok=True)
    
    # Automatically use OpenAI analysis and Runway generation
    use_openai = True
    use_runway = True
    print("Automatically using OpenAI 4o for layout analysis and Runway for manga generation")
    
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
        result = create_manga_page(scene, frame_template, manga_page_path, use_openai=use_openai, use_runway=use_runway)
        
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