"""
Reddit Content Fetcher

Handles fetching and filtering content from Reddit using PRAW.
"""

import praw
import os
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RedditFetcher:
    """Fetches and filters Reddit content suitable for TikTok videos."""
    
    def __init__(self):
        """Initialize Reddit API client."""
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditVideoCreator/1.0')
            )
            # Test connection
            self.reddit.user.me()
            logger.info("Reddit API connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Reddit API: {e}")
            raise
    
    def get_funny_posts(self, 
                       subreddits: Optional[List[str]] = None, 
                       limit: int = 50,
                       time_filter: str = 'day') -> List[Dict]:
        """
        Fetch funny posts from multiple subreddits.
        
        Args:
            subreddits: List of subreddit names. If None, uses default list.
            limit: Maximum number of posts to fetch
            time_filter: Time filter for posts ('hour', 'day', 'week', 'month', 'year', 'all')
            
        Returns:
            List of post dictionaries suitable for video creation
        """
        if subreddits is None:
            subreddits = [
                'funny', 'memes', 'wholesomememes', 'tifu', 
                'askreddit', 'showerthoughts', 'todayilearned',
                'confession', 'unpopularopinion', 'amitheasshole'
            ]
        
        all_posts = []
        posts_per_subreddit = max(1, limit // len(subreddits))
        
        logger.info(f"Fetching posts from {len(subreddits)} subreddits")
        
        for sub_name in subreddits:
            try:
                posts = self._fetch_from_subreddit(sub_name, posts_per_subreddit, time_filter)
                all_posts.extend(posts)
                logger.info(f"Fetched {len(posts)} posts from r/{sub_name}")
            except Exception as e:
                logger.warning(f"Failed to fetch from r/{sub_name}: {e}")
                continue
        
        # Sort by score and return top posts
        sorted_posts = sorted(all_posts, key=lambda x: x['score'], reverse=True)
        final_posts = sorted_posts[:limit]
        
        logger.info(f"Returning {len(final_posts)} total posts")
        return final_posts
    
    def _fetch_from_subreddit(self, 
                             subreddit_name: str, 
                             limit: int,
                             time_filter: str) -> List[Dict]:
        """Fetch posts from a specific subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Get hot posts
            for post in subreddit.hot(limit=limit * 3):  # Fetch extra to account for filtering
                if self._is_suitable_post(post):
                    post_data = self._extract_post_data(post)
                    posts.append(post_data)
                    
                    if len(posts) >= limit:
                        break
            
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit_name}: {e}")
            return []
    
    def _is_suitable_post(self, post) -> bool:
        """
        Check if a post is suitable for TikTok video creation.
        
        Args:
            post: PRAW submission object
            
        Returns:
            True if post is suitable, False otherwise
        """
        # Must be text-based (self post)
        if not post.is_self:
            return False
        
        # Check if post is removed or deleted
        if post.removed_by_category or post.selftext in ['[removed]', '[deleted]', '']:
            return False
        
        # Check minimum score
        if post.score < 50:
            return False
        
        # Check text length for TTS suitability
        total_text = post.title + " " + post.selftext
        text_length = len(total_text)
        
        # Too short or too long
        if text_length < 100 or text_length > 1500:
            return False
        
        # Check for problematic content
        if self._contains_inappropriate_content(total_text):
            return False
        
        # Check if post is recent enough
        post_age = datetime.utcnow() - datetime.utcfromtimestamp(post.created_utc)
        if post_age > timedelta(days=7):
            return False
        
        # Check comment engagement (indicates quality)
        if post.num_comments < 10:
            return False
        
        return True
    
    def _contains_inappropriate_content(self, text: str) -> bool:
        """Check for inappropriate content that shouldn't be in TikTok videos."""
        inappropriate_keywords = [
            # NSFW content
            'nsfw', 'explicit', 'sexual', 'porn', 'nude', 'naked',
            # Violence
            'kill', 'murder', 'suicide', 'death', 'violence', 'abuse',
            # Illegal activities
            'drug', 'illegal', 'steal', 'crime', 'hack',
            # Hate speech indicators
            'racist', 'sexist', 'homophobic', 'hate',
            # Political controversy (to avoid polarization)
            'trump', 'biden', 'politics', 'election', 'democrat', 'republican'
        ]
        
        text_lower = text.lower()
        for keyword in inappropriate_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def _extract_post_data(self, post) -> Dict:
        """
        Extract relevant data from a Reddit post.
        
        Args:
            post: PRAW submission object
            
        Returns:
            Dictionary with post data
        """
        # Clean text for TTS
        title = self._clean_text_for_tts(post.title)
        selftext = self._clean_text_for_tts(post.selftext)
        
        return {
            'id': post.id,
            'title': title,
            'selftext': selftext,
            'score': post.score,
            'upvote_ratio': post.upvote_ratio,
            'url': f"https://reddit.com{post.permalink}",
            'subreddit': post.subreddit.display_name,
            'created_utc': post.created_utc,
            'num_comments': post.num_comments,
            'author': str(post.author) if post.author else '[deleted]',
            'total_length': len(title + selftext),
            'fetched_at': datetime.utcnow().isoformat()
        }
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text to make it suitable for text-to-speech.
        
        Args:
            text: Raw text from Reddit
            
        Returns:
            Cleaned text suitable for TTS
        """
        if not text:
            return ""
        
        # Remove Reddit markdown
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)      # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)          # Italic
        text = re.sub(r'~~([^~]+)~~', r'\1', text)          # Strikethrough
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Headers
        
        # Remove special characters that cause TTS issues
        text = re.sub(r'[^\w\s.,!?;:\'"()-]', ' ', text)
        
        # Fix common Reddit abbreviations
        replacements = {
            'TL;DR': 'Too long, didn\'t read',
            'TLDR': 'Too long, didn\'t read',
            'IMO': 'In my opinion',
            'IMHO': 'In my humble opinion',
            'BTW': 'By the way',
            'FYI': 'For your information',
            'EDIT:': 'Edit:',
            'UPDATE:': 'Update:',
            'WIBTA': 'Would I be the asshole',
            'AITA': 'Am I the asshole',
            'NTA': 'Not the asshole',
            'YTA': 'You are the asshole'
        }
        
        for abbr, full in replacements.items():
            text = re.sub(rf'\b{re.escape(abbr)}\b', full, text, flags=re.IGNORECASE)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict]:
        """
        Get a specific post by its Reddit ID.
        
        Args:
            post_id: Reddit post ID
            
        Returns:
            Post data dictionary or None if not found
        """
        try:
            post = self.reddit.submission(id=post_id)
            if self._is_suitable_post(post):
                return self._extract_post_data(post)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            return None
    
    def search_posts(self, 
                    query: str, 
                    subreddits: Optional[List[str]] = None,
                    limit: int = 20) -> List[Dict]:
        """
        Search for posts matching a query.
        
        Args:
            query: Search query
            subreddits: List of subreddits to search. If None, searches all.
            limit: Maximum number of posts to return
            
        Returns:
            List of matching posts
        """
        if subreddits is None:
            subreddits = ['funny', 'memes', 'tifu', 'askreddit']
        
        all_posts = []
        
        for sub_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                for post in subreddit.search(query, limit=limit // len(subreddits)):
                    if self._is_suitable_post(post):
                        all_posts.append(self._extract_post_data(post))
            except Exception as e:
                logger.warning(f"Search failed in r/{sub_name}: {e}")
                continue
        
        return sorted(all_posts, key=lambda x: x['score'], reverse=True)[:limit]


if __name__ == "__main__":
    # Test the Reddit fetcher
    import sys
    import json
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        fetcher = RedditFetcher()
        posts = fetcher.get_funny_posts(limit=5)
        
        print(f"Fetched {len(posts)} posts:")
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post['title'][:60]}...")
            print(f"   Subreddit: r/{post['subreddit']}")
            print(f"   Score: {post['score']}")
            print(f"   Length: {post['total_length']} chars")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
