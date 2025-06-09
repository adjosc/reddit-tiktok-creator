"""
Component Tests for Reddit to TikTok Video Creator

Tests individual components to ensure they work correctly.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables for testing
load_dotenv()

# Test data
SAMPLE_REDDIT_POST = {
    'id': 'test123',
    'title': 'TIFU by accidentally sending my boss a meme instead of my resignation letter',
    'selftext': 'So this happened yesterday and I\'m still cringing. I was planning to quit my job and had typed up a professional resignation letter. At the same time, I was texting my friend a hilarious meme about office life. Guess which one I accidentally sent to my boss? Yep, the meme. He replied asking if this was my way of telling him I quit. I had to send the actual letter after that. Most awkward resignation ever.',
    'subreddit': 'tifu',
    'score': 1250,
    'upvote_ratio': 0.95,
    'url': 'https://reddit.com/r/tifu/test123',
    'created_utc': 1234567890,
    'num_comments': 89,
    'author': 'testuser',
    'total_length': 150,
    'fetched_at': '2024-01-01T00:00:00'
}

SAMPLE_ASSESSED_POST = {
    **SAMPLE_REDDIT_POST,
    'humor_rating': 8.5,
    'assessment_reasoning': 'Relatable workplace humor with good storytelling structure',
    'suggested_improvements': 'Could add more dramatic pauses for TTS delivery'
}


class TestRedditFetcher:
    """Test the Reddit content fetcher."""
    
    @pytest.fixture
    def reddit_fetcher(self):
        """Create a reddit fetcher instance for testing."""
        from reddit_fetcher import RedditFetcher
        return RedditFetcher()
    
    def test_initialization(self, reddit_fetcher):
        """Test that Reddit fetcher initializes correctly."""
        assert reddit_fetcher.reddit is not None
        assert hasattr(reddit_fetcher, 'reddit')
    
    def test_text_cleaning(self, reddit_fetcher):
        """Test text cleaning functionality."""
        dirty_text = "**Bold text** with *italics* and [link](url) and ~~strikethrough~~"
        clean_text = reddit_fetcher._clean_text_for_tts(dirty_text)
        
        assert "**" not in clean_text
        assert "*" not in clean_text
        assert "[" not in clean_text
        assert "~~" not in clean_text
        assert "Bold text" in clean_text
    
    def test_content_filtering(self, reddit_fetcher):
        """Test content appropriateness filtering."""
        inappropriate_text = "This contains nsfw content and violence"
        assert reddit_fetcher._contains_inappropriate_content(inappropriate_text) == True
        
        appropriate_text = "This is a funny and clean story"
        assert reddit_fetcher._contains_inappropriate_content(appropriate_text) == False
    
    @patch('praw.Reddit')
    def test_post_extraction(self, mock_reddit, reddit_fetcher):
        """Test post data extraction."""
        # Mock post object
        mock_post = Mock()
        mock_post.id = 'test123'
        mock_post.title = 'Test Title'
        mock_post.selftext = 'Test content'
        mock_post.score = 100
        mock_post.subreddit.display_name = 'test'
        mock_post.created_utc = 1234567890
        mock_post.num_comments = 10
        mock_post.author = 'testuser'
        mock_post.upvote_ratio = 0.9
        mock_post.permalink = '/r/test/test123'
        
        result = reddit_fetcher._extract_post_data(mock_post)
        
        assert result['id'] == 'test123'
        assert result['title'] == 'Test Title'
        assert result['subreddit'] == 'test'
        assert result['score'] == 100


class TestContentAssessor:
    """Test the AI content assessor."""
    
    @pytest.fixture
    def content_assessor(self):
        """Create a content assessor instance for testing."""
        from content_assessor import ContentAssessor
        return ContentAssessor()
    
    def test_initialization(self, content_assessor):
        """Test that content assessor initializes correctly."""
        assert content_assessor.client is not None
        assert content_assessor.model == "claude-3-sonnet-20240229"
    
    def test_response_parsing(self, content_assessor):
        """Test parsing of assessment responses."""
        test_response = """
        RATING: 8.5
        REASONING: This is a funny and relatable story with good TikTok potential.
        IMPROVEMENTS: Could add more dramatic pauses for better TTS delivery.
        """
        
        rating, reasoning, improvements = content_assessor._parse_assessment_response(test_response)
        
        assert rating == 8.5
        assert "funny and relatable" in reasoning
        assert "dramatic pauses" in improvements
    
    def test_assessment_prompt_creation(self, content_assessor):
        """Test creation of assessment prompts."""
        prompt = content_assessor._create_assessment_prompt(SAMPLE_REDDIT_POST)
        
        assert "TIFU by accidentally sending" in prompt
        assert "RATING:" in prompt
        assert "REASONING:" in prompt
        assert "IMPROVEMENTS:" in prompt
        assert "r/tifu" in prompt
    
    @patch('anthropic.Anthropic')
    def test_single_post_assessment(self, mock_anthropic, content_assessor):
        """Test assessment of a single post."""
        # Mock the API response
        mock_response = Mock()
        mock_response.content = [Mock(text="RATING: 8.0\nREASONING: Good story\nIMPROVEMENTS: None needed")]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        content_assessor.client = mock_client
        
        rating, reasoning, improvements = content_assessor._assess_single_post(SAMPLE_REDDIT_POST)
        
        assert rating == 8.0
        assert reasoning == "Good story"
        assert improvements == "None needed"


class TestTTSGenerator:
    """Test the text-to-speech generator."""
    
    @pytest.fixture
    def tts_generator(self):
        """Create a TTS generator instance for testing."""
        from tts_generator import TTSGenerator
        return TTSGenerator()
    
    def test_initialization(self, tts_generator):
        """Test that TTS generator initializes correctly."""
        assert tts_generator.openai_client is not None
        assert tts_generator.output_dir.exists()
        assert 'funny_male' in tts_generator.openai_voices
        assert 'story_female' in tts_generator.openai_voices
    
    def test_script_creation(self, tts_generator):
        """Test creation of TikTok-optimized scripts."""
        script = tts_generator.create_engaging_script(SAMPLE_REDDIT_POST, style="engaging")
        
        assert len(script) > 50  # Should have substantial content
        assert len(script) <= 1000  # Should not be too long
        assert "TIFU" not in script  # Should be cleaned
        assert any(word in script.lower() for word in ['story', 'reddit', 'happened'])
    
    def test_voice_selection(self, tts_generator):
        """Test automatic voice selection."""
        voice = tts_generator.get_voice_for_content(SAMPLE_REDDIT_POST)
        
        assert voice in tts_generator.openai_voices.values() or voice in ['funny_male', 'story_male', 'dramatic', 'casual']
    
    def test_text_optimization(self, tts_generator):
        """Test text optimization for TTS."""
        raw_text = "Check this out: user123 said 'lol wtf' and got 50% upvotes!"
        optimized = tts_generator._optimize_for_tts(raw_text)
        
        assert "laugh out loud" in optimized.lower()
        assert "what the heck" in optimized.lower() or "wtf" not in optimized
        assert "percent" in optimized.lower()
    
    def test_intro_generation(self, tts_generator):
        """Test intro generation for different subreddits."""
        tifu_intro = tts_generator._get_intro('tifu', 'engaging')
        funny_intro = tts_generator._get_intro('funny', 'engaging')
        
        assert len(tifu_intro) > 10
        assert len(funny_intro) > 10
        assert tifu_intro != funny_intro  # Should be different for different subreddits


class TestVideoCreator:
    """Test the video creator."""
    
    @pytest.fixture
    def video_creator(self):
        """Create a video creator instance for testing."""
        from video_creator import VideoCreator
        return VideoCreator()
    
    def test_initialization(self, video_creator):
        """Test that video creator initializes correctly."""
        assert video_creator.width == 1080
        assert video_creator.height == 1920
        assert video_creator.fps == 30
        assert video_creator.output_dir.exists()
    
    def test_color_schemes(self, video_creator):
        """Test color scheme selection."""
        tifu_colors = video_creator.color_schemes['tifu']
        default_colors = video_creator.color_schemes['default']
        
        assert 'bg_gradient' in tifu_colors
        assert 'text_color' in tifu_colors
        assert 'accent' in tifu_colors
        assert len(tifu_colors['bg_gradient']) == 2  # Should have two colors for gradient
    
    def test_safe_font_sizing(self, video_creator):
        """Test font size calculation."""
        short_text = "Short title"
        long_text = "This is a very long title that should require smaller font size to fit properly"
        
        short_font = video_creator._get_safe_font_size(short_text, 800)
        long_font = video_creator._get_safe_font_size(long_text, 800)
        
        assert long_font <= short_font  # Longer text should use smaller font


class TestVideoOrganizer:
    """Test the video organizer."""
    
    @pytest.fixture
    def video_organizer(self):
        """Create a video organizer instance for testing."""
        from video_organizer import VideoOrganizer
        return VideoOrganizer()
    
    def test_initialization(self, video_organizer):
        """Test that video organizer initializes correctly."""
        assert video_organizer.output_dir.exists()
        assert video_organizer.ready_dir.exists()
        assert video_organizer.uploaded_dir.exists()
        assert video_organizer.archive_dir.exists()
    
    def test_caption_generation(self, video_organizer):
        """Test TikTok caption generation."""
        caption = video_organizer._generate_caption(SAMPLE_REDDIT_POST)
        
        assert len(caption) > 20
        assert 'tifu' in caption.lower() or 'reddit' in caption.lower()
        assert len(caption) <= 150  # TikTok caption length limit
    
    def test_hashtag_generation(self, video_organizer):
        """Test hashtag generation."""
        hashtags = video_organizer._generate_hashtags(SAMPLE_REDDIT_POST)
        
        assert len(hashtags) > 5
        assert len(hashtags) <= 15  # TikTok hashtag limit
        assert 'reddit' in hashtags
        assert 'tifu' in hashtags
        assert all(isinstance(tag, str) for tag in hashtags)
    
    def test_performance_prediction(self, video_organizer):
        """Test performance prediction algorithm."""
        prediction = video_organizer._predict_performance(SAMPLE_ASSESSED_POST)
        
        assert 'predicted_views' in prediction
        assert 'predicted_likes' in prediction
        assert 'confidence_score' in prediction
        assert prediction['predicted_views'] > 0
        assert 0 <= prediction['confidence_score'] <= 100
    
    def test_audience_determination(self, video_organizer):
        """Test target audience determination."""
        audiences = video_organizer._determine_target_audience(SAMPLE_REDDIT_POST)
        
        assert len(audiences) > 0
        assert all(isinstance(audience, str) for audience in audiences)
    
    def test_content_categorization(self, video_organizer):
        """Test content categorization."""
        category = video_organizer._categorize_content(SAMPLE_REDDIT_POST)
        
        assert isinstance(category, str)
        assert len(category) > 0


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mocked components for integration testing."""
        components = {}
        
        # Mock Reddit Fetcher
        components['reddit_fetcher'] = Mock()
        components['reddit_fetcher'].get_funny_posts.return_value = [SAMPLE_REDDIT_POST]
        
        # Mock Content Assessor
        components['content_assessor'] = Mock()
        components['content_assessor'].assess_humor_quality.return_value = [SAMPLE_ASSESSED_POST]
        
        # Mock TTS Generator
        components['tts_generator'] = Mock()
        components['tts_generator'].create_engaging_script.return_value = "Test script content"
        components['tts_generator'].get_voice_for_content.return_value = "funny_male"
        components['tts_generator'].generate_with_fallback = AsyncMock(return_value="/path/to/audio.mp3")
        
        # Mock Video Creator
        components['video_creator'] = Mock()
        components['video_creator'].create_tiktok_video.return_value = "/path/to/video.mp4"
        
        # Mock Video Organizer
        components['video_organizer'] = Mock()
        components['video_organizer'].save_video_metadata.return_value = {"test": "metadata"}
        
        return components
    
    def test_agent_state_flow(self, mock_components):
        """Test that agent state flows correctly through workflow."""
        from main_agent import AgentState
        
        # Test state creation
        initial_state = AgentState(
            posts=[],
            selected_post={},
            optimized_script="",
            audio_path="",
            video_path="",
            metadata={},
            creation_status="starting",
            error_message="",
            creation_stats={}
        )
        
        assert initial_state['creation_status'] == "starting"
        assert initial_state['posts'] == []
        
        # Test state updates
        initial_state['posts'] = [SAMPLE_REDDIT_POST]
        initial_state['selected_post'] = SAMPLE_ASSESSED_POST
        
        assert len(initial_state['posts']) == 1
        assert initial_state['selected_post']['humor_rating'] == 8.5


# Async mock for testing async functions
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


# Test configuration and utilities
@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        'subreddits': ['test'],
        'post_limit': 5,
        'min_humor_rating': 6.0,
        'script_style': 'engaging',
        'video_style': 'modern'
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory for testing."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


# Performance and load tests
class TestPerformance:
    """Performance tests for critical components."""
    
    def test_text_cleaning_performance(self):
        """Test that text cleaning performs well with large content."""
        from reddit_fetcher import RedditFetcher
        fetcher = RedditFetcher()
        
        # Large text sample
        large_text = "**Bold text** " * 1000 + "Regular text " * 1000
        
        import time
        start_time = time.time()
        cleaned = fetcher._clean_text_for_tts(large_text)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # Less than 1 second
        assert len(cleaned) > 0
    
    def test_batch_processing(self):
        """Test batch processing performance."""
        from content_assessor import ContentAssessor
        
        # Mock multiple posts
        posts = [SAMPLE_REDDIT_POST.copy() for _ in range(10)]
        
        # This would normally test actual API calls, but we'll test the structure
        assessor = ContentAssessor()
        assert hasattr(assessor, 'assess_humor_quality')
        assert callable(assessor.assess_humor_quality)


# Utility functions for tests
def create_test_audio_file(path: str, duration: float = 5.0):
    """Create a test audio file for video creation tests."""
    # This would create an actual audio file in a real test environment
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).touch()
    return path


def create_test_video_file(path: str):
    """Create a test video file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).touch()
    return path


# Error handling tests
class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_missing_api_keys(self):
        """Test handling of missing API keys."""
        # Temporarily remove API key
        original_key = os.environ.get('ANTHROPIC_API_KEY')
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']
        
        try:
            from content_assessor import ContentAssessor
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ContentAssessor()
        finally:
            # Restore API key
            if original_key:
                os.environ['ANTHROPIC_API_KEY'] = original_key
    
    def test_invalid_post_data(self):
        """Test handling of invalid post data."""
        from video_organizer import VideoOrganizer
        organizer = VideoOrganizer()
        
        # Test with missing required fields
        invalid_post = {'title': 'Test'}  # Missing required fields
        
        # Should handle gracefully
        try:
            caption = organizer._generate_caption(invalid_post)
            assert isinstance(caption, str)
        except Exception as e:
            # Should not crash, but may have specific error handling
            assert "subreddit" in str(e).lower() or isinstance(e, KeyError)


if __name__ == "__main__":
    """Run tests when script is executed directly."""
    
    print("🧪 Running Reddit to TikTok Video Creator Tests...")
    
    # Check if required packages are available
    try:
        import pytest
        print("✅ pytest found, running full test suite...")
        
        # Run pytest with verbose output
        exit_code = pytest.main([
            __file__,
            "-v",
            "--tb=short",
            "--color=yes"
        ])
        
        if exit_code == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
    except ImportError:
        print("⚠️  pytest not found, running basic tests...")
        
        # Run basic tests without pytest
        test_runner = TestRedditFetcher()
        test_runner.test_text_cleaning(None)  # This would need proper setup
        
        print("✅ Basic tests completed!")
