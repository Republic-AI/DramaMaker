#!/usr/bin/env python3
"""
简化版StoryForge MVP
输入故事 -> 生成3个文件：daily.yaml, anime_script.json, story_analysis.txt
默认只处理Trump和Elon的故事
"""

import json
import yaml
import anthropic
import re
import os
import time

def load_prompt(prompt_path, **kwargs):
    """Load and format prompt from file"""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read()
    return prompt.format(**kwargs)

class SimpleStoryParser:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_retries = 3
        self.retry_delay = 2
        
        # 加载场景-动作配置
        self.config = self._load_config()
    
    def _load_config(self):
        """加载场景-动作配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'anime_script_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config not found, using default settings")
            return self._get_default_config()
    
    def _get_default_config(self):
        """默认配置"""
        return {
            "setting_action_mapping": {
                "trumpSpeech": {"available_actions": [129], "name": "Trump's Speech Location"},
                "trumpMeeting": {"available_actions": [124], "name": "Trump's Meeting Room"},
                "muskData_right_1": {"available_actions": [123], "name": "Elon's Data Station"},
                "muskMeeting": {"available_actions": [124], "name": "Elon's Meeting Room"},
                "press_conference_room": {"available_actions": [129, 124], "name": "Press Conference Room"},
                "space_center_elevator": {"available_actions": [110, 127], "name": "Space Center Elevator"},
                "private_meeting_room": {"available_actions": [124, 110], "name": "Private Meeting Room"}
            },
            "character_ids": {"Trump": 10012, "Elon": 10009},
            "action_definitions": {
                "104": "Cook", "105": "Eat", "106": "Sleep", "110": "Talk",
                "116": "Read", "123": "Analyze", "124": "Meeting", "127": "Visit",
                "129": "Speech", "133": "Share"
            }
        }
    
    def _parse_story(self, story_text):
        """使用story_parser.py的解析方法"""
        try:
            # 构建绝对路径到prompt文件
            script_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(script_dir, 'prompts', 'story_extraction.txt')
            
            # 使用load_prompt函数加载和格式化prompt
            prompt = load_prompt(prompt_path, story_text=story_text)
            print(f"✅ 成功加载prompt: {prompt_path}")
            print(f"📖 故事长度: {len(story_text)} 字符")
            print(f"📖 故事预览: {story_text[:100]}...")
        except FileNotFoundError:
            print("⚠️ story_extraction.txt 未找到，使用默认prompt")
            prompt = f"""你是一个故事结构分析器。分析以下故事并提取关键信息：

故事：{story_text}

请返回JSON格式：
{{
  "story_title": "故事标题",
  "genre": "comedy|drama|thriller",
  "characters": [
    {{
      "name": "Trump|Elon",
      "role": "角色描述",
      "personality_traits": ["特质1", "特质2"],
      "character_arc": "角色弧线"
    }}
  ],
  "drama_events": [
    {{
      "id": "事件ID",
      "time_suggestion": "HH:MM",
      "characters": ["Trump", "Elon"],
      "location": "场景名称",
      "description": "事件描述"
    }}
  ]
}}

只返回JSON，不要其他文字。"""
        
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 API调用尝试 {attempt + 1}/{self.max_retries}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = getattr(response.content[0], 'text', str(response.content[0])) if response.content else ""
                
                # 提取JSON
                parsed_json = self._extract_json_from_response(content)
                if parsed_json and self._validate_structure(parsed_json):
                    print(f"✅ 成功解析JSON")
                    return parsed_json
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                print(f"❌ API调用错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        return self._fallback_structure()
    
    def _extract_json_from_response(self, content):
        """从AI响应中提取JSON的多种方法"""
        # 方法1: 查找大括号之间的JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group())
                return parsed_json
            except json.JSONDecodeError as e:
                print(f"JSON解码错误: {e}")
        
        # 方法2: 查找```json或```块
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_block_match:
            try:
                parsed_json = json.loads(json_block_match.group(1))
                return parsed_json
            except json.JSONDecodeError as e:
                print(f"JSON块解码错误: {e}")
        
        # 方法3: 尝试找到最大的JSON结构
        json_candidates = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        for candidate in sorted(json_candidates, key=len, reverse=True):
            try:
                parsed_json = json.loads(candidate)
                return parsed_json
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _validate_structure(self, data):
        """验证JSON结构"""
        return all(key in data for key in ['story_title', 'characters', 'drama_events'])
    
    def _fallback_structure(self):
        """备用结构"""
        return {
            "story_title": "Trump和Elon的故事",
            "genre": "drama",
            "characters": [
                {"name": "Trump", "role": "政治人物", "personality_traits": ["confrontational"], "character_arc": "从对立到合作"},
                {"name": "Elon", "role": "科技企业家", "personality_traits": ["innovative"], "character_arc": "从冲突到理解"}
            ],
            "drama_events": [
                {"id": "main_event", "time_suggestion": "12:00", "characters": ["Trump", "Elon"], "location": "press_conference_room", "description": "重要事件"}
            ]
        }
    
    def generate_daily_yaml(self, structure):
        """生成daily.yaml"""
        daily_data = {"npcCharacters": []}
        
        for char in structure.get('characters', []):
            char_name = char.get('name', '')
            if char_name in ['Trump', 'Elon']:
                char_data = {
                    "npcId": self.config['character_ids'].get(char_name, 10000),
                    "name": char_name,
                    "description": f"{char_name}, {char.get('role', 'Main character')}",
                    "schedule": self._get_schedule(char_name),
                    "availableActions": self._get_actions(char_name)
                }
                daily_data["npcCharacters"].append(char_data)
        
        return yaml.dump(daily_data, default_flow_style=False, allow_unicode=True)
    
    def _get_schedule(self, char_name):
        """获取角色时间表"""
        if char_name == "Trump":
            return "06:00 Wake up\n08:00 Breakfast\n12:00 Lunch\n18:00 Dinner\n22:00 Sleep"
        elif char_name == "Elon":
            return "08:00 Start work\n10:00 Break\n12:00 Lunch\n15:00 Break\n18:00 End work"
        return "09:00 Start work\n12:00 Lunch\n15:00 Break\n18:00 End work"
    
    def _get_actions(self, char_name):
        """获取角色可用动作"""
        if char_name == "Trump":
            return [
                {"actionName": "Meeting", "description": "Have a meeting", "actionId": 124},
                {"actionName": "Speech", "description": "Give a speech", "actionId": 129},
                {"actionName": "Read", "description": "Read documents", "actionId": 116},
                {"actionName": "Visit", "description": "Visit another NPC", "actionId": 127}
            ]
        elif char_name == "Elon":
            return [
                {"actionName": "Analyze", "description": "Analyze data", "actionId": 123},
                {"actionName": "Meeting", "description": "Have a meeting", "actionId": 124},
                {"actionName": "Read", "description": "Read documents", "actionId": 116},
                {"actionName": "Visit", "description": "Visit another NPC", "actionId": 127}
            ]
        return []
    
    def generate_anime_script(self, structure):
        """使用AI生成anime_script.json"""
        try:
            # 构建绝对路径到prompt文件
            script_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(script_dir, 'prompts', 'anime_script_generation.txt')
            
            # 准备故事事件数据
            drama_events = structure.get('drama_events', [])
            if not drama_events:
                print("⚠️ 没有找到戏剧事件，使用默认事件")
                drama_events = [
                    {"id": "default_event", "time_suggestion": "12:00", "characters": ["Trump", "Elon"], 
                     "location": "press_conference_room", "description": "重要事件"}
                ]
            
            # 格式化事件数据，添加更多细节
            story_events = []
            for event in drama_events:
                # 提取更多上下文信息
                characters = event.get('characters', [])
                location = event.get('location', 'Unknown')
                time = event.get('time_suggestion', 'Unknown')
                description = event.get('description', 'Event description')
                
                # 为每个角色添加个性化细节
                character_details = []
                for char in characters:
                    if char == "Trump":
                        character_details.append(f"{char}: Confrontational, political, loves attention, speaks in bold statements")
                    elif char == "Elon":
                        character_details.append(f"{char}: Innovative, focused on technology, speaks about future and progress")
                
                event_data = {
                    "id": event.get('id', 'event'),
                    "intro": description,
                    "details": [
                        f"Location: {location}",
                        f"Time: {time}",
                        f"Characters: {', '.join(characters)}",
                        f"Character personalities: {'; '.join(character_details)}",
                        f"Emotional tone: {self._get_emotional_tone(description)}",
                        f"Scene importance: {self._get_scene_importance(description)}"
                    ]
                }
                story_events.append(event_data)
            
            # 直接读取prompt文件并手动替换占位符
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            # 添加详细化指令
            detailed_instructions = """

## ENHANCED DETAIL REQUIREMENTS

Make the anime script MUCH more detailed and rich:

1. **DIALOGUE DETAILS**: 
   - Extract and include actual dialogue from the story
   - Add character-specific speech patterns (Trump: bold, political language; Elon: technical, future-focused)
   - Include emotional reactions and tone changes

2. **ACTION SEQUENCES**:
   - Break down complex events into multiple sequential actions
   - Add reaction shots and character movements
   - Include environmental interactions (elevator buttons, press conference setup)

3. **EMOTIONAL BEATS**:
   - Add facial expressions and body language actions
   - Include internal monologue moments (Action 110 with introspective content)
   - Show character development through subtle actions

4. **SCENE TRANSITIONS**:
   - Add detailed scene setup actions
   - Include camera movements and focus changes
   - Show location changes with proper transitions

5. **CHARACTER INTERACTIONS**:
   - Add more dialogue exchanges between characters
   - Include non-verbal communication (gestures, expressions)
   - Show power dynamics and relationship changes

6. **ENVIRONMENTAL DETAILS**:
   - Add actions that show the setting (elevator controls, press conference room)
   - Include background characters and atmosphere
   - Show time progression through lighting/atmosphere changes

Generate at least 15-20 detailed actions that fully capture the emotional and narrative complexity of the story.

"""
            
            prompt = prompt.replace('{story_events}', json.dumps(story_events, indent=2, ensure_ascii=False))
            prompt += detailed_instructions
            print(f"✅ 成功加载anime script prompt: {prompt_path}")
            
        except FileNotFoundError:
            print("⚠️ anime_script_generation.txt 未找到，使用默认方法")
            return self._generate_anime_script_fallback(structure)
        
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 Anime script API调用尝试 {attempt + 1}/{self.max_retries}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.4,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = getattr(response.content[0], 'text', str(response.content[0])) if response.content else ""
                
                # 提取JSON数组
                anime_script = self._extract_anime_script_json(content)
                if anime_script:
                    print(f"✅ 成功生成anime script ({len(anime_script)} 个动作)")
                    return anime_script
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                print(f"❌ Anime script API调用错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        print("⚠️ AI生成失败，使用备用方法")
        return self._generate_anime_script_fallback(structure)
    
    def _extract_anime_script_json(self, content):
        """从AI响应中提取anime script JSON数组"""
        # 方法1: 查找JSON数组
        json_array_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
        if json_array_match:
            try:
                anime_script = json.loads(json_array_match.group())
                if isinstance(anime_script, list):
                    return anime_script
            except json.JSONDecodeError as e:
                print(f"Anime script JSON解码错误: {e}")
        
        # 方法2: 查找```json块中的数组
        json_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
        if json_block_match:
            try:
                anime_script = json.loads(json_block_match.group(1))
                if isinstance(anime_script, list):
                    return anime_script
            except json.JSONDecodeError as e:
                print(f"Anime script JSON块解码错误: {e}")
        
        return None
    
    def _get_emotional_tone(self, description):
        """分析事件的情感基调"""
        description_lower = description.lower()
        if any(word in description_lower for word in ['fight', 'argument', 'conflict', 'heated', 'angry']):
            return "confrontational, tense"
        elif any(word in description_lower for word in ['trapped', 'stuck', 'forced']):
            return "claustrophobic, uncomfortable"
        elif any(word in description_lower for word in ['respect', 'understand', 'agree', 'deal']):
            return "reconciliation, understanding"
        elif any(word in description_lower for word in ['announce', 'speech', 'public']):
            return "public, performative"
        else:
            return "neutral, conversational"
    
    def _get_scene_importance(self, description):
        """分析场景的重要性"""
        description_lower = description.lower()
        if any(word in description_lower for word in ['announce', 'public', 'speech', 'deal', 'partnership']):
            return "critical plot point"
        elif any(word in description_lower for word in ['fight', 'argument', 'conflict']):
            return "major conflict"
        elif any(word in description_lower for word in ['trapped', 'stuck', 'elevator']):
            return "character development"
        else:
            return "supporting scene"
    
    def _generate_anime_script_fallback(self, structure):
        """备用anime script生成方法"""
        anime_script = []
        section_counter = 1
        
        for event in structure.get('drama_events', []):
            characters = event.get('characters', [])
            location = event.get('location', 'press_conference_room')
            description = event.get('description', '')
            
            # 确定场景和动作
            scene_info = self.config['setting_action_mapping'].get(location, {})
            available_actions = scene_info.get('available_actions', [124])
            
            # 为每个角色生成动作
            for char_name in characters:
                if char_name in ['Trump', 'Elon']:
                    npc_id = self.config['character_ids'].get(char_name, 10000)
                    
                    # 选择第一个可用动作
                    action_id = available_actions[0] if available_actions else 124
                    
                    # 生成动画ID
                    animation_id = 40201 if char_name == "Trump" else 40301
                    
                    # 创建脚本条目
                    script_entry = {
                        "npcId": npc_id,
                        "action": action_id,
                        "section": section_counter,
                        "animationId": animation_id,
                        "preAction": 0,
                        "param": location,
                        "id": 1,
                        "direction": "center",
                        "focus": "1"
                    }
                    
                    # 如果是对话动作，添加内容
                    if action_id == 110:
                        script_entry["content"] = description
                    
                    anime_script.append(script_entry)
                    section_counter += 1
        
        return anime_script
    
    def generate_drama_yaml(self, structure):
        """生成drama.yaml"""
        drama_data = {
            "npcEvents": []
        }
        
        for char in structure.get('characters', []):
            char_events = [e for e in structure.get('drama_events', []) if char.get('name') in e.get('characters', [])]
            
            if char_events:
                npc_event = {
                    "npcId": self.config['character_ids'].get(char.get('name', ''), 10000),
                    "name": char.get('name', 'Unknown'),
                    "events": []
                }
                
                for event in char_events:
                    event_data = {
                        "id": f"event_{len(npc_event['events'])}",
                        "intro": f"{char.get('name')} participates in an important event",
                        "details": [event.get('description', 'Event description')]
                    }
                    npc_event["events"].append(event_data)
                
                drama_data["npcEvents"].append(npc_event)
        
        return yaml.dump(drama_data, default_flow_style=False, allow_unicode=True)
    
    def generate_story_analysis(self, structure):
        """生成story_analysis.txt"""
        lines = []
        lines.append("=" * 50)
        lines.append("故事结构分析")
        lines.append("=" * 50)
        lines.append(f"\n📖 标题: {structure.get('story_title', 'Untitled')}")
        lines.append(f"🎭 类型: {structure.get('genre', 'Unknown')}")
        
        # 角色信息
        lines.append("\n👥 角色:")
        for char in structure.get('characters', []):
            lines.append(f"  • {char.get('name', 'Unknown')} - {char.get('role', 'Character')}")
            if char.get('personality_traits'):
                lines.append(f"    特质: {', '.join(char['personality_traits'])}")
            if char.get('character_arc'):
                lines.append(f"    弧线: {char['character_arc']}")
        
        # 事件信息
        lines.append("\n🎬 戏剧事件:")
        for event in structure.get('drama_events', []):
            lines.append(f"  • [{event.get('time_suggestion', 'Time unknown')}] {event.get('description', 'Event')}")
            lines.append(f"    地点: {event.get('location', 'Location unknown')}")
            if event.get('characters'):
                lines.append(f"    角色: {', '.join(event['characters'])}")
        
        return '\n'.join(lines)
    
    def process_story(self, story_text):
        """处理故事的主流程"""
        print("🔍 开始故事分析...")
        
        # 创建输出目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 解析故事
        structure = self._parse_story(story_text)
        if not structure:
            print("❌ 故事解析失败")
            return None
        
        # 2. 生成daily.yaml
        daily_yaml = self.generate_daily_yaml(structure)
        daily_path = os.path.join(output_dir, 'daily.yaml')
        with open(daily_path, 'w', encoding='utf-8') as f:
            f.write(daily_yaml)
        print(f"✅ 生成 daily.yaml")
        
        # 3. 生成drama.yaml
        drama_yaml = self.generate_drama_yaml(structure)
        drama_path = os.path.join(output_dir, 'drama.yaml')
        with open(drama_path, 'w', encoding='utf-8') as f:
            f.write(drama_yaml)
        print(f"✅ 生成 drama.yaml")
        
        # 4. 生成anime_script.json
        anime_script = self.generate_anime_script(structure)
        anime_path = os.path.join(output_dir, 'anime_script.json')
        with open(anime_path, 'w', encoding='utf-8') as f:
            json.dump(anime_script, f, indent=2, ensure_ascii=False)
        print(f"✅ 生成 anime_script.json ({len(anime_script)} 个动作)")
        
        # 5. 生成story_analysis.txt
        analysis_text = self.generate_story_analysis(structure)
        analysis_path = os.path.join(output_dir, 'story_analysis.txt')
        with open(analysis_path, 'w', encoding='utf-8') as f:
            f.write(analysis_text)
        print(f"✅ 生成 story_analysis.txt")
        
        print(f"\n🎉 完成！所有文件保存到: {output_dir}")
        return structure

# 使用示例
if __name__ == "__main__":
    # 初始化 - API key should be set as environment variable
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import config
    
    api_key = config.get_api_key()
    if not api_key:
        print("❌ Error: CLAUDE_API_KEY environment variable not set")
        print("Please set your Claude API key: export CLAUDE_API_KEY='your-api-key-here'")
        exit(1)
    
    parser = SimpleStoryParser(api_key=api_key)
    
    # 读取示例故事
    try:
        # 构建绝对路径到故事文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        story_path = os.path.join(script_dir, '..', 'examples', 'sample_story.txt')
        
        with open(story_path, 'r', encoding='utf-8') as f:
            story = f.read()
        print(f"📖 成功读取示例故事: {story_path}")
        print(f"📖 故事长度: {len(story)} 字符")
        print(f"📖 故事预览: {story[:100]}...")
    except FileNotFoundError:
        story = "Trump和Elon在Space Center的电梯里被困住了，他们被迫交谈，最终发现彼此的共同点。"
        print("⚠️ sample_story.txt 未找到，使用默认故事")
    except Exception as e:
        story = "Trump和Elon在Space Center的电梯里被困住了，他们被迫交谈，最终发现彼此的共同点。"
        print(f"⚠️ 读取故事文件时出错: {e}，使用默认故事")
    
    # 处理故事
    result = parser.process_story(story)
    
    # 显示结果
    if result:
        print("\n" + "="*50)
        print("生成结果预览:")
        print("="*50)
        
        # 显示anime script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        anime_path = os.path.join(script_dir, '..', 'output', 'anime_script.json')
        if os.path.exists(anime_path):
            with open(anime_path, 'r', encoding='utf-8') as f:
                anime_script = json.load(f)
            print(f"\n🎬 Anime Script:")
            for i, action in enumerate(anime_script, 1):
                print(f"  {i}. NPC {action['npcId']} - Action {action['action']} - Section {action['section']}") 