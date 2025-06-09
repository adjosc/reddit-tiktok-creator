import openai
import os
from pathlib import Path
import edge_tts
import asyncio

class TTSGenerator:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def generate_speech_openai(self, text: str, output_path: str, voice="onyx"):
        """Generate speech using OpenAI TTS"""
        response = self.openai_client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,  # alloy, echo, fable, onyx, nova, shimmer
            input=text,
            speed=1.1  # Slightly faster for TikTok
        )
        
        response.stream_to_file(output_path)
    
    async def generate_speech_edge(self, text: str, output_path: str, voice="en-US-AriaNeural"):
        """Generate speech using Edge TTS (free alternative)"""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
    
    def create_engaging_script(self, post: Dict) -> str:
        """Create TikTok-optimized script from Reddit post"""
        title = post['title']
        content = post['selftext']
        
        # Add engaging intro
        intros = [
            "You won't believe what happened on Reddit today!",
            "This Reddit story is absolutely wild!",
            "Wait until you hear this Reddit confession!",
            "This person just shared the funniest story!"
        ]
        
        import random
        intro = random.choice(intros)
        
        # Clean and format content
        script = f"{intro} {title}. {content}"
        
        # Clean up formatting for TTS
        script = script.replace('\n', '. ')
        script = script.replace('  ', ' ')
        
        return script[:800]  # Keep under TikTok time limits
