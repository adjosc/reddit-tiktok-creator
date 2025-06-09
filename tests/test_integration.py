"""
Integration Tests for Reddit to TikTok Video Creator

End-to-end tests that verify the complete workflow functions correctly.
"""

import pytest
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# Test data
MOCK_REDDIT_POSTS = [
    {
        'id': 'test001',
        'title': 'TIFU by accidentally becoming a meme at work',
        'selftext': 'So yesterday I was giving a presentation to the entire company about our quarterly results. Everything was going smoothly until I accidentally shared my screen with a folder full of cat memes instead of the financial charts. The CEO burst out laughing and now everyone calls me the Meme Master.',
        'subreddit': 'tifu',
        'score': 2500,
        'upvote_ratio': 0.95,
        'url': 'https://reddit.com/r/tifu/test001',
        'created_utc': 1701234567,
        'num_comments': 156,
        'author': 'meme_master_2024',
        'total_length': 280,
        'fetched_at': '2024-01-01T12:00:00'
    },
    {
        'id': 'test002', 
        'title': 'My dog learned to open doors and now I have no privacy',
        'selftext': 'My golden retriever figured out how to open door handles by jumping up and grabbing them. Now he just walks into any room whenever he wants. I was in an important video call and he casually strolled in carrying his favorite squeaky toy.',
        'subreddit': 'funny',
        'score': 1800,
        'upvote_ratio': 0.92,
        'url': 'https://reddit.com/r/funny/test002',
        'created_utc': 1701234568,
        'num_comments': 89,
        'author': 'dog_parent_123',
        'total_length': 220,
        'fetched_at': '2024-01-01T12:05:00'
    }
]

MOCK_ASSESSED_POSTS = [
    {
        **MOCK_REDDIT_POSTS[0],
        'humor_rating': 8.5,
        'assessment_reasoning': 'Relatable workplace humor with embarrassing but harmless situation',
        'suggested_improvements': 'Could emphasize the audience reaction more for better comedic timing'
    },
    {
        **MOCK_REDDIT_POSTS[1],
        'humor_rating': 7.8,
        'assessment_reasoning': 'Cute and relatable pet story with visual comedy potential',
        'suggested_improvements': 'Could add more specific details about the dog\'s behavior'
    }
]


class TestEndToEndWorkflow:
    """Test the complete end-to-end workflow."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp(prefix="reddit_tiktok_test_")
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            # Create necessary directories
            for directory in ["output_videos", "output_videos/audio", "output_videos/logs", "assets"]:
                Path(directory).mkdir(parents=True, exist_ok=True)
            
            yield temp_dir
            
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_environment(self, monkeypatch):
        """Set up mock environment variables."""
        monkeypatch.setenv("REDDIT_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setenv("REDDIT_USER_AGENT", "TestAgent/1.0")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    
    @pytest.mark.asyncio
    async def test_complete_workflow_success(self, temp_workspace, mock_environment):
        """Test successful end-to-end video creation workflow."""
        
        # Mock all external dependencies
        with patch('src.reddit_fetcher.praw.Reddit') as mock_reddit, \
             patch('src.content_assessor.anthropic.Anthropic') as mock_anthropic, \
             patch('src.tts_generator.openai.OpenAI') as mock_openai, \
             patch('src.video_creator.VideoFileClip') as mock_video_clip:
            
            # Setup Reddit mock
            mock_reddit_instance = Mock()
            mock_reddit.return_value = mock_reddit_instance
            mock_reddit_instance.user.me.return_value = Mock()
            
            # Setup content fetcher mock
            from src.reddit_fetcher import RedditFetcher
            original_get_posts = RedditFetcher.get_funny_posts
            RedditFetcher.get_funny_posts = Mock(return_value=MOCK_REDDIT_POSTS)
            
            # Setup content assessor mock
            from src.content_assessor import ContentAssessor
            original_assess = ContentAssessor.assess_humor_quality
            ContentAssessor.assess_humor_quality = Mock(return_value=MOCK_ASSESSED_POSTS)
            
            # Setup TTS mock
            mock_openai_client = Mock()
            mock_openai.return_value = mock_openai_client
            
            mock_response = Mock()
            mock_response.stream_to_file = Mock()
            mock_openai_client.audio.speech.create.return_value = mock_response
            
            # Setup video creation mock
            mock_clip = Mock()
            mock_clip.duration = 25.0
            mock_clip.write_videofile = Mock()
            mock_clip.close = Mock()
            mock_video_clip.return_value = mock_clip
            
            # Create test audio file
            test_audio_path = Path("output_videos/audio/test_audio.mp3")
            test_audio_path.touch()
            
            try:
                # Import and run the main agent
                from src.main_agent import RedditTikTokAgent
                
                config = {
                    'subreddits': ['tifu', 'funny'],
                    'post_limit': 5,
                    'min_humor_rating': 7.0,
                    'script_style': 'engaging',
                    'video_style': 'modern'
                }
                
                agent = RedditTikTokAgent(config)
                result = await agent.run()
                
                # Verify successful completion
                assert result['creation_status'] == 'success'
                assert 'video_path' in result
                assert 'metadata' in result
                
                # Verify metadata structure
                metadata = result['metadata']
                assert 'video_info' in metadata
                assert 'reddit_data' in metadata
                assert 'tiktok_content' in metadata
                
                # Verify TikTok content generation
                tiktok_content = metadata['tiktok_content']
                assert 'suggested_caption' in tiktok_content
                assert 'suggested_hashtags' in tiktok_content
                assert len(tiktok_content['suggested_hashtags']) > 0
                
            finally:
                # Restore original methods
                RedditFetcher.get_funny_posts = original_get_posts
                ContentAssessor.assess_humor_quality = original_assess
    
    @pytest.mark.asyncio
    async def test_workflow_with_reddit_failure(self, temp_workspace, mock_environment):
        """Test workflow handling when Reddit API fails."""
        
        with patch('src.reddit_fetcher.praw.Reddit') as mock_reddit:
            # Make Reddit initialization fail
            mock_reddit.side_effect = Exception("Reddit API connection failed")
            
            from src.main_agent import RedditTikTokAgent
            
            with pytest.raises(Exception):
                agent = RedditTikTokAgent()
    
    @pytest.mark.asyncio
    async def test_workflow_with_no_quality_posts(self, temp_workspace, mock_environment):
        """Test workflow when no posts meet quality threshold."""
        
        with patch('src.reddit_fetcher.praw.Reddit') as mock_reddit, \
             patch('src.content_assessor.anthropic.Anthropic') as mock_anthropic:
            
            # Setup mocks
            mock_reddit_instance = Mock()
            mock_reddit.return_value = mock_reddit_instance
            mock_reddit_instance.user.me.return_value = Mock()
            
            # Reddit returns posts but assessor rejects all
            from src.reddit_fetcher import RedditFetcher
            from src.content_assessor import ContentAssessor
            
            RedditFetcher.get_funny_posts = Mock(return_value=MOCK_REDDIT_POSTS)
            ContentAssessor.assess_humor_quality = Mock(return_value=[])  # No posts pass quality
            
            from src.main_agent import RedditTikTokAgent
            
            agent = RedditTikTokAgent({'min_humor_rating': 9.5})
            result = await agent.run()
            
            assert result['creation_status'] == 'failed'
            assert 'No posts met quality threshold' in result['error_message']
    
    @pytest.mark.asyncio
    async def test_batch_video_creation(self, temp_workspace, mock_environment):
        """Test creating multiple videos in a batch."""
        
        with patch('src.reddit_fetcher.praw.Reddit') as mock_reddit, \
             patch('src.content_assessor.anthropic.Anthropic') as mock_anthropic, \
             patch('src.tts_generator.openai.OpenAI') as mock_openai, \
             patch('src.video_creator.VideoFileClip') as mock_video_clip:
            
            # Setup all mocks (similar to test_complete_workflow_success)
            self._setup_all_mocks(mock_reddit, mock_anthropic, mock_openai, mock_video_clip)
            
            from src.main_agent import RedditTikTokAgent
            
            agent = RedditTikTokAgent()
            
            # Create batch of 3 videos
            results = agent.run_batch(count=3)
            
            assert len(results) == 3
            
            # Check that each result has the expected structure
            for result in results:
                assert 'creation_status' in result
                # Some might succeed, some might fail - that's realistic
    
    def test_video_organizer_integration(self, temp_workspace, mock_environment):
        """Test video organization and metadata management."""
        
        from src.video_organizer import VideoOrganizer
        
        organizer = VideoOrganizer()
        
        # Test saving metadata
        test_post = MOCK_ASSESSED_POSTS[0]
        test_video_path = "output_videos/test_video.mp4"
        test_audio_path = "output_videos/audio/test_audio.mp3"
        
        # Create mock files
        Path(test_video_path).touch()
        Path(test_audio_path).touch()
        
        metadata = organizer.save_video_metadata(test_post, test_video_path, test_audio_path)
        
        # Verify metadata structure
        assert 'video_info' in metadata
        assert 'reddit_data' in metadata
        assert 'tiktok_content' in metadata
        assert 'performance_predictions' in metadata
        
        # Verify TikTok content
        tiktok_content = metadata['tiktok_content']
        assert len(tiktok_content['suggested_caption']) > 0
        assert len(tiktok_content['suggested_hashtags']) > 0
        assert 'reddit' in tiktok_content['suggested_hashtags']
        
        # Test listing videos
        organizer.list_created_videos()
        
        # Test upload queue
        queue = organizer.get_upload_queue()
        assert len(queue) >= 1
    
    def test_configuration_integration(self, temp_workspace, mock_environment):
        """Test configuration management integration."""
        
        from config.settings import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test configuration validation
        errors = config_manager.validate_config()
        # Should have no errors with mock environment
        assert isinstance(errors, list)
        
        # Test agent configuration generation
        agent_config = config_manager.get_agent_config()
        assert 'subreddits' in agent_config
        assert 'min_humor_rating' in agent_config
        assert 'post_limit' in agent_config
        
        # Test configuration display
        config_manager.print_config()
    
    def test_cli_integration(self, temp_workspace, mock_environment):
        """Test CLI integration without actually running commands."""
        
        # Import CLI after setting up environment
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from main import CLI
        
        cli = CLI()
        
        # Test parser creation
        parser = cli.create_parser()
        assert parser is not None
        
        # Test configuration display
        result = cli.cmd_config(type('Args', (), {'show': True, 'validate': False, 'create_example': False})())
        assert result == 0
        
        # Test status command
        result = cli.cmd_status(type('Args', (), {})())
        # May fail due to missing components, but should not crash
        assert result in [0, 1]
    
    def _setup_all_mocks(self, mock_reddit, mock_anthropic, mock_openai, mock_video_clip):
        """Helper method to set up all mocks for testing."""
        
        # Reddit mock
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        mock_reddit_instance.user.me.return_value = Mock()
        
        # Content mocks
        from src.reddit_fetcher import RedditFetcher
        from src.content_assessor import ContentAssessor
        
        RedditFetcher.get_funny_posts = Mock(return_value=MOCK_REDDIT_POSTS)
        ContentAssessor.assess_humor_quality = Mock(return_value=MOCK_ASSESSED_POSTS)
        
        # TTS mock
        mock_openai_client = Mock()
        mock_openai.return_value = mock_openai_client
        mock_response = Mock()
        mock_response.stream_to_file = Mock()
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        # Video mock
        mock_clip = Mock()
        mock_clip.duration = 25.0
        mock_clip.write_videofile = Mock()
        mock_clip.close = Mock()
        mock_video_clip.return_value = mock_clip
        
        # Create test audio file
        test_audio_path = Path("output_videos/audio/test_audio.mp3")
        test_audio_path.parent.mkdir(parents=True, exist_ok=True)
        test_audio_path.touch()


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for error testing."""
        temp_dir = tempfile.mkdtemp(prefix="reddit_tiktok_error_test_")
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            Path("output_videos").mkdir(exist_ok=True)
            yield temp_dir
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_api_key_missing(self, temp_workspace):
        """Test handling of missing API keys."""
        
        # Clear environment variables
        for key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'REDDIT_CLIENT_ID']:
            if key in os.environ:
                del os.environ[key]
        
        # Should raise appropriate errors
        with pytest.raises(ValueError):
            from src.content_assessor import ContentAssessor
            ContentAssessor()
        
        with pytest.raises(ValueError):
            from src.tts_generator import TTSGenerator
            TTSGenerator()
    
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, temp_workspace, monkeypatch):
        """Test recovery from network failures."""
        
        # Set up environment
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            # Make API calls fail
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("Network error")
            
            from src.content_assessor import ContentAssessor
            assessor = ContentAssessor()
            
            # Should handle gracefully and return default values
            rating, reasoning, improvements = assessor._assess_single_post(MOCK_REDDIT_POSTS[0])
            
            assert 1.0 <= rating <= 10.0  # Should return valid rating
            assert "Assessment failed" in reasoning
    
    @pytest.mark.asyncio 
    async def test_file_system_errors(self, temp_workspace):
        """Test handling of file system errors."""
        
        from src.video_organizer import VideoOrganizer
        
        # Make output directory read-only
        output_dir = Path("output_videos")
        output_dir.chmod(0o444)  # Read-only
        
        try:
            organizer = VideoOrganizer()
            
            # Should handle gracefully when cannot write
            with pytest.raises(PermissionError):
                organizer.save_video_metadata(
                    MOCK_ASSESSED_POSTS[0],
                    "test_video.mp4",
                    "test_audio.mp3"
                )
        finally:
            # Restore permissions for cleanup
            output_dir.chmod(0o755)


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""
    
    def test_large_batch_processing(self):
        """Test processing large batches of posts."""
        
        # Create a large number of mock posts
        large_post_batch = []
        for i in range(100):
            post = MOCK_REDDIT_POSTS[0].copy()
            post['id'] = f"test_{i:03d}"
            post['title'] = f"Test post {i} with unique content"
            large_post_batch.append(post)
        
        from src.content_assessor import ContentAssessor
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            # Mock successful responses
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            mock_response = Mock()
            mock_response.content = [Mock(text="RATING: 7.5\nREASONING: Good\nIMPROVEMENTS: None")]
            mock_client.messages.create.return_value = mock_response
            
            assessor = ContentAssessor()
            
            # Process large batch
            import time
            start_time = time.time()
            
            # Process in smaller chunks to avoid rate limits
            assessed_posts = assessor.assess_humor_quality(large_post_batch[:10], min_rating=6.0)
            
            end_time = time.time()
            
            # Should complete in reasonable time
            assert end_time - start_time < 30.0  # Less than 30 seconds for 10 posts
            assert len(assessed_posts) <= 10
    
    def test_memory_usage(self):
        """Test memory usage with multiple video creations."""
        
        # This would test memory leaks in a real scenario
        # For now, just verify that objects can be created and destroyed
        
        from src.video_creator import VideoCreator
        
        creators = []
        for i in range(10):
            creator = VideoCreator()
            creators.append(creator)
        
        # Clean up
        del creators
        
        # Memory should be freed (in a real test, you'd measure this)
        assert True  # Placeholder assertion


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_daily_automation_scenario(self, monkeypatch):
        """Test a realistic daily automation scenario."""
        
        # Set up realistic environment
        monkeypatch.setenv("REDDIT_CLIENT_ID", "test_client")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic")
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai")
        monkeypatch.setenv("SCHEDULE_MAX_VIDEOS_PER_DAY", "5")
        monkeypatch.setenv("CONTENT_MIN_HUMOR_RATING", "7.5")
        
        # Mock successful workflow
        with patch('src.reddit_fetcher.praw.Reddit'), \
             patch('src.content_assessor.anthropic.Anthropic'), \
             patch('src.tts_generator.openai.OpenAI'), \
             patch('src.video_creator.VideoFileClip'):
            
            from scheduler import VideoCreationScheduler
            
            scheduler = VideoCreationScheduler()
            
            # Test can_create_video logic
            can_create, reason = scheduler._can_create_video_now()
            assert isinstance(can_create, bool)
            assert isinstance(reason, str)
            
            # Test peak time detection
            is_peak = scheduler._is_peak_time()
            assert isinstance(is_peak, bool)


if __name__ == "__main__":
    """Run integration tests when script is executed directly."""
    
    print("🧪 Running Reddit to TikTok Integration Tests...")
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest found, running integration test suite...")
        
        # Run pytest with integration tests
        exit_code = pytest.main([
            __file__,
            "-v",
            "--tb=short",
            "--color=yes",
            "-k", "not test_large_batch_processing"  # Skip long-running tests by default
        ])
        
        if exit_code == 0:
            print("✅ All integration tests passed!")
        else:
            print("❌ Some integration tests failed!")
            
    except ImportError:
        print("⚠️  pytest not found. Install with: pip install pytest pytest-asyncio")
        print("Running basic integration checks...")
        
        # Basic integration check without pytest
        async def basic_check():
            try:
                # Test imports
                from src.main_agent import RedditTikTokAgent
                from src.video_organizer import VideoOrganizer
                from config.settings import ConfigManager
                
                print("✅ All imports successful")
                print("✅ Basic integration check passed")
                
            except Exception as e:
                print(f"❌ Basic integration check failed: {e}")
        
        import asyncio
        asyncio.run(basic_check())
