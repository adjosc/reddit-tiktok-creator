"""
Configuration Settings for Reddit to TikTok Video Creator

Centralized configuration management for the entire system.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class RedditConfig:
    """Reddit API configuration."""
    subreddits: List[str]
    post_limit: int
    time_filter: str  # 'hour', 'day', 'week', 'month', 'year', 'all'
    min_score: int
    max_content_length: int
    min_content_length: int
    excluded_keywords: List[str]

@dataclass 
class ContentConfig:
    """Content assessment configuration."""
    min_humor_rating: float
    assessment_batch_size: int
    enable_batch_comparison: bool
    target_audience: str
    content_safety_level: str  # 'strict', 'moderate', 'relaxed'

@dataclass
class TTSConfig:
    """Text-to-speech configuration."""
    preferred_service: str  # 'openai' or 'edge'
    voice_style: Optional[str]  # Auto-detect if None
    speech_speed: float
    enable_voice_variation: bool
    script_style: str  # 'engaging', 'dramatic', 'casual', 'story'

@dataclass
class VideoConfig:
    """Video creation configuration."""
    style: str  # 'modern', 'minimal', 'dynamic', 'story'
    quality: str  # 'high', 'medium', 'low'
    enable_animations: bool
    background_type: str  # 'gradient', 'solid', 'particles'
    text_overlay: bool
    watermark: bool

@dataclass
class OutputConfig:
    """Output and organization configuration."""
    output_directory: str
    auto_organize: bool
    generate_thumbnails: bool
    save_audio_files: bool
    cleanup_temp_files: bool
    backup_original_posts: bool

@dataclass
class SystemConfig:
    """System-level configuration."""
    max_concurrent_videos: int
    retry_attempts: int
    timeout_seconds: int
    enable_logging: bool
    log_level: str
    enable_stats_tracking: bool


class ConfigManager:
    """Manages configuration settings for the entire system."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to custom config file
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and defaults."""
        
        # Reddit Configuration
        self.reddit = RedditConfig(
            subreddits=self._get_list_env('REDDIT_SUBREDDITS', [
                'funny', 'tifu', 'confession', 'wholesome', 'memes',
                'askreddit', 'showerthoughts', 'unpopularopinion'
            ]),
            post_limit=int(os.getenv('REDDIT_POST_LIMIT', '20')),
            time_filter=os.getenv('REDDIT_TIME_FILTER', 'day'),
            min_score=int(os.getenv('REDDIT_MIN_SCORE', '100')),
            max_content_length=int(os.getenv('REDDIT_MAX_CONTENT_LENGTH', '1500')),
            min_content_length=int(os.getenv('REDDIT_MIN_CONTENT_LENGTH', '100')),
            excluded_keywords=self._get_list_env('REDDIT_EXCLUDED_KEYWORDS', [
                'nsfw', 'politics', 'suicide', 'death', 'illegal'
            ])
        )
        
        # Content Assessment Configuration
        self.content = ContentConfig(
            min_humor_rating=float(os.getenv('CONTENT_MIN_HUMOR_RATING', '7.0')),
            assessment_batch_size=int(os.getenv('CONTENT_BATCH_SIZE', '10')),
            enable_batch_comparison=os.getenv('CONTENT_ENABLE_COMPARISON', 'true').lower() == 'true',
            target_audience=os.getenv('CONTENT_TARGET_AUDIENCE', 'general'),
            content_safety_level=os.getenv('CONTENT_SAFETY_LEVEL', 'moderate')
        )
        
        # TTS Configuration
        self.tts = TTSConfig(
            preferred_service=os.getenv('TTS_PREFERRED_SERVICE', 'openai'),
            voice_style=os.getenv('TTS_VOICE_STYLE'),  # None = auto-detect
            speech_speed=float(os.getenv('TTS_SPEECH_SPEED', '1.1')),
            enable_voice_variation=os.getenv('TTS_VOICE_VARIATION', 'false').lower() == 'true',
            script_style=os.getenv('TTS_SCRIPT_STYLE', 'engaging')
        )
        
        # Video Configuration
        self.video = VideoConfig(
            style=os.getenv('VIDEO_STYLE', 'modern'),
            quality=os.getenv('VIDEO_QUALITY', 'high'),
            enable_animations=os.getenv('VIDEO_ANIMATIONS', 'true').lower() == 'true',
            background_type=os.getenv('VIDEO_BACKGROUND_TYPE', 'gradient'),
            text_overlay=os.getenv('VIDEO_TEXT_OVERLAY', 'true').lower() == 'true',
            watermark=os.getenv('VIDEO_WATERMARK', 'true').lower() == 'true'
        )
        
        # Output Configuration
        self.output = OutputConfig(
            output_directory=os.getenv('OUTPUT_DIRECTORY', './output_videos'),
            auto_organize=os.getenv('OUTPUT_AUTO_ORGANIZE', 'true').lower() == 'true',
            generate_thumbnails=os.getenv('OUTPUT_GENERATE_THUMBNAILS', 'false').lower() == 'true',
            save_audio_files=os.getenv('OUTPUT_SAVE_AUDIO', 'true').lower() == 'true',
            cleanup_temp_files=os.getenv('OUTPUT_CLEANUP_TEMP', 'true').lower() == 'true',
            backup_original_posts=os.getenv('OUTPUT_BACKUP_POSTS', 'true').lower() == 'true'
        )
        
        # System Configuration
        self.system = SystemConfig(
            max_concurrent_videos=int(os.getenv('SYSTEM_MAX_CONCURRENT', '1')),
            retry_attempts=int(os.getenv('SYSTEM_RETRY_ATTEMPTS', '3')),
            timeout_seconds=int(os.getenv('SYSTEM_TIMEOUT', '300')),
            enable_logging=os.getenv('SYSTEM_ENABLE_LOGGING', 'true').lower() == 'true',
            log_level=os.getenv('SYSTEM_LOG_LEVEL', 'INFO'),
            enable_stats_tracking=os.getenv('SYSTEM_ENABLE_STATS', 'true').lower() == 'true'
        )
    
    def _get_list_env(self, key: str, default: List[str]) -> List[str]:
        """Get list from environment variable."""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(',')]
        return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'reddit': asdict(self.reddit),
            'content': asdict(self.content),
            'tts': asdict(self.tts),
            'video': asdict(self.video),
            'output': asdict(self.output),
            'system': asdict(self.system)
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get configuration formatted for the main agent."""
        return {
            # Reddit settings
            'subreddits': self.reddit.subreddits,
            'post_limit': self.reddit.post_limit,
            'time_filter': self.reddit.time_filter,
            
            # Content settings
            'min_humor_rating': self.content.min_humor_rating,
            'selection_strategy': 'highest_rated',
            
            # TTS settings
            'script_style': self.tts.script_style,
            'voice_style': self.tts.voice_style,
            
            # Video settings
            'video_style': self.video.style,
            'video_quality': self.video.quality
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate required environment variables
        required_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET', 
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate paths
        output_path = Path(self.output.output_directory)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create output directory: {e}")
        
        # Validate numeric ranges
        if not 0 < self.content.min_humor_rating <= 10:
            errors.append("min_humor_rating must be between 0 and 10")
        
        if not 0.25 <= self.tts.speech_speed <= 4.0:
            errors.append("TTS speech_speed must be between 0.25 and 4.0")
        
        if self.reddit.post_limit < 1:
            errors.append("post_limit must be at least 1")
        
        # Validate choices
        valid_time_filters = ['hour', 'day', 'week', 'month', 'year', 'all']
        if self.reddit.time_filter not in valid_time_filters:
            errors.append(f"time_filter must be one of: {valid_time_filters}")
        
        valid_video_styles = ['modern', 'minimal', 'dynamic', 'story']
        if self.video.style not in valid_video_styles:
            errors.append(f"video_style must be one of: {valid_video_styles}")
        
        valid_script_styles = ['engaging', 'dramatic', 'casual', 'story']
        if self.tts.script_style not in valid_script_styles:
            errors.append(f"script_style must be one of: {valid_script_styles}")
        
        return errors
    
    def print_config(self):
        """Print current configuration in a readable format."""
        
        print("\n" + "="*50)
        print("🔧 REDDIT TO TIKTOK VIDEO CREATOR CONFIG")
        print("="*50)
        
        print(f"\n📡 Reddit Settings:")
        print(f"   Subreddits: {', '.join(self.reddit.subreddits[:5])}{'...' if len(self.reddit.subreddits) > 5 else ''}")
        print(f"   Post Limit: {self.reddit.post_limit}")
        print(f"   Time Filter: {self.reddit.time_filter}")
        print(f"   Min Score: {self.reddit.min_score}")
        
        print(f"\n🤖 Content Assessment:")
        print(f"   Min Humor Rating: {self.content.min_humor_rating}/10")
        print(f"   Target Audience: {self.content.target_audience}")
        print(f"   Safety Level: {self.content.content_safety_level}")
        
        print(f"\n🎤 Text-to-Speech:")
        print(f"   Service: {self.tts.preferred_service}")
        print(f"   Script Style: {self.tts.script_style}")
        print(f"   Speech Speed: {self.tts.speech_speed}x")
        
        print(f"\n🎬 Video Creation:")
        print(f"   Style: {self.video.style}")
        print(f"   Quality: {self.video.quality}")
        print(f"   Animations: {'Enabled' if self.video.enable_animations else 'Disabled'}")
        
        print(f"\n📁 Output Settings:")
        print(f"   Directory: {self.output.output_directory}")
        print(f"   Auto Organize: {'Yes' if self.output.auto_organize else 'No'}")
        print(f"   Save Audio: {'Yes' if self.output.save_audio_files else 'No'}")
        
        print("="*50 + "\n")
    
    def create_example_env_file(self, filepath: str = ".env.example"):
        """Create an example environment file with all configuration options."""
        
        env_content = """# Reddit to TikTok Video Creator Configuration

# =============================================================================
# REQUIRED SETTINGS (Must be configured)
# =============================================================================

# Reddit API Credentials (Get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=RedditVideoCreator/1.0

# AI Service API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# =============================================================================
# OPTIONAL SETTINGS (Defaults will be used if not specified)
# =============================================================================

# Reddit Content Settings
REDDIT_SUBREDDITS=funny,tifu,confession,wholesome,memes
REDDIT_POST_LIMIT=20
REDDIT_TIME_FILTER=day
REDDIT_MIN_SCORE=100
REDDIT_MAX_CONTENT_LENGTH=1500
REDDIT_MIN_CONTENT_LENGTH=100
REDDIT_EXCLUDED_KEYWORDS=nsfw,politics,suicide,death,illegal

# Content Quality Assessment
CONTENT_MIN_HUMOR_RATING=7.0
CONTENT_BATCH_SIZE=10
CONTENT_ENABLE_COMPARISON=true
CONTENT_TARGET_AUDIENCE=general
CONTENT_SAFETY_LEVEL=moderate

# Text-to-Speech Settings
TTS_PREFERRED_SERVICE=openai
TTS_VOICE_STYLE=auto
TTS_SPEECH_SPEED=1.1
TTS_VOICE_VARIATION=false
TTS_SCRIPT_STYLE=engaging

# Video Creation Settings  
VIDEO_STYLE=modern
VIDEO_QUALITY=high
VIDEO_ANIMATIONS=true
VIDEO_BACKGROUND_TYPE=gradient
VIDEO_TEXT_OVERLAY=true
VIDEO_WATERMARK=true

# Output and Organization
OUTPUT_DIRECTORY=./output_videos
OUTPUT_AUTO_ORGANIZE=true
OUTPUT_GENERATE_THUMBNAILS=false
OUTPUT_SAVE_AUDIO=true
OUTPUT_CLEANUP_TEMP=true
OUTPUT_BACKUP_POSTS=true

# System Settings
SYSTEM_MAX_CONCURRENT=1
SYSTEM_RETRY_ATTEMPTS=3
SYSTEM_TIMEOUT=300
SYSTEM_ENABLE_LOGGING=true
SYSTEM_LOG_LEVEL=INFO
SYSTEM_ENABLE_STATS=true

# =============================================================================
# DEBUGGING AND DEVELOPMENT
# =============================================================================

DEBUG=false
LOG_LEVEL=INFO
"""
        
        with open(filepath, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Example environment file created: {filepath}")
        print("📝 Copy this to .env and configure your API keys!")


# Pre-configured setups for different use cases
class PresetConfigs:
    """Pre-configured setups for common use cases."""
    
    @staticmethod
    def high_quality_preset() -> Dict[str, Any]:
        """Configuration for high-quality, carefully curated content."""
        return {
            'reddit': {
                'subreddits': ['tifu', 'confession', 'wholesomememes'],
                'post_limit': 10,
                'min_score': 500,
                'time_filter': 'week'
            },
            'content': {
                'min_humor_rating': 8.5,
                'target_audience': 'quality_focused'
            },
            'tts': {
                'preferred_service': 'openai',
                'script_style': 'dramatic'
            },
            'video': {
                'style': 'dynamic',
                'quality': 'high'
            }
        }
    
    @staticmethod
    def high_volume_preset() -> Dict[str, Any]:
        """Configuration for high-volume content creation."""
        return {
            'reddit': {
                'subreddits': ['funny', 'memes', 'tifu', 'askreddit', 'showerthoughts'],
                'post_limit': 30,
                'min_score': 100,
                'time_filter': 'day'
            },
            'content': {
                'min_humor_rating': 6.5,
                'target_audience': 'broad'
            },
            'tts': {
                'preferred_service': 'edge',
                'script_style': 'casual'
            },
            'video': {
                'style': 'minimal',
                'quality': 'medium'
            }
        }
    
    @staticmethod
    def family_friendly_preset() -> Dict[str, Any]:
        """Configuration for family-friendly content."""
        return {
            'reddit': {
                'subreddits': ['wholesomememes', 'mademesmile', 'aww'],
                'post_limit': 15,
                'min_score': 200,
                'excluded_keywords': ['nsfw', 'politics', 'death', 'violence', 'alcohol', 'drugs']
            },
            'content': {
                'min_humor_rating': 7.0,
                'target_audience': 'family',
                'content_safety_level': 'strict'
            },
            'tts': {
                'script_style': 'wholesome'
            },
            'video': {
                'style': 'cheerful',
                'watermark': True
            }
        }


# Global configuration instance
config_manager = None

def get_config() -> ConfigManager:
    """Get global configuration manager instance."""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager()
    return config_manager

def load_preset(preset_name: str) -> Dict[str, Any]:
    """Load a preset configuration."""
    presets = {
        'high_quality': PresetConfigs.high_quality_preset(),
        'high_volume': PresetConfigs.high_volume_preset(),
        'family_friendly': PresetConfigs.family_friendly_preset()
    }
    
    return presets.get(preset_name, {})


if __name__ == "__main__":
    # Test configuration
    import sys
    
    try:
        # Load and validate configuration
        config = ConfigManager()
        
        print("🔧 Testing Configuration Manager...")
        config.print_config()
        
        # Validate configuration
        errors = config.validate_config()
        if errors:
            print("❌ Configuration Errors:")
            for error in errors:
                print(f"   • {error}")
        else:
            print("✅ Configuration is valid!")
        
        # Create example env file
        config.create_example_env_file()
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        sys.exit(1)
