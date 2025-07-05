#!/usr/bin/env python3
"""
StoryForge Configuration
Centralized configuration management for API keys and settings
"""

import os
from pathlib import Path

class Config:
    def __init__(self):
        self.config_file = Path(__file__).parent / '.config'
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or environment variables"""
        # Try to load from .config file first
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                print(f"✅ Loaded configuration from {self.config_file}")
            except Exception as e:
                print(f"⚠️ Could not load config file: {e}")
        
        # Set defaults
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.4'))
    
    def set_api_key(self, api_key: str):
        """Set Claude API key"""
        self.claude_api_key = api_key
        self.save_config()
        print("✅ API key saved to configuration")
    
    def remove_api_key(self):
        """Remove Claude API key"""
        self.claude_api_key = None
        self.save_config()
        print("✅ API key removed from configuration")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                f.write("# StoryForge Configuration\n")
                f.write("# This file is automatically managed - edit with caution\n\n")
                
                if self.claude_api_key:
                    f.write(f"CLAUDE_API_KEY={self.claude_api_key}\n")
                f.write(f"CLAUDE_MODEL={self.model}\n")
                f.write(f"MAX_TOKENS={self.max_tokens}\n")
                f.write(f"TEMPERATURE={self.temperature}\n")
            
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Could not save configuration: {e}")
    
    def get_api_key(self):
        """Get API key with validation"""
        if not self.claude_api_key:
            print("❌ No API key found!")
            print("Set your API key using:")
            print("  python -c \"from config import Config; Config().set_api_key('your-key-here')\"")
            return None
        return self.claude_api_key
    
    def show_status(self):
        """Show current configuration status"""
        print("🔧 Configuration Status:")
        print(f"  API Key: {'✅ Set' if self.claude_api_key else '❌ Not set'}")
        print(f"  Model: {self.model}")
        print(f"  Max Tokens: {self.max_tokens}")
        print(f"  Temperature: {self.temperature}")
        print(f"  Config File: {self.config_file}")

# Global config instance
config = Config()

def main():
    """Command line interface for configuration management"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 StoryForge Configuration Manager")
        print("Usage:")
        print("  python config.py set-key <your-api-key>")
        print("  python config.py remove-key")
        print("  python config.py status")
        return
    
    command = sys.argv[1]
    
    if command == "set-key":
        if len(sys.argv) < 3:
            print("❌ Please provide your API key")
            return
        api_key = sys.argv[2]
        config.set_api_key(api_key)
    
    elif command == "remove-key":
        config.remove_api_key()
    
    elif command == "status":
        config.show_status()
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main() 