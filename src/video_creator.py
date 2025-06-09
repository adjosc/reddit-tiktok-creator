"""
Video Creator

Creates TikTok-style videos from Reddit content with professional visuals and animations.
"""

from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import colorsys

logger = logging.getLogger(__name__)


class VideoCreator:
    """Creates engaging TikTok-style videos from Reddit content and audio."""
    
    def __init__(self):
        """Initialize video creator with TikTok specifications."""
        self.output_dir = Path("output_videos")
        self.output_dir.mkdir(exist_ok=True)
        
        # TikTok video specifications
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.aspect_ratio = 9/16
        
        # Asset directories
        self.assets_dir = Path("assets")
        self.backgrounds_dir = self.assets_dir / "backgrounds"
        self.fonts_dir = self.assets_dir / "fonts"
        
        # Create asset directories
        self.assets_dir.mkdir(exist_ok=True)
        self.backgrounds_dir.mkdir(exist_ok=True)
        self.fonts_dir.mkdir(exist_ok=True)
        
        # Color schemes for different content types
        self.color_schemes = {
            'tifu': {
                'bg_gradient': ['#FF6B6B', '#4ECDC4'],  # Red to teal
                'text_color': 'white',
                'accent': '#FFE66D'
            },
            'confession': {
                'bg_gradient': ['#667eea', '#764ba2'],  # Blue purple gradient
                'text_color': 'white', 
                'accent': '#f093fb'
            },
            'funny': {
                'bg_gradient': ['#FDBB2D', '#22C1C3'],  # Orange to cyan
                'text_color': 'white',
                'accent': '#FF6B6B'
            },
            'wholesome': {
                'bg_gradient': ['#a8edea', '#fed6e3'],  # Mint to pink
                'text_color': '#2c3e50',
                'accent': '#3498db'
            },
            'default': {
                'bg_gradient': ['#1a1a2e', '#16213e'],  # Dark theme
                'text_color': 'white',
                'accent': '#0f3460'
            }
        }
        
        logger.info("Video creator initialized")
    
    def create_tiktok_video(self, 
                           post: Dict, 
                           audio_path: str,
                           style: str = "modern") -> str:
        """
        Create a complete TikTok video from post and audio.
        
        Args:
            post: Reddit post dictionary
            audio_path: Path to generated audio file
            style: Video style ("modern", "minimal", "dynamic", "story")
            
        Returns:
            Path to created video file
        """
        try:
            logger.info(f"Creating {style} style video for: {post['title'][:50]}...")
            
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            logger.info(f"Audio duration: {duration:.2f} seconds")
            
            # Create video elements based on style
            if style == "dynamic":
                video_clip = self._create_dynamic_video(post, duration)
            elif style == "minimal":
                video_clip = self._create_minimal_video(post, duration)
            elif style == "story":
                video_clip = self._create_story_video(post, duration)
            else:  # modern (default)
                video_clip = self._create_modern_video(post, duration)
            
            # Add audio
            final_video = video_clip.set_audio(audio_clip)
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in post['title'][:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            output_filename = f"reddit_video_{timestamp}_{safe_title}.mp4"
            output_path = self.output_dir / output_filename
            
            # Export video
            logger.info("Exporting video...")
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile_path=str(self.output_dir / "temp_audio.m4a"),
                remove_temp=True,
                preset='medium',  # Balance quality and speed
                ffmpeg_params=['-crf', '23']  # Good quality compression
            )
            
            # Cleanup
            audio_clip.close()
            final_video.close()
            
            logger.info(f"✅ Video created: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            raise
    
    def _create_modern_video(self, post: Dict, duration: float) -> VideoClip:
        """Create a modern-style video with gradients and animations."""
        
        # Get color scheme
        subreddit = post['subreddit'].lower()
        colors = self.color_schemes.get(subreddit, self.color_schemes['default'])
        
        # Create animated background
        background = self._create_animated_gradient_background(colors['bg_gradient'], duration)
        
        # Create title card
        title_clip = self._create_animated_title(
            post['title'], 
            duration,
            colors['text_color'],
            colors['accent']
        )
        
        # Create content text (if content exists and isn't too long)
        content_clips = []
        if post['selftext'] and len(post['selftext']) > 50:
            content_clips = self._create_scrolling_content(
                post['selftext'],
                duration,
                colors['text_color']
            )
        
        # Create subreddit badge
        badge_clip = self._create_subreddit_badge(
            post['subreddit'],
            duration,
            colors['accent']
        )
        
        # Combine all elements
        all_clips = [background, title_clip, badge_clip] + content_clips
        
        return CompositeVideoClip(all_clips, size=(self.width, self.height))
    
    def _create_dynamic_video(self, post: Dict, duration: float) -> VideoClip:
        """Create a dynamic video with moving elements and effects."""
        
        # Animated particle background
        background = self._create_particle_background(duration)
        
        # Title with typewriter effect
        title_clip = self._create_typewriter_title(post['title'], duration)
        
        # Floating elements
        floating_clips = self._create_floating_elements(duration)
        
        # Content with reveal animation
        content_clip = self._create_reveal_content(post['selftext'], duration)
        
        # Stats display
        stats_clip = self._create_stats_display(post, duration)
        
        all_clips = [background, title_clip, content_clip, stats_clip] + floating_clips
        
        return CompositeVideoClip(all_clips, size=(self.width, self.height))
    
    def _create_minimal_video(self, post: Dict, duration: float) -> VideoClip:
        """Create a clean, minimal video focused on readability."""
        
        # Simple solid background
        bg_color = '#f8f9fa'  # Light gray
        background = ColorClip(size=(self.width, self.height), color=bg_color, duration=duration)
        
        # Clean typography
        title_clip = self._create_clean_title(post['title'], duration)
        content_clip = self._create_clean_content(post['selftext'], duration)
        
        # Simple subreddit indicator
        source_clip = self._create_simple_source(post['subreddit'], duration)
        
        return CompositeVideoClip([background, title_clip, content_clip, source_clip], 
                                size=(self.width, self.height))
    
    def _create_story_video(self, post: Dict, duration: float) -> VideoClip:
        """Create a story-style video with scene transitions."""
        
        # Multiple background scenes
        scenes = self._create_story_scenes(post, duration)
        
        # Progressive text reveal
        story_text = self._create_progressive_story_text(post, duration)
        
        # Scene transitions
        transition_clips = self._create_scene_transitions(duration)
        
        all_clips = scenes + [story_text] + transition_clips
        
        return CompositeVideoClip(all_clips, size=(self.width, self.height))
    
    def _create_animated_gradient_background(self, colors: List[str], duration: float) -> VideoClip:
        """Create an animated gradient background."""
        
        def make_frame(t):
            # Create gradient that shifts over time
            angle = (t / duration) * 360  # Full rotation over video duration
            
            img = Image.new('RGB', (self.width, self.height))
            draw = ImageDraw.Draw(img)
            
            # Convert hex colors to RGB
            color1 = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
            color2 = tuple(int(colors[1][i:i+2], 16) for i in (1, 3, 5))
            
            # Create diagonal gradient
            for y in range(self.height):
                # Calculate gradient position with animation
                progress = (y + t * 100) % self.height / self.height
                
                # Interpolate between colors
                r = int(color1[0] + (color2[0] - color1[0]) * progress)
                g = int(color1[1] + (color2[1] - color1[1]) * progress)
                b = int(color1[2] + (color2[2] - color1[2]) * progress)
                
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
            
            return np.array(img)
        
        return VideoClip(make_frame, duration=duration)
    
    def _create_animated_title(self, 
                             title: str, 
                             duration: float,
                             text_color: str = 'white',
                             accent_color: str = '#FF6B6B') -> TextClip:
        """Create an animated title with effects."""
        
        # Clean title for display
        display_title = title[:80] + "..." if len(title) > 80 else title
        
        # Create main title
        title_clip = TextClip(
            display_title,
            fontsize=55,
            color=text_color,
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(900, None),
            align='center'
        ).set_position('center').set_duration(duration)
        
        # Add slide-in animation
        title_clip = title_clip.set_position(lambda t: ('center', 200 + max(0, 100 - t * 200)))
        
        # Add fade-in effect
        title_clip = title_clip.fadein(0.5)
        
        return title_clip
    
    def _create_scrolling_content(self, 
                                content: str, 
                                duration: float,
                                text_color: str = 'white') -> List[TextClip]:
        """Create scrolling content text."""
        
        if not content or len(content) < 50:
            return []
        
        # Split content into chunks for better readability
        words = content.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(' '.join(current_chunk)) > 200:  # ~3 lines of text
                chunks.append(' '.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        clips = []
        chunk_duration = duration / max(1, len(chunks))
        
        for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
            start_time = i * chunk_duration
            
            text_clip = TextClip(
                chunk,
                fontsize=35,
                color=text_color,
                font='Arial',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(800, None),
                align='center'
            ).set_start(start_time).set_duration(chunk_duration).set_position(('center', 500))
            
            # Add slide-up animation
            text_clip = text_clip.set_position(lambda t, i=i: ('center', 500 - min(50, t * 100)))
            
            clips.append(text_clip)
        
        return clips
    
    def _create_subreddit_badge(self, 
                              subreddit: str, 
                              duration: float,
                              accent_color: str = '#FF6B6B') -> TextClip:
        """Create a subreddit badge/watermark."""
        
        badge_text = f"r/{subreddit}"
        
        badge_clip = TextClip(
            badge_text,
            fontsize=30,
            color='white',
            font='Arial-Bold',
            stroke_color=accent_color,
            stroke_width=2
        ).set_position((50, 100)).set_duration(duration)
        
        # Add subtle fade-in
        badge_clip = badge_clip.fadein(1.0)
        
        return badge_clip
    
    def _create_typewriter_title(self, title: str, duration: float) -> CompositeVideoClip:
        """Create typewriter effect for title."""
        
        clips = []
        chars_per_second = max(10, len(title) / (duration * 0.3))  # Finish typing in first 30% of video
        
        for i in range(1, len(title) + 1):
            partial_text = title[:i]
            start_time = (i - 1) / chars_per_second
            
            if start_time >= duration:
                break
            
            text_clip = TextClip(
                partial_text,
                fontsize=50,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            ).set_start(start_time).set_duration(duration - start_time).set_position('center')
            
            clips.append(text_clip)
        
        return CompositeVideoClip(clips)
    
    def _create_particle_background(self, duration: float) -> VideoClip:
        """Create animated particle background."""
        
        def make_frame(t):
            img = Image.new('RGB', (self.width, self.height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # Create moving particles
            num_particles = 50
            for i in range(num_particles):
                # Particle position based on time and particle index
                x = ((i * 73 + t * 20) % self.width)
                y = ((i * 97 + t * 15) % self.height)
                
                # Particle size varies
                size = 2 + (i % 4)
                
                # Particle color (subtle)
                opacity = int(100 + 50 * math.sin(t + i))
                color = (opacity, opacity, opacity)
                
                draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
            
            return np.array(img)
        
        return VideoClip(make_frame, duration=duration)
    
    def _create_floating_elements(self, duration: float) -> List[VideoClip]:
        """Create floating decorative elements."""
        
        elements = []
        
        # Create floating circles
        for i in range(5):
            def make_circle_frame(t, offset=i):
                img = Image.new('RGBA', (100, 100), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Animated opacity
                opacity = int(50 + 25 * math.sin(t + offset))
                color = (255, 255, 255, opacity)
                
                draw.ellipse([20, 20, 80, 80], outline=color, width=3)
                return np.array(img)
            
            circle_clip = VideoClip(lambda t, o=i: make_circle_frame(t, o), duration=duration)
            
            # Floating animation
            x_pos = 100 + i * 200
            y_func = lambda t, offset=i: 300 + 50 * math.sin(t * 0.5 + offset)
            circle_clip = circle_clip.set_position(lambda t, x=x_pos: (x, y_func(t)))
            
            elements.append(circle_clip)
        
        return elements
    
    def _create_clean_title(self, title: str, duration: float) -> TextClip:
        """Create clean, readable title for minimal style."""
        
        return TextClip(
            title,
            fontsize=45,
            color='#2c3e50',
            font='Arial-Bold',
            method='caption',
            size=(900, None),
            align='center'
        ).set_position(('center', 300)).set_duration(duration).fadein(0.5)
    
    def _create_clean_content(self, content: str, duration: float) -> TextClip:
        """Create clean content text for minimal style."""
        
        if not content:
            return TextClip("", duration=0)
        
        # Limit content length
        display_content = content[:400] + "..." if len(content) > 400 else content
        
        return TextClip(
            display_content,
            fontsize=30,
            color='#34495e',
            font='Arial',
            method='caption',
            size=(800, None),
            align='center'
        ).set_position(('center', 600)).set_duration(duration).fadein(1.0)
    
    def _create_simple_source(self, subreddit: str, duration: float) -> TextClip:
        """Create simple source attribution."""
        
        return TextClip(
            f"via r/{subreddit}",
            fontsize=25,
            color='#7f8c8d',
            font='Arial'
        ).set_position((50, self.height - 100)).set_duration(duration).fadein(1.0)
    
    def _get_safe_font_size(self, text: str, max_width: int) -> int:
        """Calculate safe font size for given text and width."""
        
        # Rough approximation: 1 character ≈ 0.6 * font_size pixels width
        chars_per_line = max_width / 30  # Assuming 30px average char width
        lines_needed = len(text) / chars_per_line
        
        if lines_needed <= 2:
            return 45
        elif lines_needed <= 3:
            return 35
        else:
            return 25
    
    def _create_stats_display(self, post: Dict, duration: float) -> CompositeVideoClip:
        """Create animated stats display (upvotes, comments)."""
        
        stats_clips = []
        
        # Upvotes
        upvote_text = f"⬆ {post['score']:,}"
        upvote_clip = TextClip(
            upvote_text,
            fontsize=25,
            color='#FF4500',
            font='Arial-Bold'
        ).set_position((50, self.height - 200)).set_duration(duration).fadein(1.5)
        
        stats_clips.append(upvote_clip)
        
        # Comments
        if 'num_comments' in post:
            comment_text = f"💬 {post['num_comments']:,}"
            comment_clip = TextClip(
                comment_text,
                fontsize=25,
                color='#1DA1F2',
                font='Arial-Bold'
            ).set_position((50, self.height - 160)).set_duration(duration).fadein(2.0)
            
            stats_clips.append(comment_clip)
        
        return CompositeVideoClip(stats_clips)
    
    def _create_reveal_content(self, content: str, duration: float) -> TextClip:
        """Create content with reveal animation."""
        
        if not content:
            return TextClip("", duration=0)
        
        # Limit and clean content
        display_content = content[:300] + "..." if len(content) > 300 else content
        
        content_clip = TextClip(
            display_content,
            fontsize=32,
            color='white',
            font='Arial',
            stroke_color='black',
            stroke_width=1,
            method='caption',
            size=(850, None),
            align='center'
        ).set_position(('center', 700)).set_duration(duration)
        
        # Slide up reveal
        content_clip = content_clip.set_position(lambda t: ('center', 700 + max(0, 200 - t * 400)))
        content_clip = content_clip.fadein(1.0)
        
        return content_clip
    
    def _create_story_scenes(self, post: Dict, duration: float) -> List[VideoClip]:
        """Create multiple background scenes for story style."""
        
        scenes = []
        scene_duration = duration / 3
        
        # Scene 1: Setup
        scene1 = ColorClip(size=(self.width, self.height), color='#2c3e50', duration=scene_duration)
        scenes.append(scene1)
        
        # Scene 2: Development 
        scene2 = ColorClip(size=(self.width, self.height), color='#34495e', duration=scene_duration).set_start(scene_duration)
        scenes.append(scene2)
        
        # Scene 3: Resolution
        scene3 = ColorClip(size=(self.width, self.height), color='#1abc9c', duration=scene_duration).set_start(scene_duration * 2)
        scenes.append(scene3)
        
        return scenes
    
    def _create_progressive_story_text(self, post: Dict, duration: float) -> CompositeVideoClip:
        """Create progressive text reveal for story style."""
        
        title = post['title']
        content = post['selftext'][:400] if post['selftext'] else ""
        
        clips = []
        
        # Title appears first
        title_clip = TextClip(
            title,
            fontsize=40,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(800, None),
            align='center'
        ).set_position(('center', 300)).set_duration(duration * 0.4).fadein(0.5).fadeout(0.5)
        
        clips.append(title_clip)
        
        # Content appears second
        if content:
            content_clip = TextClip(
                content,
                fontsize=30,
                color='white',
                font='Arial',
                stroke_color='black',
                stroke_width=1,
                method='caption',
                size=(700, None),
                align='center'
            ).set_start(duration * 0.3).set_duration(duration * 0.7).set_position(('center', 600)).fadein(0.5)
            
            clips.append(content_clip)
        
        return CompositeVideoClip(clips)
    
    def _create_scene_transitions(self, duration: float) -> List[VideoClip]:
        """Create transition effects between scenes."""
        
        transitions = []
        
        # Simple fade transitions
        for i in range(2):
            transition_time = duration / 3 * (i + 1)
            
            fade_clip = ColorClip(
                size=(self.width, self.height), 
                color='black', 
                duration=0.5
            ).set_start(transition_time - 0.25).set_opacity(0.3)
            
            transitions.append(fade_clip)
        
        return transitions


if __name__ == "__main__":
    # Test the video creator
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Sample test data
    test_post = {
        'title': 'TIFU by accidentally sending a love text to my boss',
        'selftext': 'So this happened yesterday and I am still cringing. I was texting my girlfriend about our dinner plans and meant to send her "Can\'t wait to see you tonight, love you!" But somehow I sent it to my boss instead. He just replied "Thanks but I\'m married." Most awkward Monday ever.',
        'subreddit': 'tifu',
        'score': 2500,
        'num_comments': 156
    }
    
    try:
        creator = VideoCreator()
        
        # Create a sample audio file path (in real use, this would come from TTS)
        print("Note: This test requires an actual audio file to create a complete video.")
        print("Run this after generating TTS audio in the main workflow.")
        
        print("Video creator initialized successfully!")
        print(f"Output directory: {creator.output_dir}")
        print(f"Video dimensions: {creator.width}x{creator.height}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
