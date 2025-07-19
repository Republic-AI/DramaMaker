# StoryForge - AI-Powered Story Processing System

## Overview
StoryForge is a natural language story processing system that transforms user story ideas into structured outputs for the DraMai multi-agent animation system. It uses Claude AI to extract story elements and generate multiple output formats.

## Current Features
- **Natural language story input** - Process stories in plain English
- **AI-powered structure extraction** - Uses Claude 3.5 Sonnet for intelligent parsing
- **Multi-format output generation** - Creates daily.yaml, drama.yaml, anime_script.json, and story_analysis.txt
- **Character-focused processing** - Optimized for Trump and Elon Musk stories
- **Configurable action mapping** - Maps story locations to available character actions
- **Robust error handling** - Fallback mechanisms and retry logic

## Workflow
```
User Story (Natural Language) 
    ↓
AI Structure Extraction (Claude 3.5 Sonnet)
    ↓
Story Analysis & Validation
    ↓
Multi-Format Generation
    ↓
Output Files (daily.yaml, drama.yaml, anime_script.json, story_analysis.txt)
    ↓
DraMai Integration
```

## System Architecture

### Core Components
- **`src/story_parser.py`** - Main processing engine with AI integration
- **`src/anime_script_config.json`** - Configuration for location-action mappings
- **`src/prompts/`** - AI prompt templates for story extraction and anime script generation
- **`main.py`** - Simple entry point to run the story parser

### Key Features
- Natural language story input
- AI-powered character and event extraction
- Automated daily schedule generation
- Drama event mapping with timing
- Detailed anime script generation with emotional beats
- DraMai system compatibility
- Robust JSON parsing with multiple fallback methods

## Installation

### Prerequisites
- Python 3.8+
- Claude API key from Anthropic

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your Claude API key using the configuration manager:
   ```bash
   python config.py set-key <your-claude-api-key-here>
   ```
   
   **Alternative methods:**
   ```bash
   # One-liner
   python -c "from config import Config; Config().set_api_key('your-key-here')"
   
   # Environment variable (still supported)
   export CLAUDE_API_KEY="your-claude-api-key-here"
   ```
   
   **Note**: The API key is stored in a local `.config` file that is automatically gitignored for security.

## Usage

### Basic Usage

#### Option 1: Using main.py (Recommended)
```bash
# Run from the StoryForge root directory
python main.py
```

#### Configuration Management
```bash
# Set your API key
python config.py set-key <your-api-key>

# Check configuration status
python config.py status

# Remove API key
python config.py remove-key
```

#### Option 2: Direct import
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from story_parser import SimpleStoryParser

# Initialize with your Claude API key
parser = SimpleStoryParser(api_key="your-claude-api-key")

# Process a story
story_text = """
Trump and Elon have a huge fight about Mars in the morning, 
then they accidentally get stuck in an elevator together at lunch. 
By evening, they realize they actually respect each other and make a secret deal.
"""

result = parser.process_story(story_text)
```

### Example Story Input
```
I want to see Trump and Elon have a huge fight about Mars in the morning, 
then they accidentally get stuck in an elevator together at lunch. 
By evening, they realize they actually respect each other and make a secret deal.

The story should start with Trump making a public announcement about his opposition 
to Mars colonization, which makes Elon really angry. They have a heated argument 
at a press conference around 9 AM. Then at lunchtime, they both end up in the same 
elevator at the Space Center, and it breaks down, forcing them to talk to each other. 
During this time, they discover they actually have more in common than they thought. 
By the end of the day, they secretly agree to work together on a joint Mars project 
while maintaining their public rivalry for political reasons.
```

### Generated Output Files

#### 1. daily.yaml
Character schedules and available actions for daily activities:
```yaml
npcCharacters:
  - npcId: 10012
    name: Trump
    description: Trump, 政治人物
    schedule: "06:00 Wake up\n08:00 Breakfast\n12:00 Lunch\n18:00 Dinner\n22:00 Sleep"
    availableActions:
      - actionName: Meeting
        description: Have a meeting
        actionId: 124
      - actionName: Speech
        description: Give a speech
        actionId: 129
```

#### 2. drama.yaml
Key dramatic events with timing and character interactions:
```yaml
npcEvents:
  - npcId: 10012
    name: Trump
    events:
      - id: event_0
        intro: Trump participates in an important event
        details: ["Heated argument about Mars colonization"]
```

#### 3. anime_script.json
Detailed animation script with actions, dialogue, and emotional beats:
```json
[
  {
    "npcId": 10012,
    "action": 129,
    "section": 1,
    "animationId": 40201,
    "preAction": 0,
    "param": "press_conference_room",
    "id": 1,
    "direction": "center",
    "focus": "1",
    "content": "I oppose Mars colonization! It's a waste of taxpayer money!"
  }
]
```

#### 4. story_analysis.txt
Human-readable story structure analysis:
```
==================================================
故事结构分析
==================================================

📖 标题: Trump和Elon的太空之争
🎭 类型: drama

👥 角色:
  • Trump - 政治人物
    特质: confrontational, political
    弧线: 从对立到合作
  • Elon - 科技企业家
    特质: innovative, focused
    弧线: 从冲突到理解

🎬 戏剧事件:
  • [09:00] Heated argument about Mars colonization
    地点: press_conference_room
    角色: Trump, Elon
```

## Configuration

### Character IDs
- Trump: 10012
- Elon: 10009

### Available Actions
- 104: Cook
- 105: Eat  
- 106: Sleep
- 110: Talk
- 116: Read
- 123: Analyze
- 124: Meeting
- 127: Visit
- 129: Speech
- 133: Share

### Location-Action Mappings
- `press_conference_room`: [129, 124] (Speech, Meeting)
- `space_center_elevator`: [110, 127] (Talk, Visit)
- `private_meeting_room`: [124, 110] (Meeting, Talk)

## Integration with DraMai
StoryForge generates files that are directly compatible with the existing DraMai system:
- **Character configurations** with proper NPC IDs
- **Daily schedules** with realistic timing
- **Drama events** with detailed descriptions
- **Available actions** mapped to specific locations
- **Anime scripts** with emotional depth and character interactions

## File Structure
```
StoryForge/
├── main.py                      # Entry point to run the system
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── src/
│   ├── story_parser.py          # Main processing engine
│   ├── anime_script_config.json # Location-action mappings
│   └── prompts/
│       ├── story_extraction.txt # AI prompt for story parsing
│       └── anime_script_generation.txt # AI prompt for script generation
├── examples/
│   ├── sample_story.txt         # Example story input
│   ├── sample_story2.txt        # Additional examples
│   └── sample_story2-1.txt
└── output/                      # Generated files (created automatically)
    ├── daily.yaml
    ├── drama.yaml
    ├── anime_script.json
    └── story_analysis.txt
```

## Error Handling
The system includes robust error handling:
- **API retry logic** with exponential backoff
- **JSON parsing fallbacks** with multiple extraction methods
- **Default configurations** when config files are missing
- **Graceful degradation** when AI generation fails

## Development
- Built with Python 3.8+
- Uses Claude 3.5 Sonnet for AI processing
- Modular design for easy extension
- Comprehensive error handling and logging

## License
This project is part of the DraMai system and follows the same licensing terms.