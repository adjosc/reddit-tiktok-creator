import anthropic
import os
from typing import Dict, List

class ContentAssessor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def assess_humor_quality(self, posts: List[Dict]) -> List[Dict]:
        """Use Claude to assess and rank posts by humor quality"""
        assessed_posts = []
        
        for post in posts:
            prompt = f"""
            Rate this Reddit post for TikTok humor potential (1-10):
            
            Title: {post['title']}
            Content: {post['selftext'][:500]}
            Subreddit: {post['subreddit']}
            Score: {post['score']}
            
            Consider:
            - Humor quality and broad appeal
            - TikTok audience appropriateness 
            - Text-to-speech readability
            - Engaging hook in first few seconds
            
            Respond with just a number 1-10 and brief reason.
            """
            
            try:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                rating_text = response.content[0].text
                rating = float(rating_text.split()[0])
                post['humor_rating'] = rating
                post['assessment_reason'] = rating_text
                
                if rating >= 7:  # Only keep high-quality posts
                    assessed_posts.append(post)
                    
            except Exception as e:
                print(f"Error assessing post: {e}")
                continue
        
        return sorted(assessed_posts, key=lambda x: x['humor_rating'], reverse=True)
