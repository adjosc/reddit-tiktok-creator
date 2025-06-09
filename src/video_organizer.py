"""
Video Organizer

Manages created videos, metadata, and provides utilities for content management.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available for video duration calculation")

logger = logging.getLogger(__name__)


class VideoOrganizer:
    """Organizes and manages created videos with metadata and suggestions."""
    
    def __init__(self):
        """Initialize video organizer."""
        self.output_dir = Path("output_videos")
        self.output_dir.mkdir(exist_ok=True)
        
        # Metadata and organization files
        self.metadata_file = self.output_dir / "video_metadata.json"
        self.queue_file = self.output_dir / "upload_queue.json"
        self.stats_file = self.output_dir / "creation_stats.json"
        
        # Subdirectories for organization
        self.ready_dir = self.output_dir / "ready_to_upload"
        self.uploaded_dir = self.output_dir / "uploaded"
        self.archive_dir = self.output_dir / "archive"
        
        # Create subdirectories
        for directory in [self.ready_dir, self.uploaded_dir, self.archive_dir]:
            directory.mkdir(exist_ok=True)
        
        logger.info("Video organizer initialized")
    
    def save_video_metadata(self, 
                           post: Dict, 
                           video_path: str, 
                           audio_path: str,
                           creation_stats: Optional[Dict] = None) -> Dict:
        """
        Save comprehensive metadata for a created video.
        
        Args:
            post: Reddit post dictionary
            video_path: Path to created video
            audio_path: Path to generated audio
            creation_stats: Optional stats about creation process
            
        Returns:
            Complete metadata dictionary
        """
        try:
            # Calculate video duration
            duration = self._get_video_duration(video_path)
            
            # Generate TikTok-ready content
            caption = self._generate_caption(post)
            hashtags = self._generate_hashtags(post)
            description = self._generate_description(post)
            
            # Create comprehensive metadata
            metadata = {
                'video_info': {
                    'video_path': str(video_path),
                    'audio_path': str(audio_path),
                    'duration_seconds': duration,
                    'file_size_mb': self._get_file_size_mb(video_path),
                    'created_at': datetime.now().isoformat(),
                    'status': 'ready_to_upload'
                },
                'reddit_data': {
                    'id': post.get('id'),
                    'title': post['title'],
                    'content': post.get('selftext', ''),
                    'subreddit': post['subreddit'],
                    'score': post['score'],
                    'url': post.get('url', ''),
                    'num_comments': post.get('num_comments', 0),
                    'author': post.get('author', '[unknown]'),
                    'humor_rating': post.get('humor_rating', 0),
                    'assessment_reasoning': post.get('assessment_reasoning', ''),
                    'fetched_at': post.get('fetched_at')
                },
                'tiktok_content': {
                    'suggested_caption': caption,
                    'suggested_hashtags': hashtags,
                    'description': description,
                    'target_audience': self._determine_target_audience(post),
                    'content_category': self._categorize_content(post),
                    'upload_timing': self._suggest_upload_timing(post)
                },
                'creation_stats': creation_stats or {},
                'performance_predictions': self._predict_performance(post)
            }
            
            # Save to metadata file
            self._append_metadata(metadata)
            
            # Update creation statistics
            self._update_creation_stats(metadata)
            
            # Add to upload queue
            self._add_to_upload_queue(metadata)
            
            # Move video to ready folder
            ready_path = self._move_to_ready_folder(video_path)
            metadata['video_info']['video_path'] = str(ready_path)
            
            logger.info(f"✅ Video metadata saved for: {post['title'][:50]}...")
            self._print_upload_info(metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to save video metadata: {e}")
            raise
    
    def _generate_caption(self, post: Dict) -> str:
        """Generate TikTok-ready caption."""
        
        subreddit = post['subreddit']
        title = post['title']
        
        # Subreddit-specific caption templates
        caption_templates = {
            'tifu': [
                "This person really messed up 😅 #{subreddit}",
                "When everything goes wrong at once 😭 #{subreddit}",
                "Epic fail story incoming! 🤦‍♂️ #{subreddit}"
            ],
            'amitheasshole': [
                "You be the judge! 🤔 #{subreddit}",
                "Drama alert! Who's right here? 👀 #{subreddit}",
                "This situation is wild! 😳 #{subreddit}"
            ],
            'confession': [
                "Finally telling the truth 😌 #{subreddit}",
                "Secret revealed! 🤫 #{subreddit}",
                "They couldn't keep this secret anymore 😬 #{subreddit}"
            ],
            'funny': [
                "This had me dying 😂 #{subreddit}",
                "Comedy gold right here! 🤣 #{subreddit}",
                "You won't believe this! 😭 #{subreddit}"
            ]
        }
        
        # Choose appropriate template
        templates = caption_templates.get(subreddit, [
            "This Reddit story is wild! 🤯 #{subreddit}",
            "You have to hear this! 👀 #{subreddit}",
            "Reddit never disappoints! 😂 #{subreddit}"
        ])
        
        import random
        base_caption = random.choice(templates).replace('{subreddit}', subreddit)
        
        # Add context if title is short enough
        if len(title) < 60:
            base_caption = f'"{title}" {base_caption}'
        
        # Add standard ending
        base_caption += " Follow for more Reddit stories! 🔥"
        
        return base_caption
    
    def _generate_hashtags(self, post: Dict) -> List[str]:
        """Generate relevant hashtags for maximum reach."""
        
        base_hashtags = ['reddit', 'story', 'viral', 'foryou', 'fyp']
        
        # Subreddit-specific hashtags
        subreddit_tags = {
            'tifu': ['tifu', 'fail', 'embarrassing', 'mistakes', 'oops'],
            'amitheasshole': ['aita', 'drama', 'relationships', 'family', 'conflict'],
            'confession': ['confession', 'secret', 'truth', 'reveal', 'anonymous'],
            'funny': ['funny', 'comedy', 'humor', 'laughing', 'hilarious'],
            'wholesome': ['wholesome', 'heartwarming', 'positive', 'sweet', 'love'],
            'memes': ['memes', 'relatable', 'mood', 'facts', 'same'],
            'askreddit': ['askreddit', 'questions', 'answers', 'thoughts', 'opinions']
        }
        
        subreddit = post['subreddit'].lower()
        specific_tags = subreddit_tags.get(subreddit, [])
        
        # Content-based hashtags
        title_lower = post['title'].lower()
        content_lower = post.get('selftext', '').lower()
        all_text = title_lower + ' ' + content_lower
        
        content_keywords = {
            'relationship': ['dating', 'love', 'relationships', 'couple'],
            'work': ['work', 'job', 'boss', 'office', 'career'],
            'family': ['family', 'parents', 'siblings', 'relatives'],
            'school': ['school', 'college', 'university', 'student', 'teacher'],
            'food': ['food', 'cooking', 'restaurant', 'eating'],
            'travel': ['travel', 'vacation', 'trip', 'airport', 'hotel'],
            'technology': ['phone', 'computer', 'internet', 'app', 'tech'],
            'pets': ['dog', 'cat', 'pet', 'animal']
        }
        
        for category, keywords in content_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                specific_tags.append(category)
        
        # Combine and limit hashtags
        all_hashtags = base_hashtags + specific_tags
        unique_hashtags = list(dict.fromkeys(all_hashtags))  # Remove duplicates, preserve order
        
        return unique_hashtags[:15]  # TikTok hashtag limit
    
    def _generate_description(self, post: Dict) -> str:
        """Generate a description for the video."""
        
        title = post['title'][:100] + "..." if len(post['title']) > 100 else post['title']
        
        description = f"Reddit Story: {title}\n\n"
        description += f"From r/{post['subreddit']} • {post['score']:,} upvotes\n\n"
        description += "What would you do in this situation? Let me know in the comments! 👇\n\n"
        description += "#RedditStories #Viral #Story #Reddit"
        
        return description
    
    def _determine_target_audience(self, post: Dict) -> List[str]:
        """Determine target audience for the content."""
        
        audiences = []
        
        subreddit = post['subreddit'].lower()
        title_content = (post['title'] + ' ' + post.get('selftext', '')).lower()
        
        # Age-based audiences
        if any(word in title_content for word in ['school', 'college', 'university', 'teen']):
            audiences.append('teens_young_adults')
        
        if any(word in title_content for word in ['work', 'job', 'boss', 'career', 'office']):
            audiences.append('working_professionals')
        
        if any(word in title_content for word in ['parent', 'family', 'child', 'kid']):
            audiences.append('parents_families')
        
        # Interest-based audiences
        if subreddit in ['tifu', 'confession']:
            audiences.append('story_lovers')
        
        if subreddit in ['amitheasshole', 'relationship_advice']:
            audiences.append('drama_enthusiasts')
        
        if subreddit in ['funny', 'memes']:
            audiences.append('comedy_fans')
        
        # Default audiences
        if not audiences:
            audiences = ['general_entertainment', 'reddit_users']
        
        return audiences
    
    def _categorize_content(self, post: Dict) -> str:
        """Categorize content type for analytics."""
        
        subreddit = post['subreddit'].lower()
        title = post['title'].lower()
        
        # Primary categorization by subreddit
        category_map = {
            'tifu': 'embarrassing_stories',
            'amitheasshole': 'moral_dilemmas', 
            'confession': 'personal_confessions',
            'funny': 'humor_comedy',
            'wholesome': 'positive_content',
            'memes': 'meme_culture',
            'askreddit': 'q_and_a'
        }
        
        primary_category = category_map.get(subreddit, 'general_stories')
        
        # Secondary categorization by content
        if any(word in title for word in ['relationship', 'dating', 'boyfriend', 'girlfriend']):
            return f"{primary_category}_relationship"
        elif any(word in title for word in ['work', 'job', 'boss']):
            return f"{primary_category}_workplace"
        elif any(word in title for word in ['family', 'parent', 'sibling']):
            return f"{primary_category}_family"
        
        return primary_category
    
    def _suggest_upload_timing(self, post: Dict) -> Dict:
        """Suggest optimal upload timing based on content type."""
        
        # General TikTok peak times (EST)
        peak_times = {
            'weekday_morning': '6:00-9:00 AM',
            'weekday_lunch': '12:00-3:00 PM', 
            'weekday_evening': '7:00-9:00 PM',
            'weekend_afternoon': '12:00-6:00 PM'
        }
        
        subreddit = post['subreddit'].lower()
        
        # Content-specific timing suggestions
        if subreddit in ['funny', 'memes']:
            return {
                'best_times': [peak_times['weekday_lunch'], peak_times['weekday_evening']],
                'reasoning': 'Comedy content performs well during lunch and evening hours'
            }
        elif subreddit in ['tifu', 'confession']:
            return {
                'best_times': [peak_times['weekday_evening'], peak_times['weekend_afternoon']],
                'reasoning': 'Story content works well when people have time to engage'
            }
        elif subreddit in ['amitheasshole']:
            return {
                'best_times': [peak_times['weekday_evening'], peak_times['weekend_afternoon']],
                'reasoning': 'Drama content gets more engagement during leisure hours'
            }
        else:
            return {
                'best_times': list(peak_times.values()),
                'reasoning': 'General content can work at any peak time'
            }
    
    def _predict_performance(self, post: Dict) -> Dict:
        """Predict potential TikTok performance based on Reddit metrics."""
        
        score = post['score']
        comments = post.get('num_comments', 0)
        humor_rating = post.get('humor_rating', 5)
        
        # Calculate engagement rate on Reddit
        reddit_engagement = comments / max(score, 1) * 100
        
        # Predict TikTok metrics
        predicted_views = min(100000, max(1000, score * 5))  # 5x Reddit score, capped
        predicted_likes = predicted_views * 0.05 * (humor_rating / 10)  # 5% like rate adjusted for humor
        predicted_shares = predicted_likes * 0.1  # 10% of likes
        predicted_comments = predicted_views * 0.02  # 2% comment rate
        
        confidence = min(100, max(20, humor_rating * 10))  # Confidence based on humor rating
        
        return {
            'predicted_views': int(predicted_views),
            'predicted_likes': int(predicted_likes),
            'predicted_shares': int(predicted_shares),
            'predicted_comments': int(predicted_comments),
            'confidence_score': confidence,
            'reddit_engagement_rate': round(reddit_engagement, 2),
            'prediction_factors': {
                'reddit_score': score,
                'reddit_comments': comments,
                'humor_rating': humor_rating,
                'engagement_rate': reddit_engagement
            }
        }
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        
        if not MOVIEPY_AVAILABLE:
            return 0.0
        
        try:
            with VideoFileClip(video_path) as clip:
                return clip.duration
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
            return 0.0
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        
        try:
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def _append_metadata(self, metadata: Dict):
        """Append metadata to the main metadata file."""
        
        all_metadata = []
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    all_metadata = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Metadata file corrupted, starting fresh")
                all_metadata = []
        
        all_metadata.append(metadata)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)
    
    def _update_creation_stats(self, metadata: Dict):
        """Update overall creation statistics."""
        
        stats = {}
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
            except json.JSONDecodeError:
                stats = {}
        
        # Initialize stats if needed
        if not stats:
            stats = {
                'total_videos_created': 0,
                'subreddits': {},
                'average_humor_rating': 0,
                'total_processing_time': 0,
                'creation_dates': []
            }
        
        # Update stats
        stats['total_videos_created'] += 1
        
        subreddit = metadata['reddit_data']['subreddit']
        stats['subreddits'][subreddit] = stats['subreddits'].get(subreddit, 0) + 1
        
        humor_rating = metadata['reddit_data']['humor_rating']
        if humor_rating > 0:
            current_avg = stats['average_humor_rating']
            total_videos = stats['total_videos_created']
            stats['average_humor_rating'] = (current_avg * (total_videos - 1) + humor_rating) / total_videos
        
        stats['creation_dates'].append(datetime.now().isoformat())
        
        # Keep only last 100 creation dates
        stats['creation_dates'] = stats['creation_dates'][-100:]
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def _add_to_upload_queue(self, metadata: Dict):
        """Add video to upload queue."""
        
        queue = []
        
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    queue = json.load(f)
            except json.JSONDecodeError:
                queue = []
        
        queue_item = {
            'video_path': metadata['video_info']['video_path'],
            'caption': metadata['tiktok_content']['suggested_caption'],
            'hashtags': metadata['tiktok_content']['suggested_hashtags'],
            'description': metadata['tiktok_content']['description'],
            'upload_timing': metadata['tiktok_content']['upload_timing'],
            'priority': metadata['reddit_data']['humor_rating'],
            'added_at': datetime.now().isoformat()
        }
        
        queue.append(queue_item)
        
        # Sort by priority (humor rating)
        queue.sort(key=lambda x: x['priority'], reverse=True)
        
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
    
    def _move_to_ready_folder(self, video_path: str) -> Path:
        """Move video to ready-to-upload folder."""
        
        video_file = Path(video_path)
        new_path = self.ready_dir / video_file.name
        
        try:
            shutil.move(str(video_file), str(new_path))
            return new_path
        except Exception as e:
            logger.warning(f"Could not move video to ready folder: {e}")
            return video_file
    
    def _print_upload_info(self, metadata: Dict):
        """Print formatted upload information."""
        
        print(f"\n🎬 Video Ready for Upload!")
        print(f"📁 File: {Path(metadata['video_info']['video_path']).name}")
        print(f"⏱️  Duration: {metadata['video_info']['duration_seconds']:.1f}s")
        print(f"📊 Humor Rating: {metadata['reddit_data']['humor_rating']}/10")
        print(f"\n📝 Suggested Caption:")
        print(f"   {metadata['tiktok_content']['suggested_caption']}")
        print(f"\n🏷️  Suggested Hashtags:")
        hashtags = ' '.join([f'#{tag}' for tag in metadata['tiktok_content']['suggested_hashtags'][:10]])
        print(f"   {hashtags}")
        print(f"\n📈 Performance Prediction:")
        pred = metadata['performance_predictions']
        print(f"   Views: {pred['predicted_views']:,} (confidence: {pred['confidence_score']}%)")
        print(f"   Likes: {pred['predicted_likes']:,}")
        print(f"\n⏰ Best Upload Times:")
        for time in metadata['tiktok_content']['upload_timing']['best_times']:
            print(f"   • {time}")
        print("\n" + "="*50)
    
    def list_created_videos(self, limit: int = 10):
        """List recently created videos with metadata."""
        
        if not self.metadata_file.exists():
            print("📂 No videos created yet!")
            return
        
        try:
            with open(self.metadata_file, 'r') as f:
                videos = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error reading video metadata")
            return
        
        if not videos:
            print("📂 No videos found!")
            return
        
        print(f"\n🎬 Created Videos ({len(videos)} total, showing last {min(limit, len(videos))}):\n")
        
        for i, video in enumerate(reversed(videos[-limit:]), 1):
            reddit_data = video['reddit_data']
            video_info = video['video_info']
            
            print(f"{i}. {reddit_data['title'][:60]}...")
            print(f"   📁 {Path(video_info['video_path']).name}")
            print(f"   📊 Rating: {reddit_data['humor_rating']}/10")
            print(f"   ⏱️  Duration: {video_info['duration_seconds']:.1f}s")
            print(f"   📅 Created: {video_info['created_at'][:19].replace('T', ' ')}")
            print(f"   🎯 r/{reddit_data['subreddit']} • {reddit_data['score']:,} upvotes")
            print()
    
    def get_upload_queue(self) -> List[Dict]:
        """Get current upload queue sorted by priority."""
        
        if not self.queue_file.exists():
            return []
        
        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    
    def mark_as_uploaded(self, video_path: str):
        """Mark a video as uploaded and move to uploaded folder."""
        
        try:
            video_file = Path(video_path)
            uploaded_path = self.uploaded_dir / video_file.name
            
            # Move file
            shutil.move(str(video_file), str(uploaded_path))
            
            # Remove from queue
            queue = self.get_upload_queue()
            queue = [item for item in queue if item['video_path'] != video_path]
            
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
            
            logger.info(f"✅ Video marked as uploaded: {video_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to mark video as uploaded: {e}")
    
    def get_creation_stats(self) -> Dict:
        """Get overall creation statistics."""
        
        if not self.stats_file.exists():
            return {}
        
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def cleanup_old_files(self, days_old: int = 30):
        """Clean up files older than specified days."""
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for directory in [self.uploaded_dir, self.archive_dir]:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        try:
                            file_path.unlink()
                            logger.info(f"Cleaned up old file: {file_path.name}")
                        except Exception as e:
                            logger.warning(f"Could not clean up {file_path.name}: {e}")


if __name__ == "__main__":
    # Test the video organizer
    from datetime import datetime
    
    # Sample test data
    test_post = {
        'id': 'test123',
        'title': 'TIFU by accidentally sending my boss a meme',
        'selftext': 'This happened yesterday and I am still cringing...',
        'subreddit': 'tifu',
        'score': 1500,
        'num_comments': 89,
        'humor_rating': 8.5,
        'assessment_reasoning': 'Relatable workplace humor with good storytelling'
    }
    
    try:
        organizer = VideoOrganizer()
        
        print("✅ Video organizer initialized successfully!")
        print(f"📁 Output directory: {organizer.output_dir}")
        print(f"📊 Metadata file: {organizer.metadata_file}")
        
        # Show existing videos
        organizer.list_created_videos()
        
        # Show stats
        stats = organizer.get_creation_stats()
        if stats:
            print(f"\n📈 Creation Stats:")
            print(f"   Total videos: {stats.get('total_videos_created', 0)}")
            print(f"   Average rating: {stats.get('average_humor_rating', 0):.1f}/10")
        
    except Exception as e:
        print(f"Error: {e}")
