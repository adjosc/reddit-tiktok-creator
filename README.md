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
reddit-video-creator/
├── src/
│   ├── __init__.py
│   ├── main_agent.py           # Main LangGraph workflow
│   ├── reddit_fetcher.py       # Reddit API integration
│   ├── content_assessor.py     # AI content evaluation
│   ├── tts_generator.py        # Text-to-speech generation
│   ├── video_creator.py        # Video creation and editing
│   └── video_organizer.py      # Video organization and metadata
├── tests/
│   ├── test_components.py      # Component testing
│   └── test_integration.py     # End-to-end testing
├── output_videos/
│   ├── [generated videos]      # Created video files
│   ├── video_metadata.json     # Video metadata and captions
│   └── audio/                  # Generated TTS files
├── assets/
│   ├── fonts/                  # Custom fonts for videos
│   └── backgrounds/            # Video background templates
├── config/
│   └── settings.py             # Configuration management
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── scheduler.py                # Automated video creation
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

### Basic Video Creation

```python
import asyncio
from src.main_agent import RedditTikTokAgent

async def main():
    agent = RedditTikTokAgent()
    result = await agent.run()
    print(f"Status: {result['creation_status']}")
    print(f"Video: {result['video_path']}")

asyncio.run(main())
```

### View Created Videos

```python
from src.video_organizer import VideoOrganizer

# List all created videos with metadata
organizer = VideoOrganizer()
organizer.list_created_videos()
```

### Custom Content Selection

```python
from src.reddit_fetcher import RedditFetcher
from src.content_assessor import ContentAssessor

# Fetch from specific subreddit
fetcher = RedditFetcher()
posts = fetcher.get_funny_posts(subreddits=['programmerhumor'], limit=10)

# Assess with custom criteria
assessor = ContentAssessor()
top_posts = assessor.assess_humor_quality(posts, min_rating=8)
```

### Manual Video Creation

```python
from src.video_creator import VideoCreator
from src.tts_generator import TTSGenerator

# Create custom video
tts = TTSGenerator()
video_creator = VideoCreator()

# Generate audio
await tts.generate_speech_openai("Your funny text here", "audio.mp3")

# Create video
video_path = video_creator.create_tiktok_video(post_data, "audio.mp3")
print(f"Video created: {video_path}")
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

### Continuous Video Creation

```bash
# Create videos every 4 hours
python scheduler.py
```

### Batch Video Creation

```python
# Create multiple videos in one run
import asyncio
from src.main_agent import RedditTikTokAgent

async def create_batch():
    agent = RedditTikTokAgent()
    
    for i in range(5):  # Create 5 videos
        print(f"Creating video {i+1}/5...")
        result = await agent.run()
        print(f"Video {i+1} status: {result['creation_status']}")

asyncio.run(create_batch())
```

### Cron Job Setup (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add line to create videos every 4 hours
0 */4 * * * cd /path/to/reddit-video-creator && python main_agent.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily" and repeat every 4 hours
4. Set action to start `python.exe` with argument `main_agent.py`

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

## License

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
