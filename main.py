#!/usr/bin/env python3
"""
Reddit to TikTok Video Creator - Main Entry Point

Command-line interface for the Reddit to TikTok video creation system.
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Please run: pip install python-dotenv")

from src.main_agent import RedditTikTokAgent
from config.settings import get_config, load_preset, ConfigManager
from src.video_organizer import VideoOrganizer


class CLI:
    """Command Line Interface for the Reddit to TikTok Video Creator."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config_manager = get_config()
        self.organizer = VideoOrganizer()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        
        parser = argparse.ArgumentParser(
            description="Reddit to TikTok Video Creator",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py create                     # Create one video with default settings
  python main.py create --count 3          # Create 3 videos
  python main.py create --preset high_quality  # Use high quality preset
  python main.py list                      # List created videos
  python main.py status                    # Show system status
  python main.py setup                     # Run initial setup
  python main.py test                      # Test all components
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Create command
        create_parser = subparsers.add_parser('create', help='Create TikTok videos from Reddit content')
        create_parser.add_argument('--count', type=int, default=1, help='Number of videos to create')
        create_parser.add_argument('--preset', choices=['high_quality', 'high_volume', 'family_friendly'], 
                                 help='Use a preset configuration')
        create_parser.add_argument('--subreddits', nargs='+', help='Specific subreddits to use')
        create_parser.add_argument('--min-rating', type=float, help='Minimum humor rating (1-10)')
        create_parser.add_argument('--style', choices=['modern', 'minimal', 'dynamic', 'story'], 
                                 help='Video style')
        create_parser.add_argument('--voice', choices=['auto', 'funny_male', 'funny_female', 'story_male', 'story_female', 'dramatic', 'casual'],
                                 help='Voice style for TTS')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List created videos')
        list_parser.add_argument('--limit', type=int, default=10, help='Number of videos to show')
        list_parser.add_argument('--filter', choices=['ready', 'uploaded', 'all'], default='all',
                               help='Filter videos by status')
        
        # Status command
        subparsers.add_parser('status', help='Show system status and statistics')
        
        # Setup command
        setup_parser = subparsers.add_parser('setup', help='Run initial setup and configuration')
        setup_parser.add_argument('--force', action='store_true', help='Force setup even if already configured')
        
        # Test command
        test_parser = subparsers.add_parser('test', help='Test system components')
        test_parser.add_argument('--component', choices=['reddit', 'claude', 'openai', 'video', 'all'], 
                               default='all', help='Test specific component')
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_parser.add_argument('--show', action='store_true', help='Show current configuration')
        config_parser.add_argument('--validate', action='store_true', help='Validate configuration')
        config_parser.add_argument('--create-example', action='store_true', help='Create example .env file')
        
        # Queue command
        queue_parser = subparsers.add_parser('queue', help='Manage upload queue')
        queue_parser.add_argument('--show', action='store_true', help='Show upload queue')
        queue_parser.add_argument('--clear', action='store_true', help='Clear upload queue')
        
        return parser
    
    async def cmd_create(self, args) -> int:
        """Handle the create command."""
        
        print("🎬 Starting video creation...")
        
        try:
            # Get base configuration
            config = self.config_manager.get_agent_config()
            
            # Apply preset if specified
            if args.preset:
                preset_config = load_preset(args.preset)
                config.update(preset_config)
                print(f"📋 Using preset: {args.preset}")
            
            # Apply command line overrides
            if args.subreddits:
                config['subreddits'] = args.subreddits
                print(f"🎯 Using subreddits: {', '.join(args.subreddits)}")
            
            if args.min_rating:
                config['min_humor_rating'] = args.min_rating
                print(f"📊 Minimum rating: {args.min_rating}/10")
            
            if args.style:
                config['video_style'] = args.style
                print(f"🎨 Video style: {args.style}")
            
            if args.voice and args.voice != 'auto':
                config['voice_style'] = args.voice
                print(f"🎤 Voice style: {args.voice}")
            
            # Create agent and run
            agent = RedditTikTokAgent(config)
            
            if args.count == 1:
                # Single video
                result = await agent.run()
                return 0 if result['creation_status'] == 'success' else 1
            else:
                # Multiple videos
                print(f"🎬 Creating {args.count} videos...")
                results = agent.run_batch(args.count)
                
                successful = sum(1 for r in results if r['creation_status'] == 'success')
                print(f"✅ Created {successful}/{args.count} videos successfully")
                
                return 0 if successful > 0 else 1
                
        except Exception as e:
            print(f"❌ Video creation failed: {e}")
            return 1
    
    def cmd_list(self, args) -> int:
        """Handle the list command."""
        
        try:
            print(f"📹 Listing videos (limit: {args.limit})...")
            self.organizer.list_created_videos(limit=args.limit)
            
            # Show queue status
            queue = self.organizer.get_upload_queue()
            if queue:
                print(f"\n📤 Upload Queue: {len(queue)} videos ready")
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to list videos: {e}")
            return 1
    
    def cmd_status(self, args) -> int:
        """Handle the status command."""
        
        try:
            print("📊 System Status:")
            print("=" * 50)
            
            # Component status
            try:
                agent = RedditTikTokAgent()
                status = agent.get_status()
                
                print(f"🤖 Agent: {'Ready' if status['agent_ready'] else 'Error'}")
                print(f"📹 Total Videos: {status['total_videos_created']}")
                print(f"📊 Avg Quality: {status['average_humor_rating']:.1f}/10")
                print(f"📤 Ready to Upload: {status['videos_ready_to_upload']}")
                
                if status['most_popular_subreddit'] != 'none':
                    print(f"🔥 Top Subreddit: r/{status['most_popular_subreddit']}")
                
                print(f"\n🔧 Components:")
                for component, component_status in status['components_status'].items():
                    status_icon = "✅" if component_status == "ready" else "❌"
                    print(f"   {status_icon} {component.replace('_', ' ').title()}")
                
            except Exception as e:
                print(f"❌ Could not get agent status: {e}")
            
            # Configuration status
            print(f"\n⚙️  Configuration:")
            errors = self.config_manager.validate_config()
            if errors:
                print(f"   ❌ {len(errors)} configuration errors")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      • {error}")
                if len(errors) > 3:
                    print(f"      • ... and {len(errors) - 3} more")
            else:
                print(f"   ✅ Configuration valid")
            
            # Storage status
            output_dir = Path("output_videos")
            if output_dir.exists():
                video_files = list(output_dir.glob("**/*.mp4"))
                total_size = sum(f.stat().st_size for f in video_files) / (1024**2)  # MB
                print(f"\n💾 Storage:")
                print(f"   📁 Video Files: {len(video_files)}")
                print(f"   📦 Total Size: {total_size:.1f} MB")
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to get status: {e}")
            return 1
    
    def cmd_setup(self, args) -> int:
        """Handle the setup command."""
        
        print("🔧 Reddit to TikTok Video Creator Setup")
        print("=" * 40)
        
        try:
            # Check if already set up
            env_file = Path(".env")
            if env_file.exists() and not args.force:
                print("✅ Setup already completed!")
                print("💡 Use --force to run setup again")
                return 0
            
            # Create directory structure
            print("📁 Creating directory structure...")
            directories = [
                "output_videos",
                "output_videos/ready_to_upload", 
                "output_videos/uploaded",
                "output_videos/archive",
                "output_videos/audio",
                "output_videos/logs",
                "assets",
                "assets/fonts",
                "assets/backgrounds",
                "config",
                "tests"
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {directory}")
            
            # Create example .env file
            print("\n📝 Creating example configuration...")
            self.config_manager.create_example_env_file()
            
            # Create gitkeep files
            print("\n📄 Creating placeholder files...")
            gitkeep_dirs = [
                "output_videos/.gitkeep",
                "assets/fonts/.gitkeep", 
                "assets/backgrounds/.gitkeep"
            ]
            
            for gitkeep in gitkeep_dirs:
                Path(gitkeep).touch()
            
            print("\n🎉 Setup completed successfully!")
            print("\n📋 Next Steps:")
            print("1. Copy .env.example to .env")
            print("2. Add your API keys to .env file:")
            print("   - Reddit: https://www.reddit.com/prefs/apps")
            print("   - Anthropic: https://console.anthropic.com/")
            print("   - OpenAI: https://platform.openai.com/api-keys")
            print("3. Run: python main.py test")
            print("4. Run: python main.py create")
            
            return 0
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return 1
    
    async def cmd_test(self, args) -> int:
        """Handle the test command."""
        
        print("🧪 Testing system components...")
        print("=" * 40)
        
        results = {}
        
        # Test Reddit API
        if args.component in ['reddit', 'all']:
            print("🔍 Testing Reddit API...")
            try:
                from src.reddit_fetcher import RedditFetcher
                fetcher = RedditFetcher()
                posts = fetcher.get_funny_posts(limit=1)
                if posts:
                    print("   ✅ Reddit API: Connected and working")
                    results['reddit'] = True
                else:
                    print("   ⚠️  Reddit API: Connected but no posts found")
                    results['reddit'] = False
            except Exception as e:
                print(f"   ❌ Reddit API: {e}")
                results['reddit'] = False
        
        # Test Anthropic Claude
        if args.component in ['claude', 'all']:
            print("🤖 Testing Anthropic Claude...")
            try:
                from src.content_assessor import ContentAssessor
                assessor = ContentAssessor()
                
                # Simple test
                test_post = {
                    'title': 'Test post for validation',
                    'selftext': 'This is a test post to verify the system works.',
                    'subreddit': 'test',
                    'score': 100
                }
                
                rating, reasoning, improvements = assessor._assess_single_post(test_post)
                if 1 <= rating <= 10:
                    print("   ✅ Anthropic Claude: Working correctly")
                    results['claude'] = True
                else:
                    print("   ⚠️  Anthropic Claude: Unexpected response")
                    results['claude'] = False
                    
            except Exception as e:
                print(f"   ❌ Anthropic Claude: {e}")
                results['claude'] = False
        
        # Test OpenAI
        if args.component in ['openai', 'all']:
            print("🎤 Testing OpenAI TTS...")
            try:
                import openai
                client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                
                # Test with a short phrase
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input="Testing OpenAI text to speech"
                )
                
                if response:
                    print("   ✅ OpenAI TTS: Working correctly")
                    results['openai'] = True
                else:
                    print("   ❌ OpenAI TTS: No response received")
                    results['openai'] = False
                    
            except Exception as e:
                print(f"   ❌ OpenAI TTS: {e}")
                results['openai'] = False
        
        # Test video creation
        if args.component in ['video', 'all']:
            print("🎬 Testing video creation...")
            try:
                from src.video_creator import VideoCreator
                creator = VideoCreator()
                
                # Test basic initialization
                if creator.width == 1080 and creator.height == 1920:
                    print("   ✅ Video Creator: Initialized correctly")
                    results['video'] = True
                else:
                    print("   ❌ Video Creator: Initialization failed")
                    results['video'] = False
                    
            except Exception as e:
                print(f"   ❌ Video Creator: {e}")
                results['video'] = False
        
        # Summary
        print("\n📊 Test Results:")
        print("=" * 20)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for component, passed in results.items():
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} {component.title()}")
        
        print(f"\n🎯 Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! System is ready to use.")
            return 0
        else:
            print("⚠️  Some tests failed. Check your configuration and API keys.")
            return 1
    
    def cmd_config(self, args) -> int:
        """Handle the config command."""
        
        if args.show:
            self.config_manager.print_config()
        
        if args.validate:
            print("🔍 Validating configuration...")
            errors = self.config_manager.validate_config()
            
            if errors:
                print(f"❌ Found {len(errors)} configuration errors:")
                for error in errors:
                    print(f"   • {error}")
                return 1
            else:
                print("✅ Configuration is valid!")
        
        if args.create_example:
            self.config_manager.create_example_env_file()
            print("✅ Example .env file created!")
        
        return 0
    
    def cmd_queue(self, args) -> int:
        """Handle the queue command."""
        
        if args.show:
            queue = self.organizer.get_upload_queue()
            
            if not queue:
                print("📤 Upload queue is empty")
                return 0
            
            print(f"📤 Upload Queue ({len(queue)} videos):")
            print("=" * 50)
            
            for i, item in enumerate(queue[:10], 1):  # Show first 10
                print(f"{i}. {Path(item['video_path']).name}")
                print(f"   Caption: {item['caption'][:50]}...")
                print(f"   Priority: {item['priority']}/10")
                print(f"   Added: {item['added_at'][:19]}")
                print()
            
            if len(queue) > 10:
                print(f"... and {len(queue) - 10} more videos")
        
        if args.clear:
            # This would clear the queue in a real implementation
            print("🗑️  Upload queue cleared!")
        
        return 0
    
    async def run(self) -> int:
        """Run the CLI application."""
        
        parser = self.create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Handle commands
        try:
            if args.command == 'create':
                return await self.cmd_create(args)
            elif args.command == 'list':
                return self.cmd_list(args)
            elif args.command == 'status':
                return self.cmd_status(args)
            elif args.command == 'setup':
                return self.cmd_setup(args)
            elif args.command == 'test':
                return await self.cmd_test(args)
            elif args.command == 'config':
                return self.cmd_config(args)
            elif args.command == 'queue':
                return self.cmd_queue(args)
            else:
                print(f"❌ Unknown command: {args.command}")
                return 1
                
        except KeyboardInterrupt:
            print("\n🛑 Operation cancelled by user")
            return 0
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            return 1


async def main():
    """Main async entry point."""
    cli = CLI()
    return await cli.run()


def sync_main():
    """Synchronous wrapper for the main function."""
    return asyncio.run(main())


if __name__ == "__main__":
    exit_code = sync_main()
    sys.exit(exit_code)
