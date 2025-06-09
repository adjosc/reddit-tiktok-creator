# Reddit to TikTok Video Creator

An intelligent agent that automatically discovers funny Reddit content and transforms it into engaging TikTok-ready videos using AI-powered content assessment, text-to-speech, and automated video creation. Videos are created locally for manual review and upload.

## Features

- **Automated Content Discovery**: Scrapes multiple Reddit communities for viral content
- **AI Content Assessment**: Uses Anthropic Claude to evaluate humor quality and TikTok potential
- **Professional TTS**: OpenAI's advanced text-to-speech with multiple voice options
- **TikTok-Optimized Videos**: Creates 9:16 videos with engaging visuals and animations
- **Smart Organization**: Automatically organizes videos with metadata for easy management
- **Manual Upload Ready**: Provides suggested captions and hashtags for easy TikTok posting
- **LangGraph Orchestration**: Multi-step agentic workflow with error handling

## System Architecture

```
Reddit API → Content Filter → AI Assessment → TTS Generation → Video Creation → Local Storage
     ↓              ↓             ↓              ↓              ↓            ↓
 RedditFetcher → ContentAssessor → Claude → TTSGenerator → VideoCreator → VideoOrganizer
```

## Prerequisites

- Python 3.8+
- VS Code with Python extension
- Git
- Active accounts: Reddit, Anthropic, OpenAI

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/reddit-tiktok-agent.git
cd reddit-tiktok-agent
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Reddit API (Get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditVideoCreator/1.0

# AI Services
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Video Output Settings
OUTPUT_DIRECTORY=./output_videos
VIDEO_QUALITY=high

# Optional: Debugging
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Test Installation

```bash
python test_components.py
```

### 4. Run the Agent

```bash
python main_agent.py
```

## Project Structure

```
reddit-tiktok-creator/
├── src/                        # Core source code
│   ├── __init__.py             # Package initialization
│   ├── main_agent.py           # Main LangGraph workflow orchestrator
│   ├── reddit_fetcher.py       # Reddit API integration & content filtering
│   ├── content_assessor.py     # AI content evaluation using Claude
│   ├── tts_generator.py        # Text-to-speech generation (OpenAI/Edge)
│   ├── video_creator.py        # Video creation and editing with MoviePy
│   └── video_organizer.py      # Video organization and metadata management
├── config/                     # Configuration management
│   └── settings.py             # Centralized configuration system
├── tests/                      # Test suite
│   ├── test_components.py      # Component unit tests
│   └── test_integration.py     # End-to-end integration tests
├── output_videos/              # Generated content (auto-created)
│   ├── ready_to_upload/        # Videos ready for TikTok upload
│   ├── uploaded/               # Successfully uploaded videos
│   ├── archive/                # Archived old videos
│   ├── audio/                  # Generated TTS audio files
│   ├── logs/                   # System and error logs
│   └── video_metadata.json     # Video metadata and upload suggestions
├── assets/                     # Static assets (auto-created)
│   ├── fonts/                  # Custom fonts for video text
│   └── backgrounds/            # Video background templates
├── main.py                     # Main CLI entry point
├── quick_start.py              # Guided setup for new users
├── scheduler.py                # Automated video creation scheduler
├── setup.py                    # Package installation script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
├── .gitignore                  # Git ignore rules
└── README.md                   # This documentation
```

## Configuration

### Reddit API Setup

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the form:
   - **Name**: `reddit-video-creator`
   - **Description**: `Automated content discovery for video creation`
   - **Redirect URI**: `http://localhost:8080`
5. Copy the client ID (under the app name) and secret

### Video Output Configuration

The system creates TikTok-ready videos with:
- **Aspect Ratio**: 9:16 (1080x1920)
- **Format**: MP4 with H.264 encoding
- **Audio**: AAC, optimized for mobile viewing
- **Duration**: Automatically adjusted based on content (15-60 seconds)
- **Quality**: HD with mobile-optimized compression

### Content Filtering Configuration

Edit `config/settings.py` to customize content selection:

```python
CONTENT_FILTERS = {
    'min_score': 100,           # Minimum Reddit upvotes
    'max_length': 1000,         # Maximum character count
    'min_humor_rating': 7,      # AI humor assessment threshold
    'subreddits': [             # Target subreddits
        'funny', 'memes', 'tifu', 
        'askreddit', 'wholesomememes'
    ],
    'excluded_words': [         # Content to avoid
        'politics', 'nsfw', 'controversial'
    ]
}
```

## Usage Examples

### Command Line Interface

The system provides a comprehensive CLI for all operations:

```bash
# Basic video creation
python main.py create                    # Create one video with default settings
python main.py create --count 3          # Create 3 videos in batch
python main.py create --preset high_quality  # Use high-quality preset

# Advanced creation options
python main.py create --subreddits funny tifu memes --min-rating 8.0
python main.py create --style dynamic --voice funny_male
python main.py create --count 5 --preset family_friendly

# Video management
python main.py list                      # List created videos
python main.py list --limit 20           # Show last 20 videos
python main.py status                    # Show system status and statistics

# Configuration
python main.py config --show             # Display current configuration
python main.py config --validate         # Validate configuration
python main.py config --create-example   # Create example .env file

# Testing and setup
python main.py setup                     # Run initial setup
python main.py test                      # Test all components
python main.py test --component reddit   # Test specific component

# Upload queue management
python main.py queue --show              # Show videos ready for upload
python main.py queue --clear             # Clear upload queue
```

### Programmatic Usage

```python
import asyncio
from src.main_agent import RedditTikTokAgent

async def create_video():
    # Initialize with custom config
    config = {
        'subreddits': ['funny', 'tifu'],
        'min_humor_rating': 8.0,
        'video_style': 'modern',
        'voice_style': 'funny_male'
    }
    
    agent = RedditTikTokAgent(config)
    result = await agent.run()
    
    if result['creation_status'] == 'success':
        print(f"Video created: {result['video_path']}")
        return result['video_path']
    else:
        print(f"Failed: {result['error_message']}")

# Run the agent
video_path = asyncio.run(create_video())
```

### Batch Video Creation

```python
from src.main_agent import RedditTikTokAgent

# Create multiple videos with different settings
agent = RedditTikTokAgent()

# High-quality batch
results = agent.run_batch(count=3, min_humor_rating=8.5, video_style='dynamic')

# Show results
for i, result in enumerate(results, 1):
    status = result['creation_status']
    print(f"Video {i}: {status}")
```

### Automated Scheduling

```bash
# Start automated video creation
python scheduler.py start                # Run continuously
python scheduler.py once                 # Create one video now
python scheduler.py status               # Check scheduler status

# With custom configuration
python scheduler.py start --preset high_volume
```

### Advanced Configuration

```python
from config.settings import ConfigManager, load_preset

# Load and customize configuration
config_manager = ConfigManager()
config = config_manager.get_agent_config()

# Apply preset and overrides
preset_config = load_preset('high_quality')
config.update(preset_config)
config['subreddits'] = ['tifu', 'confession']

# Use with agent
agent = RedditTikTokAgent(config)
```

## Testing

### Run Component Tests

```bash
# Test individual components
python -m pytest tests/test_components.py -v

# Test Reddit fetching
python tests/test_reddit_fetcher.py

# Test TTS generation
python tests/test_tts_generator.py

# Test video creation
python tests/test_video_creator.py
```

### Integration Testing

```bash
# Full workflow test (without TikTok upload)
python tests/test_integration.py

# Test with sample data
python tests/test_with_samples.py
```

## Automation & Scheduling

### Intelligent Scheduler

The built-in scheduler creates videos automatically with smart timing and quality control:

```bash
# Start continuous automated creation
python scheduler.py start

# Create one video immediately
python scheduler.py once

# Check scheduler status and statistics
python scheduler.py status

# View scheduler configuration
python scheduler.py config
```

### Scheduler Features

- **Smart Timing**: Creates videos during optimal hours
- **Quality Control**: Only creates high-rated content
- **Quiet Hours**: Respects sleep/work schedules
- **Daily Limits**: Prevents spam with configurable limits
- **Error Recovery**: Automatically retries failed attempts
- **Performance Tracking**: Monitors success rates and quality

### Configuration Options

Set these in your `.env` file:

```env
# Scheduling settings
SCHEDULE_INTERVAL_HOURS=4              # Create videos every 4 hours
SCHEDULE_MAX_VIDEOS_PER_DAY=6          # Maximum daily videos
SCHEDULE_MIN_GAP_MINUTES=30            # Minimum time between videos

# Timing preferences
SCHEDULE_PEAK_HOURS=12-14,19-21        # Higher quality during peak times
SCHEDULE_QUIET_HOURS=23-6              # No creation during quiet hours
SCHEDULE_WEEKEND_ENABLED=true          # Enable weekend creation

# Quality settings
SCHEDULE_SKIP_LOW_QUALITY=true         # Skip videos below threshold
CONTENT_MIN_HUMOR_RATING=7.0           # Minimum quality score
```

### Manual Control

```bash
# Run scheduler with custom settings
SCHEDULE_INTERVAL_HOURS=2 python scheduler.py start

# One-time creation with specific config
python main.py create --preset high_quality --count 3
```

### Cron Job Setup

For production deployment:

```bash
# Edit crontab
crontab -e

# Add scheduled execution (every 4 hours)
0 */4 * * * cd /path/to/reddit-tiktok-creator && python scheduler.py once

# Or run continuously as a service
@reboot cd /path/to/reddit-tiktok-creator && python scheduler.py start
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "Daily" with repeat every 4 hours
4. Set action: Start `python.exe` with argument `scheduler.py once`
5. Set start in: Your project directory

### Monitoring

```bash
# View detailed logs
tail -f output_videos/logs/scheduler.log

# Check system performance
python main.py status

# View creation statistics
python scheduler.py status
```

## Monitoring & Analytics

### View Creation Logs

```bash
tail -f output_videos/logs/agent.log
```

### Performance Metrics

The system tracks:
- Posts fetched per run
- Content assessment scores
- Video creation success rate
- Audio generation time
- Processing time per video
- Total videos created

### Video Management

```python
# View video metadata
import json

with open('output_videos/video_metadata.json', 'r') as f:
    videos = json.load(f)

for video in videos[-5:]:  # Last 5 videos
    print(f"Title: {video['reddit_data']['title']}")
    print(f"Rating: {video['reddit_data']['humor_rating']}")
    print(f"Caption: {video['suggested_caption']}")
    print("---")
```

### Dashboard (Optional)

Use Lovable.dev to create a monitoring dashboard:

```bash
# After setting up Lovable account
npm install -g @lovable/cli
lovable init video-dashboard
```

## Safety & Best Practices

### Content Guidelines

- **Always credit sources**: Include subreddit and "via Reddit" in generated captions
- **Respect copyright**: Only use text-based posts, avoid copyrighted media
- **Review before uploading**: Check videos for appropriateness before posting
- **Monitor content**: Implement manual review for sensitive topics

### Rate Limiting

```python
# Built-in rate limiting
REDDIT_REQUESTS_PER_MINUTE = 60
OPENAI_REQUESTS_PER_MINUTE = 50
VIDEO_CREATION_DELAY = 30  # Seconds between videos
```

### Error Handling

- Automatic retry logic for API failures
- Graceful degradation when services are unavailable
- Comprehensive logging for debugging
- Backup content sources

### Manual Upload Workflow

1. **Review created videos** in `output_videos/` directory
2. **Check metadata file** for suggested captions and hashtags
3. **Upload manually to TikTok** using provided suggestions
4. **Track performance** to improve content selection

## Security Considerations

- Store API keys in `.env` file (never commit to git)
- Use environment variables in production
- Regularly rotate API keys
- Monitor for unusual account activity
- Consider using OAuth for TikTok when available

## Troubleshooting

### Common Issues

**Reddit API Authentication Failed**
```bash
# Check credentials
python -c "from src.reddit_fetcher import RedditFetcher; f = RedditFetcher(); print('Connected!')"
```

**TTS Generation Errors**
```bash
# Test OpenAI connection
python -c "import openai; print(openai.Model.list())"
```

**Video Creation Problems**
```bash
# Check MoviePy installation
python -c "from moviepy.editor import *; print('MoviePy working!')"
```

**File Permission Issues**
```bash
# Ensure output directory is writable
mkdir -p output_videos
chmod 755 output_videos
```

### Debug Mode

Enable verbose logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python main_agent.py
```

### Video Quality Issues

- **Low resolution**: Check `VIDEO_QUALITY` setting in .env
- **Audio sync**: Ensure proper audio file encoding
- **Large file sizes**: Adjust compression settings in `video_creator.py`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/
flake8 src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and personal use. Users are responsible for:
- Complying with Reddit's Terms of Service
- Following TikTok's Community Guidelines when uploading
- Respecting copyright and intellectual property
- Reviewing content before manual upload
- Using the tool ethically and responsibly

Videos created by this tool should be reviewed before uploading to any social media platform.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/reddit-tiktok-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/reddit-tiktok-agent/discussions)
- **Email**: your-email@example.com

## Acknowledgments

- Reddit API for content access
- Anthropic Claude for content assessment
- OpenAI for high-quality TTS
- LangGraph for workflow orchestration
- MoviePy for video processing
- The open-source community
