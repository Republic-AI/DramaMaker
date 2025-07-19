#!/usr/bin/env python3
"""
StoryForge Main Entry Point
Simple interface to run the story parser from the root directory
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

try:
    from story_parser import SimpleStoryParser  # type: ignore
    from config import config
except ImportError as e:
    print(f"❌ Error: Could not import required modules from {src_path}")
    print("Make sure story_parser.py exists in the src directory")
    sys.exit(1)

def main():
    """Main entry point for StoryForge"""
    print("🎭 StoryForge - AI-Powered Story Processing System")
    print("=" * 50)
    
    # Get API key from configuration
    api_key = config.get_api_key()
    if not api_key:
        print("\n🔧 To set up your API key, run:")
        print("  python config.py set-key <your-claude-api-key>")
        print("  or")
        print("  python -c \"from config import Config; Config().set_api_key('your-key-here')\"")
        sys.exit(1)
    
    parser = SimpleStoryParser(api_key=api_key)
    
    # Read example story
    try:
        story_path = os.path.join(os.path.dirname(__file__), 'examples', 'sample_story.txt')
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
    
    # Process story
    result = parser.process_story(story)
    
    # Show results
    if result:
        print("\n" + "="*50)
        print("生成结果预览:")
        print("="*50)
        
        # Show anime script summary
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        anime_path = os.path.join(output_dir, 'anime_script.json')
        if os.path.exists(anime_path):
            import json
            with open(anime_path, 'r', encoding='utf-8') as f:
                anime_script = json.load(f)
            print(f"\n🎬 Anime Script Summary:")
            print(f"Total actions: {len(anime_script)}")
            for i, action in enumerate(anime_script[:5], 1):
                print(f"  {i}. NPC {action['npcId']} - Action {action['action']} - Section {action['section']}")
            if len(anime_script) > 5:
                print(f"  ... and {len(anime_script) - 5} more actions")
        
        print(f"\n📁 All output files saved to: {output_dir}")
        print("   - daily.yaml")
        print("   - drama.yaml") 
        print("   - anime_script.json")
        print("   - story_analysis.txt")
    else:
        print("❌ Story processing failed")

if __name__ == "__main__":
    main() 