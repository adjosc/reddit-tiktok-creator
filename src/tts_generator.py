"""
Text-to-Speech Generator

Handles generating natural-sounding speech from Reddit content using OpenAI TTS and Edge TTS.
"""

import openai
import os
import asyncio
import aiofiles
import re
import random
from pathlib import Path
from typing import Dict, Optional, List
import logging
from datetime import datetime

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("Edge TTS not available. Install with: pip install edge-tts")

logger = logging.getLogger(__name__)


class TTSGenerator:
    """Generates high-quality text-to-speech audio from Reddit content."""
    
    def __init__(self):
        """Initialize TTS services."""
        # OpenAI setup
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Audio output setup
        self.output_dir = Path("output_videos/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice configurations
        self.openai_voices = {
            'funny_male': 'onyx',      # Deep, authoritative
            'funny_female': 'nova',     # Warm, engaging
            'story_male': 'echo',       # Conversational, friendly
            'story_female': 'shimmer',  # Clear, expressive
            'dramatic': 'fable',        # Expressive, dramatic
            'casual': 'alloy'           # Neutral, versatile
        }
        
        self.edge_voices = {
            'funny_male': 'en-US-ChristopherNeural',
            'funny_female': 'en-US-JennyNeural', 
            'story_male': 'en-US-GuyNeural',
            'story_female': 'en-US-AriaNeural',
            'dramatic': 'en-US-DavisNeural',
            'casual': 'en-US-AmberNeural'
        }
        
        logger.info("TTS Generator initialized")
    
    async def generate_speech_openai(self, 
                                   text: str, 
                                   output_path: str,
                                   voice_style: str = "funny_male",
                                   speed: float = 1.1) -> str:
        """
        Generate speech using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            output_path: Output file path
            voice_style: Voice style key
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Path to generated audio file
        """
        voice = self.openai_voices.get(voice_style, 'onyx')
        
        try:
            logger.info(f"Generating OpenAI TTS with voice '{voice}' at speed {speed}x")
            
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # Higher quality model
                voice=voice,
                input=text,
                speed=speed
            )
            
            # Save audio file
            output_path = str(self.output_dir / output_path)
            response.stream_to_file(output_path)
            
            logger.info(f"✅ OpenAI TTS generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise
    
    async def generate_speech_edge(self, 
                                 text: str, 
                                 output_path: str,
                                 voice_style: str = "funny_male",
                                 rate: str = "+10%") -> str:
        """
        Generate speech using Edge TTS (free alternative).
        
        Args:
            text: Text to convert to speech
            output_path: Output file path
            voice_style: Voice style key
            rate: Speech rate adjustment
            
        Returns:
            Path to generated audio file
        """
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("Edge TTS not available. Install with: pip install edge-tts")
        
        voice = self.edge_voices.get(voice_style, 'en-US-AriaNeural')
        output_path = str(self.output_dir / output_path)
        
        try:
            logger.info(f"Generating Edge TTS with voice '{voice}' at rate {rate}")
            
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(output_path)
            
            logger.info(f"✅ Edge TTS generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Edge TTS failed: {e}")
            raise
    
    def create_engaging_script(self, post: Dict, style: str = "engaging") -> str:
        """
        Create a TikTok-optimized script from Reddit post.
        
        Args:
            post: Reddit post dictionary
            style: Script style ("engaging", "dramatic", "casual", "story")
            
        Returns:
            Optimized script for TTS
        """
        title = post['title']
        content = post['selftext']
        subreddit = post['subreddit']
        
        # Choose intro based on style and subreddit
        intro = self._get_intro(subreddit, style)
        
        # Create hook and main content
        hook = self._create_hook(title, subreddit)
        main_content = self._format_content(content, style)
        
        # Combine elements
        if style == "dramatic":
            script = f"{intro} {hook} {main_content}"
        elif style == "story":
            script = f"{hook} {main_content}"
        else:  # engaging, casual
            script = f"{intro} {hook} {main_content}"
        
        # Clean and optimize for TTS
        script = self._optimize_for_tts(script)
        
        # Ensure appropriate length (TikTok time limits)
        script = self._ensure_optimal_length(script)
        
        logger.info(f"Created {style} script: {len(script)} characters")
        return script
    
    def _get_intro(self, subreddit: str, style: str) -> str:
        """Get appropriate intro based on subreddit and style."""
        
        intros = {
            'tifu': {
                'engaging': [
                    "Someone just shared the most embarrassing story on Reddit!",
                    "This person really messed up, and you won't believe what happened!",
                    "Here's a story that will make you feel better about your worst day!"
                ],
                'dramatic': [
                    "A tale of epic failure has emerged from Reddit...",
                    "One person's mistake changed everything...",
                    "What started as a normal day became a disaster..."
                ],
                'casual': [
                    "So this person on Reddit had quite the day...",
                    "Someone shared their epic fail story...",
                    "Here's what happened when everything went wrong..."
                ]
            },
            'amitheasshole': {
                'engaging': [
                    "Someone's asking Reddit to judge their situation!",
                    "This moral dilemma has Reddit divided!",
                    "You be the judge of this dramatic story!"
                ],
                'dramatic': [
                    "A moral crisis has divided the internet...",
                    "One decision sparked a family crisis...",
                    "Justice hangs in the balance..."
                ]
            },
            'confession': {
                'engaging': [
                    "Someone just shared their biggest secret!",
                    "This confession will blow your mind!",
                    "Reddit user finally tells the truth!"
                ],
                'dramatic': [
                    "A secret has been revealed that changes everything...",
                    "Years of hiding the truth end today...",
                    "One confession shattered their world..."
                ]
            },
            'default': {
                'engaging': [
                    "You won't believe what happened on Reddit today!",
                    "This Reddit story is absolutely wild!",
                    "Someone just shared the craziest experience!",
                    "This story from Reddit will amaze you!"
                ],
                'dramatic': [
                    "A story has emerged that will leave you speechless...",
                    "What happened next changed everything...",
                    "One moment changed their life forever..."
                ],
                'casual': [
                    "So someone on Reddit shared this story...",
                    "Here's what happened to this Reddit user...",
                    "Someone had quite the experience..."
                ]
            }
        }
        
        subreddit_intros = intros.get(subreddit, intros['default'])
        style_intros = subreddit_intros.get(style, subreddit_intros.get('engaging', []))
        
        if not style_intros:
            style_intros = intros['default']['engaging']
        
        return random.choice(style_intros)
    
    def _create_hook(self, title: str, subreddit: str) -> str:
        """Create an engaging hook from the title."""
        # Clean title
        title = re.sub(r'^(TIFU|AITA|LPT|PSA|UPDATE):\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(.*?\)\s*', '', title)  # Remove parenthetical
        
        # Add excitement based on content
        if any(word in title.lower() for word in ['accidentally', 'mistake', 'wrong', 'oops']):
            return f"Get this: {title}!"
        elif any(word in title.lower() for word in ['secret', 'confession', 'never told']):
            return f"Here's the secret: {title}."
        elif '?' in title:
            return f"They asked: {title}"
        else:
            return f"{title}."
    
    def _format_content(self, content: str, style: str) -> str:
        """Format the main content based on style."""
        if not content or len(content) < 20:
            return "Check out the full story to see what happened next!"
        
        # Split into paragraphs and clean
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        if style == "dramatic":
            # Add dramatic pauses and emphasis
            formatted = []
            for para in paragraphs[:3]:  # Limit paragraphs
                para = re.sub(r'\. ', '. ... ', para)  # Add pauses
                formatted.append(para)
            content = ' '.join(formatted)
            
        elif style == "story":
            # Natural storytelling flow
            content = ' '.join(paragraphs[:4])
            content = re.sub(r'\bAnd\b', 'Then', content)  # Better flow
            
        else:  # engaging, casual
            # Keep it snappy and engaging
            content = ' '.join(paragraphs[:3])
        
        return content
    
    def _optimize_for_tts(self, script: str) -> str:
        """Optimize script for text-to-speech clarity."""
        
        # Fix common TTS issues
        replacements = {
            # Numbers and symbols
            '&': 'and',
            '%': 'percent',
            '@': 'at',
            '#': 'hashtag',
            '$': 'dollars',
            '+': 'plus',
            '=': 'equals',
            
            # Internet slang
            'lol': 'laugh out loud',
            'omg': 'oh my god',
            'wtf': 'what the heck',
            'tbh': 'to be honest',
            'imo': 'in my opinion',
            'rn': 'right now',
            'ur': 'your',
            'u': 'you',
            
            # Reddit specific
            'op': 'original poster',
            'so': 'significant other',
            'bf': 'boyfriend',
            'gf': 'girlfriend',
            'mil': 'mother in law',
            'fil': 'father in law',
            
            # Improve flow
            'etc.': 'and so on',
            'i.e.': 'that is',
            'e.g.': 'for example',
            'vs.': 'versus'
        }
        
        # Apply replacements (case insensitive)
        for old, new in replacements.items():
            script = re.sub(rf'\b{re.escape(old)}\b', new, script, flags=re.IGNORECASE)
        
        # Fix punctuation for better speech flow
        script = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', script)  # Ensure space after sentences
        script = re.sub(r'([,;:])\s*', r'\1 ', script)  # Space after punctuation
        script = re.sub(r'\s+', ' ', script)  # Normalize whitespace
        
        # Add pauses for better pacing
        script = re.sub(r'([.!?])\s+', r'\1 ... ', script)  # Pauses between sentences
        
        return script.strip()
    
    def _ensure_optimal_length(self, script: str, max_chars: int = 1000) -> str:
        """Ensure script is optimal length for TikTok."""
        if len(script) <= max_chars:
            return script
        
        # Truncate at sentence boundary
        sentences = re.split(r'[.!?]+', script)
        truncated = ""
        
        for sentence in sentences:
            if len(truncated + sentence) + 1 <= max_chars - 50:  # Leave room for ending
                truncated += sentence + ". "
            else:
                break
        
        # Add engaging ending
        endings = [
            "What would you have done?",
            "Let me know what you think in the comments!",
            "Would you make the same choice?",
            "Share your thoughts below!",
            "What's your take on this?"
        ]
        
        truncated += random.choice(endings)
        return truncated
    
    def get_voice_for_content(self, post: Dict) -> str:
        """Suggest best voice style based on content type."""
        title = post['title'].lower()
        content = post['selftext'].lower()
        subreddit = post['subreddit'].lower()
        
        # Analyze content type
        if subreddit in ['tifu', 'confession']:
            if any(word in title + content for word in ['embarrass', 'awkward', 'cringe']):
                return 'funny_male'
            else:
                return 'story_male'
                
        elif subreddit in ['amitheasshole', 'relationship_advice']:
            return 'dramatic'
            
        elif subreddit in ['wholesome', 'mademesmile']:
            return 'funny_female'
            
        elif any(word in title + content for word in ['story', 'happened', 'experience']):
            return 'story_female'
            
        else:
            return 'casual'
    
    async def generate_with_fallback(self, 
                                   text: str, 
                                   output_filename: str,
                                   voice_style: str = "funny_male") -> str:
        """
        Generate TTS with OpenAI, fall back to Edge TTS if needed.
        
        Args:
            text: Text to convert
            output_filename: Output filename (without path)
            voice_style: Voice style to use
            
        Returns:
            Path to generated audio file
        """
        try:
            # Try OpenAI first (higher quality)
            return await self.generate_speech_openai(text, output_filename, voice_style)
            
        except Exception as openai_error:
            logger.warning(f"OpenAI TTS failed: {openai_error}")
            
            if EDGE_TTS_AVAILABLE:
                logger.info("Falling back to Edge TTS...")
                try:
                    return await self.generate_speech_edge(text, output_filename, voice_style)
                except Exception as edge_error:
                    logger.error(f"Edge TTS also failed: {edge_error}")
                    raise edge_error
            else:
                raise openai_error


if __name__ == "__main__":
    # Test the TTS generator
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Sample test post
    test_post = {
        'title': 'TIFU by accidentally texting my ex instead of my mom',
        'selftext': 'So this happened this morning and I\'m still mortified. I was trying to text my mom about dinner plans, but I accidentally sent it to my ex who I haven\'t talked to in months. The text said "Can\'t wait to see you tonight, love you!" She responded with "Um, wrong number?" Most awkward moment of my life.',
        'subreddit': 'tifu'
    }
    
    async def test_tts():
        try:
            tts = TTSGenerator()
            
            # Create script
            script = tts.create_engaging_script(test_post, style="engaging")
            print(f"Generated script: {script}")
            
            # Get voice recommendation
            voice = tts.get_voice_for_content(test_post)
            print(f"Recommended voice: {voice}")
            
            # Generate audio
            audio_path = await tts.generate_with_fallback(
                script, 
                "test_audio.mp3", 
                voice
            )
            print(f"Audio generated: {audio_path}")
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(test_tts())
