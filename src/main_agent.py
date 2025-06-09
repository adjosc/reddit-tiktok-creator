"""
Main Reddit to TikTok Video Creator Agent

LangGraph-powered workflow that orchestrates the entire video creation process.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, List, TypedDict, Optional, Any
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import os

from .reddit_fetcher import RedditFetcher
from .content_assessor import ContentAssessor
from .tts_generator import TTSGenerator
from .video_creator import VideoCreator
from .video_organizer import VideoOrganizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output_videos/logs/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State object that flows through the LangGraph workflow."""
    posts: List[Dict]
    selected_post: Dict
    optimized_script: str
    audio_path: str
    video_path: str
    metadata: Dict
    creation_status: str
    error_message: str
    creation_stats: Dict


class RedditTikTokAgent:
    """Main agent that orchestrates the Reddit to TikTok video creation workflow."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the agent with all components.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        try:
            self.reddit_fetcher = RedditFetcher()
            self.content_assessor = ContentAssessor()
            self.tts_generator = TTSGenerator()
            self.video_creator = VideoCreator()
            self.video_organizer = VideoOrganizer()
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            raise
        
        # Create logs directory
        logs_dir = Path("output_videos/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info("🤖 Reddit TikTok Agent initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        workflow = StateGraph(AgentState)
        
        # Add workflow nodes
        workflow.add_node("fetch_content", self.fetch_reddit_content)
        workflow.add_node("assess_quality", self.assess_content_quality)
        workflow.add_node("select_best", self.select_best_post)
        workflow.add_node("generate_script", self.generate_optimized_script)
        workflow.add_node("create_audio", self.create_tts_audio)
        workflow.add_node("create_video", self.create_final_video)
        workflow.add_node("organize_output", self.organize_and_save)
        
        # Define the workflow edges
        workflow.set_entry_point("fetch_content")
        workflow.add_edge("fetch_content", "assess_quality")
        workflow.add_edge("assess_quality", "select_best")
        workflow.add_edge("select_best", "generate_script")
        workflow.add_edge("generate_script", "create_audio")
        workflow.add_edge("create_audio", "create_video")
        workflow.add_edge("create_video", "organize_output")
        workflow.add_edge("organize_output", END)
        
        return workflow.compile()
    
    async def fetch_reddit_content(self, state: AgentState) -> AgentState:
        """
        Step 1: Fetch content from Reddit.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with fetched posts
        """
        logger.info("🔍 Step 1: Fetching Reddit content...")
        
        start_time = datetime.now()
        
        try:
            # Get configuration
            subreddits = self.config.get('subreddits')
            post_limit = self.config.get('post_limit', 20)
            time_filter = self.config.get('time_filter', 'day')
            
            # Fetch posts
            posts = self.reddit_fetcher.get_funny_posts(
                subreddits=subreddits,
                limit=post_limit,
                time_filter=time_filter
            )
            
            if not posts:
                state["creation_status"] = "failed"
                state["error_message"] = "No suitable posts found on Reddit"
                logger.warning("❌ No posts found")
                return state
            
            state["posts"] = posts
            
            # Track timing
            fetch_time = (datetime.now() - start_time).total_seconds()
            state["creation_stats"] = {"fetch_time": fetch_time}
            
            logger.info(f"✅ Fetched {len(posts)} posts in {fetch_time:.2f}s")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Reddit fetch failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"Reddit fetch error: {str(e)}"
            return state
    
    async def assess_content_quality(self, state: AgentState) -> AgentState:
        """
        Step 2: Assess content quality using AI.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with quality-assessed posts
        """
        logger.info("🤖 Step 2: Assessing content quality with AI...")
        
        start_time = datetime.now()
        
        try:
            posts = state["posts"]
            min_rating = self.config.get('min_humor_rating', 7.0)
            
            # Assess content quality
            assessed_posts = self.content_assessor.assess_humor_quality(
                posts, 
                min_rating=min_rating
            )
            
            if not assessed_posts:
                state["creation_status"] = "failed"
                state["error_message"] = f"No posts met quality threshold of {min_rating}/10"
                logger.warning(f"❌ No posts met quality threshold")
                return state
            
            state["posts"] = assessed_posts
            
            # Update timing
            assess_time = (datetime.now() - start_time).total_seconds()
            state["creation_stats"]["assess_time"] = assess_time
            
            logger.info(f"✅ Quality assessment complete: {len(assessed_posts)} posts passed ({assess_time:.2f}s)")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Content assessment failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"Assessment error: {str(e)}"
            return state
    
    async def select_best_post(self, state: AgentState) -> AgentState:
        """
        Step 3: Select the best post for video creation.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with selected post
        """
        logger.info("🎯 Step 3: Selecting best post...")
        
        try:
            posts = state["posts"]
            
            # Selection strategies
            selection_strategy = self.config.get('selection_strategy', 'highest_rated')
            
            if selection_strategy == 'highest_rated':
                # Select highest rated post
                best_post = max(posts, key=lambda p: p['humor_rating'])
            elif selection_strategy == 'most_upvoted':
                # Select most upvoted post
                best_post = max(posts, key=lambda p: p['score'])
            elif selection_strategy == 'best_engagement':
                # Select post with best engagement ratio
                best_post = max(posts, key=lambda p: p.get('num_comments', 0) / max(p['score'], 1))
            else:
                # Default to highest rated
                best_post = max(posts, key=lambda p: p['humor_rating'])
            
            state["selected_post"] = best_post
            
            logger.info(f"✅ Selected post: {best_post['title'][:50]}...")
            logger.info(f"   📊 Rating: {best_post['humor_rating']}/10")
            logger.info(f"   🔥 Score: {best_post['score']:,} upvotes")
            logger.info(f"   💬 Comments: {best_post.get('num_comments', 0):,}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Post selection failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"Selection error: {str(e)}"
            return state
    
    async def generate_optimized_script(self, state: AgentState) -> AgentState:
        """
        Step 4: Generate optimized script for TTS.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with optimized script
        """
        logger.info("📝 Step 4: Generating optimized script...")
        
        start_time = datetime.now()
        
        try:
            post = state["selected_post"]
            
            # Get script style from config
            script_style = self.config.get('script_style', 'engaging')
            
            # Generate script
            script = self.tts_generator.create_engaging_script(post, style=script_style)
            
            state["optimized_script"] = script
            
            # Update timing
            script_time = (datetime.now() - start_time).total_seconds()
            state["creation_stats"]["script_time"] = script_time
            
            logger.info(f"✅ Script generated ({len(script)} chars, {script_time:.2f}s)")
            logger.info(f"   Preview: {script[:100]}...")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Script generation failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"Script error: {str(e)}"
            return state
    
    async def create_tts_audio(self, state: AgentState) -> AgentState:
        """
        Step 5: Generate TTS audio from script.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with audio file path
        """
        logger.info("🎵 Step 5: Generating TTS audio...")
        
        start_time = datetime.now()
        
        try:
            script = state["optimized_script"]
            post = state["selected_post"]
            
            # Get voice configuration
            voice_style = self.config.get('voice_style')
            if not voice_style:
                voice_style = self.tts_generator.get_voice_for_content(post)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_audio_{timestamp}_{post['id']}.mp3"
            
            # Generate audio with fallback
            audio_path = await self.tts_generator.generate_with_fallback(
                script,
                audio_filename,
                voice_style
            )
            
            state["audio_path"] = audio_path
            
            # Update timing
            tts_time = (datetime.now() - start_time).total_seconds()
            state["creation_stats"]["tts_time"] = tts_time
            
            logger.info(f"✅ TTS audio generated ({tts_time:.2f}s)")
            logger.info(f"   📁 File: {Path(audio_path).name}")
            logger.info(f"   🎤 Voice: {voice_style}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"TTS error: {str(e)}"
            return state
    
    async def create_final_video(self, state: AgentState) -> AgentState:
        """
        Step 6: Create the final video.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with video file path
        """
        logger.info("🎬 Step 6: Creating final video...")
        
        start_time = datetime.now()
        
        try:
            post = state["selected_post"]
            audio_path = state["audio_path"]
            
            # Get video style from config
            video_style = self.config.get('video_style', 'modern')
            
            # Create video
            video_path = self.video_creator.create_tiktok_video(
                post,
                audio_path,
                style=video_style
            )
            
            state["video_path"] = video_path
            
            # Update timing
            video_time = (datetime.now() - start_time).total_seconds()
            state["creation_stats"]["video_time"] = video_time
            
            logger.info(f"✅ Video created ({video_time:.2f}s)")
            logger.info(f"   📁 File: {Path(video_path).name}")
            logger.info(f"   🎨 Style: {video_style}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Video creation failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"Video creation error: {str(e)}"
            return state
    
    async def organize_and_save(self, state: AgentState) -> AgentState:
        """
        Step 7: Organize output and save metadata.
        
        Args:
            state: Current agent state
            
        Returns:
            Final state with organization complete
        """
        logger.info("📁 Step 7: Organizing output and saving metadata...")
        
        start_time = datetime.now()
        
        try:
            post = state["selected_post"]
            video_path = state["video_path"]
            audio_path = state["audio_path"]
            creation_stats = state["creation_stats"]
            
            # Calculate total time
            total_time = (datetime.now() - datetime.fromisoformat(
                creation_stats.get('start_time', datetime.now().isoformat())
            )).total_seconds()
            creation_stats["total_time"] = total_time
            creation_stats["organize_time"] = (datetime.now() - start_time).total_seconds()
            
            # Save metadata and organize
            metadata = self.video_organizer.save_video_metadata(
                post,
                video_path,
                audio_path,
                creation_stats
            )
            
            state["metadata"] = metadata
            state["creation_status"] = "success"
            
            logger.info(f"✅ Organization complete")
            logger.info(f"   📊 Total time: {total_time:.2f}s")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Organization failed: {e}")
            state["creation_status"] = "failed"
            state["error_message"] = f"Organization error: {str(e)}"
            return state
    
    async def run(self, **config_overrides) -> Dict[str, Any]:
        """
        Run the complete video creation workflow.
        
        Args:
            **config_overrides: Configuration overrides
            
        Returns:
            Final state dictionary with results
        """
        logger.info("🚀 Starting Reddit to TikTok Video Creator Agent...")
        
        # Merge configuration
        run_config = {**self.config, **config_overrides}
        self.config = run_config
        
        # Initialize state
        initial_state = AgentState(
            posts=[],
            selected_post={},
            optimized_script="",
            audio_path="",
            video_path="",
            metadata={},
            creation_status="starting",
            error_message="",
            creation_stats={"start_time": datetime.now().isoformat()}
        )
        
        try:
            # Execute the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Print final results
            self._print_final_results(final_state)
            
            return final_state
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            return {
                "creation_status": "failed",
                "error_message": str(e),
                "creation_stats": initial_state["creation_stats"]
            }
    
    def _print_final_results(self, state: AgentState):
        """Print formatted final results."""
        
        print("\n" + "="*60)
        
        if state["creation_status"] == "success":
            print("🎉 VIDEO CREATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            
            metadata = state["metadata"]
            reddit_data = metadata["reddit_data"]
            video_info = metadata["video_info"]
            stats = state["creation_stats"]
            
            print(f"📹 Video: {Path(video_info['video_path']).name}")
            print(f"📊 Rating: {reddit_data['humor_rating']}/10")
            print(f"⏱️  Duration: {video_info['duration_seconds']:.1f}s")
            print(f"📁 Size: {video_info['file_size_mb']:.1f} MB")
            print(f"🕒 Total Time: {stats['total_time']:.1f}s")
            
            print(f"\n📝 Original Post:")
            print(f"   Title: {reddit_data['title']}")
            print(f"   Subreddit: r/{reddit_data['subreddit']}")
            print(f"   Score: {reddit_data['score']:,} upvotes")
            
            print(f"\n📱 Ready for TikTok Upload!")
            print(f"   Caption: {metadata['tiktok_content']['suggested_caption']}")
            
        else:
            print("❌ VIDEO CREATION FAILED")
            print("="*60)
            print(f"Error: {state['error_message']}")
        
        print("="*60 + "\n")
    
    def run_batch(self, count: int = 5, **config_overrides) -> List[Dict]:
        """
        Create multiple videos in a batch.
        
        Args:
            count: Number of videos to create
            **config_overrides: Configuration overrides
            
        Returns:
            List of results for each video
        """
        async def create_batch():
            results = []
            
            for i in range(count):
                logger.info(f"🎬 Creating video {i+1}/{count}...")
                
                try:
                    result = await self.run(**config_overrides)
                    results.append(result)
                    
                    if result["creation_status"] == "success":
                        logger.info(f"✅ Video {i+1}/{count} completed successfully")
                    else:
                        logger.warning(f"❌ Video {i+1}/{count} failed: {result['error_message']}")
                
                except Exception as e:
                    logger.error(f"❌ Video {i+1}/{count} crashed: {e}")
                    results.append({
                        "creation_status": "failed",
                        "error_message": str(e)
                    })
                
                # Small delay between videos
                if i < count - 1:
                    await asyncio.sleep(5)
            
            return results
        
        return asyncio.run(create_batch())
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics."""
        
        try:
            stats = self.video_organizer.get_creation_stats()
            queue = self.video_organizer.get_upload_queue()
            
            return {
                "agent_ready": True,
                "total_videos_created": stats.get("total_videos_created", 0),
                "average_humor_rating": stats.get("average_humor_rating", 0),
                "videos_ready_to_upload": len(queue),
                "most_popular_subreddit": max(stats.get("subreddits", {}).items(), 
                                            key=lambda x: x[1], default=("none", 0))[0],
                "components_status": {
                    "reddit_fetcher": "ready",
                    "content_assessor": "ready",
                    "tts_generator": "ready", 
                    "video_creator": "ready",
                    "video_organizer": "ready"
                }
            }
            
        except Exception as e:
            return {
                "agent_ready": False,
                "error": str(e)
            }


# Main execution functions
async def main():
    """Main execution function for running the agent."""
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Default configuration
        config = {
            'subreddits': ['funny', 'tifu', 'confession', 'wholesome'],
            'post_limit': 15,
            'min_humor_rating': 7.0,
            'script_style': 'engaging',
            'video_style': 'modern',
            'selection_strategy': 'highest_rated'
        }
        
        # Create and run agent
        agent = RedditTikTokAgent(config)
        result = await agent.run()
        
        # Show videos list
        print("\n📚 Recent Videos:")
        agent.video_organizer.list_created_videos(limit=5)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise


def run_agent(**config_overrides):
    """Synchronous wrapper to run the agent."""
    return asyncio.run(main())


if __name__ == "__main__":
    import sys
    
    try:
        result = run_agent()
        if result["creation_status"] == "success":
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

