#!/usr/bin/env python3
"""
Korean Manga Dialogue Generator
Generates context-aware dialogue and narration for Korean romance manga
Uses AI to create natural, emotional dialogue based on scene context
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import anthropic
from dataclasses import dataclass

@dataclass
class SceneContext:
    """Context information for dialogue generation"""
    scene_id: int
    description: str
    characters: List[str]
    action: str
    object: str
    location: str
    time: str
    scene_position: str  # beginning, middle, end
    previous_scenes: Optional[List[Dict[str, Any]]] = None
    character_emotions: Optional[Dict[str, str]] = None

class KoreanMangaDialogueGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.client = None
    
    def generate_context_aware_dialogue(self, scene_context: SceneContext) -> Dict[str, Any]:
        """Generate context-aware dialogue and narration for Korean romance manga"""
        if not self.client:
            return self._generate_simple_dialogue(scene_context)
        
        try:
            prompt = self._build_context_prompt(scene_context)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = getattr(response.content[0], 'text', str(response.content[0])) if response.content else ""
            return self._extract_dialogue_from_response(content) or self._generate_simple_dialogue(scene_context)
            
        except Exception as e:
            print(f"Error generating AI dialogue: {e}")
            return self._generate_simple_dialogue(scene_context)
    
    def _build_context_prompt(self, scene_context: SceneContext) -> str:
        """Build a comprehensive prompt for context-aware dialogue generation"""
        
        # Build character context
        character_context = ""
        if scene_context.character_emotions:
            character_context = "\n".join([
                f"- {char}: {emotion}" for char, emotion in scene_context.character_emotions.items()
            ])
        
        # Build story progression context
        story_progression = ""
        if scene_context.previous_scenes:
            recent_scenes = scene_context.previous_scenes[-2:]  # Last 2 scenes
            story_progression = "\n".join([
                f"Previous scene {i+1}: {scene.get('description', '')}" 
                for i, scene in enumerate(recent_scenes)
            ])
        
        prompt = f"""Generate natural dialogue and narration for a Korean romance manga scene.

**Scene Context:**
Scene ID: {scene_context.scene_id}
Description: {scene_context.description}
Characters: {', '.join(scene_context.characters)}
Action: {scene_context.action}
Object: {scene_context.object}
Location: {scene_context.location}
Time: {scene_context.time}
Scene Position: {scene_context.scene_position}

**Character Emotions:**
{character_context}

**Story Progression:**
{story_progression}

**Requirements:**
1. Create emotional, romantic dialogue fitting Korean manga style
2. Consider the scene's position in the story (beginning/middle/end)
3. Reflect character emotions and story progression
4. Include both dialogue and narration
5. Make it natural and atmospheric

**Return as JSON:**
{{
  "scene_description": "Brief atmospheric scene description",
  "dialogue": [
    {{
      "character": "Character name",
      "text": "What they say",
      "emotion": "emotion being expressed"
    }}
  ],
  "narration": "Dreamy, atmospheric narration text",
  "scene_mood": "overall mood of the scene",
  "character_development": "how this scene develops the character"
}}

Make the dialogue emotional, romantic, and fitting for Korean romance manga with soft, dreamy atmosphere."""
        
        return prompt
    
    def _extract_dialogue_from_response(self, content: str) -> Dict[str, Any]:
        """Extract dialogue JSON from AI response"""
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {}
    
    def _generate_simple_dialogue(self, scene_context: SceneContext) -> Dict[str, Any]:
        """Generate simple dialogue when AI is not available"""
        action = scene_context.action.lower()
        characters = scene_context.characters
        main_char = characters[0] if characters else "Character"
        
        # Context-aware dialogue based on action and scene position
        if 'cook' in action:
            if scene_context.scene_position == 'beginning':
                return {
                    "scene_description": f"{main_char} stands determinedly in the kitchen, ready to tackle the challenge of cooking.",
                    "dialogue": [
                        {"character": main_char, "text": "I can do this... I just need to focus.", "emotion": "determined"},
                        {"character": main_char, "text": "Let me check the recipe one more time...", "emotion": "focused"}
                    ],
                    "narration": "The kitchen fills with the sweet aroma of possibility, though uncertainty lingers in the air.",
                    "scene_mood": "determined but uncertain",
                    "character_development": "Shows determination to overcome challenges"
                }
            else:
                return {
                    "scene_description": f"{main_char} struggles with the cooking, frustration building with each failed attempt.",
                    "dialogue": [
                        {"character": main_char, "text": "Why is this so difficult?", "emotion": "frustrated"},
                        {"character": main_char, "text": "I won't give up... I can't give up.", "emotion": "determined"}
                    ],
                    "narration": "The kitchen becomes a battlefield of determination against culinary chaos.",
                    "scene_mood": "frustrated but persistent",
                    "character_development": "Shows resilience in the face of failure"
                }
        
        elif 'read' in action:
            return {
                "scene_description": f"{main_char} finds solace in the pages of a book, seeking escape from the day's challenges.",
                "dialogue": [
                    {"character": main_char, "text": "This is exactly what I needed... a moment of peace.", "emotion": "relieved"},
                    {"character": main_char, "text": "Sometimes the best escape is between the pages of a good book.", "emotion": "content"}
                ],
                "narration": "A peaceful moment of reading provides comfort and escape from the world's chaos.",
                "scene_mood": "peaceful and reflective",
                "character_development": "Shows ability to find comfort in simple pleasures"
            }
        
        elif 'frustrated' in action or 'struggles' in action:
            return {
                "scene_description": f"{main_char} feels the weight of frustration but refuses to let it defeat them.",
                "dialogue": [
                    {"character": main_char, "text": "Why is everything so difficult today?", "emotion": "frustrated"},
                    {"character": main_char, "text": "I need to stay strong... I can't let this beat me.", "emotion": "determined"}
                ],
                "narration": "Despite the frustration, there's a spark of determination that refuses to be extinguished.",
                "scene_mood": "frustrated but resilient",
                "character_development": "Shows emotional strength and determination"
            }
        
        else:
            return {
                "scene_description": f"{main_char} is deep in thought, reflecting on the day's events and challenges.",
                "dialogue": [
                    {"character": main_char, "text": "I need to figure this out... everything will be okay.", "emotion": "thoughtful"},
                    {"character": main_char, "text": "Sometimes the hardest battles are the ones we fight within ourselves.", "emotion": "introspective"}
                ],
                "narration": "The moment stretches on as thoughts swirl through their mind like autumn leaves in the wind.",
                "scene_mood": "contemplative and introspective",
                "character_development": "Shows self-reflection and emotional maturity"
            }
    
    def generate_character_emotions(self, scene_context: SceneContext) -> Dict[str, str]:
        """Generate character emotions based on scene context"""
        if not self.client:
            return self._generate_simple_emotions(scene_context)
        
        try:
            prompt = f"""Analyze the scene context and determine the emotional state of each character.

Scene: {scene_context.description}
Action: {scene_context.action}
Scene Position: {scene_context.scene_position}
Characters: {', '.join(scene_context.characters)}

Return as JSON with character emotions:
{{
  "character_name": "emotion",
  "character_name2": "emotion2"
}}

Consider the story progression and scene context for realistic emotional states."""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = getattr(response.content[0], 'text', str(response.content[0])) if response.content else ""
            return self._extract_emotions_from_response(content) or self._generate_simple_emotions(scene_context)
            
        except Exception as e:
            print(f"Error generating emotions: {e}")
            return self._generate_simple_emotions(scene_context)
    
    def _extract_emotions_from_response(self, content: str) -> Dict[str, str]:
        """Extract emotions JSON from AI response"""
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {}
    
    def _generate_simple_emotions(self, scene_context: SceneContext) -> Dict[str, str]:
        """Generate simple emotions when AI is not available"""
        emotions = {}
        action = scene_context.action.lower()
        
        for char in scene_context.characters:
            if 'cook' in action:
                emotions[char] = "determined" if scene_context.scene_position == 'beginning' else "frustrated"
            elif 'read' in action:
                emotions[char] = "peaceful"
            elif 'frustrated' in action or 'struggles' in action:
                emotions[char] = "frustrated"
            else:
                emotions[char] = "thoughtful"
        
        return emotions

def main():
    """Test the dialogue generator"""
    generator = KoreanMangaDialogueGenerator()
    
    # Test scene context
    scene_context = SceneContext(
        scene_id=1,
        description="Ryan tries to cook a meal but struggles with the recipe",
        characters=["Ryan"],
        action="cook",
        object="stove/counter",
        location="kitchen",
        time="morning",
        scene_position="beginning"
    )
    
    # Generate dialogue
    dialogue_data = generator.generate_context_aware_dialogue(scene_context)
    print("Generated Dialogue:")
    print(json.dumps(dialogue_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 