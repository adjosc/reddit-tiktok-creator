from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
from typing import Dict

class VideoCreator:
    def __init__(self):
        self.output_dir = Path("output_videos")
        self.output_dir.mkdir(exist_ok=True)
    
    def create_tiktok_video(self, post: Dict, audio_path: str) -> str:
        """Create TikTok-style video from post and audio"""
        
        # Get audio duration
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # Create background (gradient or solid color)
        background = self._create_background(duration)
        
        # Create text overlay
        text_clip = self._create_text_overlay(post, duration)
        
        # Combine elements
        final_video = CompositeVideoClip([
            background,
            text_clip
        ]).set_audio(audio_clip)
        
        # Export for TikTok (9:16 aspect ratio, 1080x1920)
        output_path = self.output_dir / f"reddit_video_{post['created_utc']}.mp4"
        
        final_video.write_videofile(
            str(output_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile_path=str(self.output_dir / "temp_audio.m4a"),
            remove_temp=True
        )
        
        return str(output_path)
    
    def _create_background(self, duration: float) -> VideoClip:
        """Create animated background"""
        # Create gradient background
        img = Image.new('RGB', (1080, 1920), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect
        for i in range(1920):
            color_val = int(26 + (i / 1920) * 30)
            draw.line([(0, i), (1080, i)], fill=(color_val, color_val, 46))
        
        # Convert to video clip
        img_path = "temp_bg.png"
        img.save(img_path)
        
        background = ImageClip(img_path, duration=duration)
        os.remove(img_path)
        
        return background
    
    def _create_text_overlay(self, post: Dict, duration: float) -> TextClip:
        """Create animated text overlay"""
        
        # Format text for display
        title = post['title']
        content = post['selftext'][:200] + "..." if len(post['selftext']) > 200 else post['selftext']
        
        display_text = f"{title}\n\n{content}"
        
        # Create text clip
        text_clip = TextClip(
            display_text,
            fontsize=45,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(900, None),
            align='center'
        ).set_position('center').set_duration(duration)
        
        # Add fade in/out
        text_clip = text_clip.fadeout(0.5)
        
        return text_clip
