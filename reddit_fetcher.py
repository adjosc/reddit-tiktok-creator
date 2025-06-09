import praw
import os
from typing import List, Dict
from datetime import datetime, timedelta

class RedditFetcher:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
    
    def get_funny_posts(self, limit=50) -> List[Dict]:
        """Fetch funny posts from multiple subreddits"""
        subreddits = ['funny', 'memes', 'wholesomememes', 'tifu', 'askreddit']
        posts = []
        
        for sub_name in subreddits:
            subreddit = self.reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=limit//len(subreddits)):
                if self._is_suitable_post(post):
                    posts.append({
                        'title': post.title,
                        'selftext': post.selftext,
                        'score': post.score,
                        'url': post.url,
                        'subreddit': post.subreddit.display_name,
                        'created_utc': post.created_utc,
                        'num_comments': post.num_comments
                    })
        
        return sorted(posts, key=lambda x: x['score'], reverse=True)
    
    def _is_suitable_post(self, post) -> bool:
        """Filter posts suitable for TikTok"""
        # Text-based posts work best for TTS
        if not post.is_self:
            return False
        
        # Check length (TikTok has time limits)
        text_length = len(post.title + post.selftext)
        if text_length < 50 or text_length > 1000:
            return False
        
        # Check if recent and popular
        if post.score < 100:
            return False
            
        return True
