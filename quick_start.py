#!/usr/bin/env python3
"""
Quick Start Script for Reddit to TikTok Video Creator

A guided setup and first-run experience for new users.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Installing required dependency: python-dotenv...")
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()


class QuickStart:
    """Guided quick start experience for new users."""
    
    def __init__(self):
        """Initialize quick start."""
        self.env_file = Path(".env")
        self.setup_complete = False
    
    def print_welcome(self):
        """Print welcome message."""
        print("""
🎬 REDDIT TO TIKTOK VIDEO CREATOR
================================
Welcome! This quick start will help you:
✅ Set up your API credentials
✅ Configure the system  
✅ Create your first video
✅ Learn the basics

Let's get started! 🚀
""")
    
    def check_requirements(self) -> bool:
        """Check if basic requirements are met."""
        
        print("🔍 Checking requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ is required")
            print(f"   Your version: {sys.version}")
            return False
        else:
            print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check dependencies
        required_packages = [
            'langgraph', 'anthropic', 'openai', 'praw', 
            'moviepy', 'pillow', 'requests'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} (missing)")
        
        if missing_packages:
            print(f"\n📦 Installing missing packages...")
            for package in missing_packages:
                print(f"   Installing {package}...")
                os.system(f"pip install {package}")
        
        return True
    
    def setup_credentials(self):
        """Guide user through API credential setup."""
        
        print("\n🔑 API CREDENTIALS SETUP")
        print("=" * 30)
        print("You'll need API keys from three services:")
        print("1. Reddit (free)")
        print("2. Anthropic Claude (paid)")  
        print("3. OpenAI (paid)")
        print()
        
        # Check if .env already exists
        if self.env_file.exists():
            print("📝 Found existing .env file")
            choice = input("Do you want to update it? (y/N): ").strip().lower()
            if choice != 'y':
                return
        
        # Create .env from template
        example_file = Path(".env.example")
        if example_file.exists():
            print("📋 Copying configuration template...")
            with open(example_file, 'r') as f:
                env_content = f.read()
            
            with open(self.env_file, 'w') as f:
                f.write(env_content)
        
        # Guide through each API key
        self._setup_reddit_api()
        self._setup_anthropic_api()
        self._setup_openai_api()
        
        print("✅ API credentials configured!")
        print("📝 Saved to .env file")
    
    def _setup_reddit_api(self):
        """Guide Reddit API setup."""
        
        print("\n🔴 REDDIT API SETUP")
        print("=" * 20)
        print("1. Go to: https://www.reddit.com/prefs/apps")
        print("2. Click 'Create App' or 'Create Another App'")
        print("3. Choose 'script' as the app type")
        print("4. Fill in any name and description")
        print("5. For redirect URI, use: http://localhost:8080")
        print()
        
        client_id = input("Enter your Reddit Client ID: ").strip()
        client_secret = input("Enter your Reddit Client Secret: ").strip()
        
        if client_id and client_secret:
            self._update_env_file('REDDIT_CLIENT_ID', client_id)
            self._update_env_file('REDDIT_CLIENT_SECRET', client_secret)
            print("✅ Reddit API configured")
        else:
            print("⚠️  Skipping Reddit API (you can configure it later)")
    
    def _setup_anthropic_api(self):
        """Guide Anthropic API setup."""
        
        print("\n🤖 ANTHROPIC CLAUDE API SETUP")
        print("=" * 30)
        print("1. Go to: https://console.anthropic.com/")
        print("2. Sign up or log in")
        print("3. Go to API Keys section")
        print("4. Create a new API key")
        print("💡 Claude is used for content quality assessment")
        print()
        
        api_key = input("Enter your Anthropic API Key: ").strip()
        
        if api_key:
            self._update_env_file('ANTHROPIC_API_KEY', api_key)
            print("✅ Anthropic API configured")
        else:
            print("⚠️  Skipping Anthropic API (required for quality assessment)")
    
    def _setup_openai_api(self):
        """Guide OpenAI API setup."""
        
        print("\n🎤 OPENAI API SETUP")
        print("=" * 18)
        print("1. Go to: https://platform.openai.com/api-keys")
        print("2. Sign up or log in")
        print("3. Create a new secret key")
        print("💡 OpenAI is used for high-quality text-to-speech")
        print("💰 This will incur costs (~$0.015 per 1K characters)")
        print()
        
        api_key = input("Enter your OpenAI API Key: ").strip()
        
        if api_key:
            self._update_env_file('OPENAI_API_KEY', api_key)
            print("✅ OpenAI API configured")
        else:
            print("⚠️  Skipping OpenAI API (will use free Edge TTS instead)")
            self._update_env_file('TTS_PREFERRED_SERVICE', 'edge')
    
    def _update_env_file(self, key: str, value: str):
        """Update a value in the .env file."""
        
        if not self.env_file.exists():
            return
        
        # Read current content
        with open(self.env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add the key
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"{key}={value}\n")
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(lines)
    
    async def test_setup(self) -> bool:
        """Test the setup by running component tests."""
        
        print("\n🧪 TESTING SETUP")
        print("=" * 15)
        
        try:
            from main import CLI
            cli = CLI()
            
            # Run tests
            class MockArgs:
                component = 'all'
            
            result = await cli.cmd_test(MockArgs())
            
            if result == 0:
                print("🎉 All tests passed! Setup is complete.")
                return True
            else:
                print("⚠️  Some tests failed. Please check your API keys.")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def configure_preferences(self):
        """Configure user preferences."""
        
        print("\n⚙️  CONFIGURATION")
        print("=" * 15)
        print("Let's configure some preferences:")
        print()
        
        # Subreddit selection
        print("📡 Which subreddits would you like to use?")
        print("1. Funny & Memes (funny, memes, wholesomememes)")
        print("2. Stories (tifu, confession, amitheasshole)")  
        print("3. Mixed Content (funny, tifu, askreddit, memes)")
        print("4. Family Friendly (wholesomememes, mademesmile, aww)")
        print("5. Custom selection")
        
        choice = input("\nChoose (1-5) [3]: ").strip() or "3"
        
        subreddit_options = {
            "1": "funny,memes,wholesomememes",
            "2": "tifu,confession,amitheasshole", 
            "3": "funny,tifu,askreddit,memes,wholesome",
            "4": "wholesomememes,mademesmile,aww",
            "5": input("Enter comma-separated subreddits: ").strip()
        }
        
        if choice in subreddit_options:
            subreddits = subreddit_options[choice]
            self._update_env_file('REDDIT_SUBREDDITS', subreddits)
            print(f"✅ Using subreddits: {subreddits}")
        
        # Quality setting
        print("\n📊 Content quality setting:")
        print("1. High quality (8.5/10 minimum, fewer videos)")
        print("2. Balanced (7.0/10 minimum, good balance)")
        print("3. High volume (6.0/10 minimum, more videos)")
        
        quality_choice = input("\nChoose (1-3) [2]: ").strip() or "2"
        
        quality_settings = {
            "1": ("8.5", "3"),  # rating, daily_limit
            "2": ("7.0", "6"),
            "3": ("6.0", "10")
        }
        
        if quality_choice in quality_settings:
            rating, daily_limit = quality_settings[quality_choice]
            self._update_env_file('CONTENT_MIN_HUMOR_RATING', rating)
            self._update_env_file('SCHEDULE_MAX_VIDEOS_PER_DAY', daily_limit)
            print(f"✅ Quality setting: {rating}/10 minimum")
        
        print("✅ Preferences configured!")
    
    async def create_first_video(self):
        """Create the first video."""
        
        print("\n🎬 CREATING YOUR FIRST VIDEO")
        print("=" * 30)
        print("Let's create your first TikTok video!")
        print()
        
        try:
            from main import CLI
            cli = CLI()
            
            class MockArgs:
                count = 1
                preset = None
                subreddits = None
                min_rating = None
                style = None
                voice = None
            
            print("🚀 Starting video creation...")
            result = await cli.cmd_create(MockArgs())
            
            if result == 0:
                print("\n🎉 SUCCESS! Your first video has been created!")
                print("📁 Check the output_videos/ready_to_upload/ folder")
                print("📝 The video includes suggested captions and hashtags")
                print("📱 You can now upload it to TikTok manually")
            else:
                print("\n❌ Video creation failed. Check the logs for details.")
                
        except Exception as e:
            print(f"❌ Error creating video: {e}")
    
    def show_next_steps(self):
        """Show next steps and usage examples."""
        
        print("\n🎓 NEXT STEPS")
        print("=" * 12)
        print("Now that you're set up, here's what you can do:")
        print()
        print("📹 Create videos:")
        print("   python main.py create                    # Create one video")
        print("   python main.py create --count 3          # Create 3 videos")
        print("   python main.py create --preset high_quality")
        print()
        print("📋 Manage videos:")
        print("   python main.py list                      # List created videos")
        print("   python main.py queue --show              # Show upload queue")
        print()
        print("⚙️  System management:")
        print("   python main.py status                    # Check system status")
        print("   python main.py config --show             # Show configuration")
        print()
        print("⏰ Automated creation:")
        print("   python scheduler.py start                # Start automated creation")
        print("   python scheduler.py status               # Check scheduler status")
        print()
        print("📚 Documentation:")
        print("   README.md - Complete documentation")
        print("   .env - Configuration file")
        print()
        print("🎉 You're all set! Happy video creating!")
    
    async def run(self):
        """Run the complete quick start process."""
        
        self.print_welcome()
        
        # Step 1: Check requirements
        if not self.check_requirements():
            print("❌ Requirements check failed. Please fix issues and try again.")
            return
        
        # Step 2: Setup credentials
        self.setup_credentials()
        
        # Step 3: Test setup
        if not await self.test_setup():
            print("⚠️  Setup test failed. You may need to check your API keys.")
            choice = input("Continue anyway? (y/N): ").strip().lower()
            if choice != 'y':
                return
        
        # Step 4: Configure preferences
        self.configure_preferences()
        
        # Step 5: Create first video
        choice = input("\nCreate your first video now? (Y/n): ").strip().lower()
        if choice != 'n':
            await self.create_first_video()
        
        # Step 6: Show next steps
        self.show_next_steps()


async def main():
    """Main function."""
    
    try:
        quick_start = QuickStart()
        await quick_start.run()
        
    except KeyboardInterrupt:
        print("\n👋 Quick start cancelled. Run again anytime!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please check your setup and try again.")


if __name__ == "__main__":
    asyncio.run(main())
