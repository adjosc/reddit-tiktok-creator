"""
Content Quality Assessor

Uses Anthropic Claude to evaluate Reddit content for humor quality and TikTok suitability.
"""

import anthropic
import os
import re
import asyncio
from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentAssessor:
    """Assesses Reddit content quality using AI to determine TikTok suitability."""
    
    def __init__(self):
        """Initialize Anthropic client."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"
        
        logger.info("Content assessor initialized with Claude")
    
    def assess_humor_quality(self, posts: List[Dict], min_rating: float = 7.0) -> List[Dict]:
        """
        Assess multiple posts for humor quality and TikTok potential.
        
        Args:
            posts: List of Reddit post dictionaries
            min_rating: Minimum rating threshold (1-10 scale)
            
        Returns:
            Filtered and sorted list of high-quality posts
        """
        logger.info(f"Assessing {len(posts)} posts for humor quality")
        
        assessed_posts = []
        
        for i, post in enumerate(posts, 1):
            try:
                logger.info(f"Assessing post {i}/{len(posts)}: {post['title'][:50]}...")
                
                rating, reasoning, improvements = self._assess_single_post(post)
                
                if rating >= min_rating:
                    post['humor_rating'] = rating
                    post['assessment_reasoning'] = reasoning
                    post['suggested_improvements'] = improvements
                    post['assessed_at'] = datetime.utcnow().isoformat()
                    assessed_posts.append(post)
                    
                    logger.info(f"✅ Post rated {rating}/10 - ACCEPTED")
                else:
                    logger.info(f"❌ Post rated {rating}/10 - REJECTED (below {min_rating})")
                
            except Exception as e:
                logger.warning(f"Failed to assess post {i}: {e}")
                continue
        
        # Sort by rating (highest first)
        assessed_posts.sort(key=lambda x: x['humor_rating'], reverse=True)
        
        logger.info(f"Assessment complete: {len(assessed_posts)}/{len(posts)} posts passed quality check")
        return assessed_posts
    
    def _assess_single_post(self, post: Dict) -> Tuple[float, str, str]:
        """
        Assess a single post for humor quality.
        
        Args:
            post: Reddit post dictionary
            
        Returns:
            Tuple of (rating, reasoning, suggested_improvements)
        """
        prompt = self._create_assessment_prompt(post)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return self._parse_assessment_response(content)
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            # Return neutral score on error
            return 5.0, f"Assessment failed: {e}", "Manual review required"
    
    def _create_assessment_prompt(self, post: Dict) -> str:
        """Create a detailed prompt for content assessment."""
        
        title = post['title']
        content = post['selftext'][:800]  # Limit content length for prompt
        subreddit = post['subreddit']
        score = post['score']
        
        prompt = f"""
Rate this Reddit post for TikTok humor potential on a scale of 1-10.

POST DETAILS:
Title: {title}
Content: {content}
Subreddit: r/{subreddit}
Reddit Score: {score} upvotes

EVALUATION CRITERIA:
1. Humor Quality (1-10): How funny/entertaining is this content?
2. TikTok Appeal (1-10): Would this engage TikTok's younger audience?
3. TTS Readability (1-10): How well would this work as text-to-speech?
4. Viral Potential (1-10): Could this become shareable content?
5. Content Safety (1-10): Is this appropriate for all audiences?

REQUIREMENTS FOR HIGH SCORES:
- Clear, engaging narrative or punchline
- Relatable situations or universal humor
- Appropriate length for TikTok (15-60 seconds when read aloud)
- No controversial, offensive, or inappropriate content
- Strong hook in the first few sentences
- Easy to understand when heard (not read)

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
RATING: [number from 1-10]
REASONING: [2-3 sentences explaining the rating]
IMPROVEMENTS: [suggestions for making this content better for TikTok, or "None needed" if rating is 9+]

Consider that this will be read aloud by AI voice, so avoid content that relies heavily on visual formatting, links, or written elements that don't translate well to audio.
"""
        
        return prompt
    
    def _parse_assessment_response(self, response: str) -> Tuple[float, str, str]:
        """
        Parse Claude's assessment response.
        
        Args:
            response: Raw response text from Claude
            
        Returns:
            Tuple of (rating, reasoning, improvements)
        """
        try:
            # Extract rating
            rating_match = re.search(r'RATING:\s*([0-9.]+)', response)
            if rating_match:
                rating = float(rating_match.group(1))
                rating = max(1.0, min(10.0, rating))  # Clamp to 1-10 range
            else:
                # Fallback: look for any number at the start
                number_match = re.search(r'([0-9.]+)', response)
                rating = float(number_match.group(1)) if number_match else 5.0
            
            # Extract reasoning
            reasoning_match = re.search(r'REASONING:\s*([^\n]+(?:\n[^\n]+)*?)(?=IMPROVEMENTS:|$)', response, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No detailed reasoning provided"
            
            # Extract improvements
            improvements_match = re.search(r'IMPROVEMENTS:\s*([^\n]+(?:\n[^\n]+)*?)$', response, re.DOTALL)
            improvements = improvements_match.group(1).strip() if improvements_match else "No specific improvements suggested"
            
            # Clean up text
            reasoning = re.sub(r'\s+', ' ', reasoning).strip()
            improvements = re.sub(r'\s+', ' ', improvements).strip()
            
            return rating, reasoning, improvements
            
        except Exception as e:
            logger.warning(f"Failed to parse assessment response: {e}")
            logger.debug(f"Raw response: {response}")
            return 5.0, "Parsing error occurred", "Manual review needed"
    
    def assess_for_specific_audience(self, post: Dict, audience_type: str = "general") -> Dict:
        """
        Assess content for a specific audience type.
        
        Args:
            post: Reddit post dictionary
            audience_type: "general", "young_adult", "family_friendly", "comedy"
            
        Returns:
            Detailed assessment dictionary
        """
        audience_prompts = {
            "general": "Rate for broad TikTok appeal across all age groups",
            "young_adult": "Rate specifically for 18-25 year old TikTok users",
            "family_friendly": "Rate for family-safe content suitable for all ages",
            "comedy": "Rate purely for comedic value and humor quality"
        }
        
        specific_prompt = f"""
{self._create_assessment_prompt(post)}

SPECIAL FOCUS: {audience_prompts.get(audience_type, audience_prompts["general"])}

Adjust your rating based on this specific audience focus.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                messages=[{"role": "user", "content": specific_prompt}]
            )
            
            content = response.content[0].text
            rating, reasoning, improvements = self._parse_assessment_response(content)
            
            return {
                'rating': rating,
                'reasoning': reasoning,
                'improvements': improvements,
                'audience_type': audience_type,
                'assessed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Audience-specific assessment failed: {e}")
            return {
                'rating': 5.0,
                'reasoning': f"Assessment failed: {e}",
                'improvements': "Manual review required",
                'audience_type': audience_type,
                'assessed_at': datetime.utcnow().isoformat()
            }
    
    def batch_assess_with_comparison(self, posts: List[Dict]) -> List[Dict]:
        """
        Assess multiple posts and provide comparative analysis.
        
        Args:
            posts: List of Reddit post dictionaries
            
        Returns:
            Posts with comparative rankings and analysis
        """
        if len(posts) <= 1:
            return self.assess_humor_quality(posts)
        
        # First, get individual assessments
        assessed_posts = self.assess_humor_quality(posts, min_rating=1.0)  # Include all for comparison
        
        if len(assessed_posts) < 2:
            return assessed_posts
        
        # Create comparative analysis
        comparison_prompt = f"""
I have {len(assessed_posts)} Reddit posts that have been individually rated. 
Please provide a comparative ranking and explain which would work best for TikTok videos.

POSTS:
"""
        
        for i, post in enumerate(assessed_posts[:5], 1):  # Limit to top 5 for prompt length
            comparison_prompt += f"""
{i}. "{post['title']}" (r/{post['subreddit']}) - Individual Rating: {post['humor_rating']}/10
   Content: {post['selftext'][:200]}...
   
"""
        
        comparison_prompt += """
Rank these posts 1-5 for TikTok video creation, considering:
- Overall entertainment value
- TikTok audience appeal
- Text-to-speech suitability
- Viral potential

Format: Provide final rankings with brief justification for each.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": comparison_prompt}]
            )
            
            comparative_analysis = response.content[0].text
            
            # Add comparative analysis to the top post
            if assessed_posts:
                assessed_posts[0]['comparative_analysis'] = comparative_analysis
            
        except Exception as e:
            logger.warning(f"Comparative analysis failed: {e}")
        
        return assessed_posts
    
    def get_content_categories(self, post: Dict) -> List[str]:
        """
        Categorize content type for better video creation.
        
        Args:
            post: Reddit post dictionary
            
        Returns:
            List of content categories
        """
        categorization_prompt = f"""
Categorize this Reddit post for video creation purposes.

Title: {post['title']}
Content: {post['selftext'][:500]}
Subreddit: r/{post['subreddit']}

Select all applicable categories:
- STORY (narrative with beginning/middle/end)
- CONFESSION (personal admission or secret)
- ADVICE (seeking or giving advice)
- QUESTION (asking something to audience)
- RANT (venting or complaining)
- WHOLESOME (positive, uplifting content)
- CRINGE (awkward or embarrassing situations)
- RELATABLE (common experiences many share)
- SHOCKING (surprising or unexpected)
- EDUCATIONAL (teaches something new)

Respond with only the applicable categories, separated by commas.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": categorization_prompt}]
            )
            
            categories = [cat.strip().upper() for cat in response.content[0].text.split(',')]
            return [cat for cat in categories if cat in [
                'STORY', 'CONFESSION', 'ADVICE', 'QUESTION', 'RANT', 
                'WHOLESOME', 'CRINGE', 'RELATABLE', 'SHOCKING', 'EDUCATIONAL'
            ]]
            
        except Exception as e:
            logger.warning(f"Categorization failed: {e}")
            return ['GENERAL']


if __name__ == "__main__":
    # Test the content assessor
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Sample test post
    test_post = {
        'title': 'TIFU by accidentally sending my boss a meme instead of my resignation letter',
        'selftext': 'So this happened yesterday and I\'m still cringing. I was planning to quit my job and had typed up a professional resignation letter. At the same time, I was texting my friend a hilarious meme about office life. Guess which one I accidentally sent to my boss? Yep, the meme. He replied asking if this was my way of telling him I quit. I had to send the actual letter after that. Most awkward resignation ever.',
        'subreddit': 'tifu',
        'score': 1250,
        'url': 'https://reddit.com/r/tifu/test',
        'created_utc': 1234567890
    }
    
    try:
        assessor = ContentAssessor()
        
        print("Testing single post assessment...")
        result = assessor.assess_humor_quality([test_post])
        
        if result:
            post = result[0]
            print(f"\nAssessment Results:")
            print(f"Rating: {post['humor_rating']}/10")
            print(f"Reasoning: {post['assessment_reasoning']}")
            print(f"Improvements: {post['suggested_improvements']}")
        else:
            print("Post did not meet quality threshold")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
