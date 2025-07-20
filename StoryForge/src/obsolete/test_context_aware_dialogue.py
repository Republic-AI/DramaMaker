#!/usr/bin/env python3
"""
Test Context-Aware Dialogue Generation
Demonstrates how the new dialogue generator uses JSON illustration data for context
"""

import os
import json
from korean_manga_dialogue_generator import KoreanMangaDialogueGenerator, SceneContext

def test_context_aware_dialogue():
    """Test the context-aware dialogue generation with JSON illustration data"""
    
    # Load existing illustration data
    output_dir = os.path.join(os.path.dirname(__file__), '../../output')
    illustrations_path = os.path.join(output_dir, 'main_illustrations_output_runway.json')
    
    try:
        with open(illustrations_path, 'r', encoding='utf-8') as f:
            illustrations_data = json.load(f)
        print(f"Loaded {len(illustrations_data)} illustrations from JSON")
    except FileNotFoundError:
        print(f"No illustration data found at {illustrations_path}")
        return
    
    # Initialize dialogue generator
    generator = KoreanMangaDialogueGenerator()
    
    print("\n" + "="*60)
    print("TESTING CONTEXT-AWARE DIALOGUE GENERATION")
    print("="*60)
    
    # Test each scene with its illustration context
    for i, illustration in enumerate(illustrations_data):
        scene_id = illustration.get('sequence_id', i + 1)
        
        print(f"\n--- Scene {scene_id} ---")
        print(f"Action: {illustration.get('action', 'N/A')}")
        print(f"Object: {illustration.get('object', 'N/A')}")
        print(f"Description: {illustration.get('short_description', 'N/A')}")
        print(f"Scene Position: {illustration.get('scene_position', 'N/A')}")
        
        # Create scene context from illustration data
        scene_context = SceneContext(
            scene_id=scene_id,
            description=illustration.get('short_description', ''),
            characters=[illustration.get('character(s) present', 'Character')],
            action=illustration.get('action', ''),
            object=illustration.get('object', ''),
            location='room',  # From the story context
            time='morning' if scene_id == 1 else 'afternoon',
            scene_position=illustration.get('scene_position', 'middle')
        )
        
        # Generate context-aware dialogue
        dialogue_data = generator.generate_context_aware_dialogue(scene_context)
        
        print("\nGenerated Dialogue:")
        print(f"Scene Description: {dialogue_data.get('scene_description', 'N/A')}")
        print(f"Scene Mood: {dialogue_data.get('scene_mood', 'N/A')}")
        print(f"Character Development: {dialogue_data.get('character_development', 'N/A')}")
        
        print("\nDialogue:")
        for dialogue in dialogue_data.get('dialogue', []):
            char = dialogue.get('character', 'Character')
            text = dialogue.get('text', '')
            emotion = dialogue.get('emotion', '')
            print(f"  {char} ({emotion}): {text}")
        
        print(f"\nNarration: {dialogue_data.get('narration', 'N/A')}")
        print("-" * 40)
    
    # Test with story progression context
    print("\n" + "="*60)
    print("TESTING WITH STORY PROGRESSION CONTEXT")
    print("="*60)
    
    # Create a sequence of scenes to show progression
    previous_scenes = [
        {
            "description": "Ryan tries to cook but struggles with the recipe",
            "action": "cook",
            "scene_position": "beginning"
        },
        {
            "description": "Ryan gets frustrated with cooking and decides to take a break",
            "action": "frustrated",
            "scene_position": "middle"
        }
    ]
    
    # Test final scene with progression context
    final_scene_context = SceneContext(
        scene_id=3,
        description="Ryan sits down to read a book to calm down",
        characters=["Ryan"],
        action="read",
        object="desk with books",
        location="room",
        time="evening",
        scene_position="end",
        previous_scenes=previous_scenes
    )
    
    print("\nFinal Scene with Story Progression:")
    print("Previous scenes context provided for emotional continuity")
    
    final_dialogue = generator.generate_context_aware_dialogue(final_scene_context)
    
    print(f"\nScene Description: {final_dialogue.get('scene_description', 'N/A')}")
    print(f"Scene Mood: {final_dialogue.get('scene_mood', 'N/A')}")
    print(f"Character Development: {final_dialogue.get('character_development', 'N/A')}")
    
    print("\nDialogue:")
    for dialogue in final_dialogue.get('dialogue', []):
        char = dialogue.get('character', 'Character')
        text = dialogue.get('text', '')
        emotion = dialogue.get('emotion', '')
        print(f"  {char} ({emotion}): {text}")
    
    print(f"\nNarration: {final_dialogue.get('narration', 'N/A')}")

def test_emotion_generation():
    """Test character emotion generation based on scene context"""
    
    print("\n" + "="*60)
    print("TESTING CHARACTER EMOTION GENERATION")
    print("="*60)
    
    generator = KoreanMangaDialogueGenerator()
    
    # Test different scene contexts
    test_scenes = [
        SceneContext(
            scene_id=1,
            description="Ryan tries to cook a meal but struggles",
            characters=["Ryan"],
            action="cook",
            object="stove",
            location="kitchen",
            time="morning",
            scene_position="beginning"
        ),
        SceneContext(
            scene_id=2,
            description="Ryan gets frustrated with cooking",
            characters=["Ryan"],
            action="frustrated",
            object="stove",
            location="kitchen",
            time="morning",
            scene_position="middle"
        ),
        SceneContext(
            scene_id=3,
            description="Ryan reads a book to calm down",
            characters=["Ryan"],
            action="read",
            object="book",
            location="room",
            time="afternoon",
            scene_position="end"
        )
    ]
    
    for i, scene_context in enumerate(test_scenes):
        emotions = generator.generate_character_emotions(scene_context)
        print(f"\nScene {i+1} - {scene_context.action}:")
        for char, emotion in emotions.items():
            print(f"  {char}: {emotion}")

if __name__ == "__main__":
    test_context_aware_dialogue()
    test_emotion_generation() 