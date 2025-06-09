from langgraph.graph import StateGraph, END
from typing import Dict, List, TypedDict
import asyncio
from datetime import datetime

class AgentState(TypedDict):
    posts: List[Dict]
    selected_post: Dict
    audio_path: str
    video_path: str
    upload_status: str

class RedditTikTokAgent:
    def __init__(self):
        self.reddit_fetcher = RedditFetcher()
        self.content_assessor = ContentAssessor()
        self.tts_generator = TTSGenerator()
        self.video_creator = VideoCreator()
        self.tiktok_uploader = TikTokUploader()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("fetch_posts", self.fetch_posts)
        workflow.add_node("assess_content", self.assess_content)
        workflow.add_node("select_best_post", self.select_best_post)
        workflow.add_node("generate_audio", self.generate_audio)
        workflow.add_node("create_video", self.create_video)
        workflow.add_node("upload_to_tiktok", self.upload_to_tiktok)
        
        # Define flow
        workflow.set_entry_point("fetch_posts")
        workflow.add_edge("fetch_posts", "assess_content")
        workflow.add_edge("assess_content", "select_best_post")
        workflow.add_edge("select_best_post", "generate_audio")
        workflow.add_edge("generate_audio", "create_video")
        workflow.add_edge("create_video", "upload_to_tiktok")
        workflow.add_edge("upload_to_tiktok", END)
        
        return workflow.compile()
    
    async def fetch_posts(self, state: AgentState) -> AgentState:
        """Fetch funny posts from Reddit"""
        print("🔍 Fetching Reddit posts...")
        posts = self.reddit_fetcher.get_funny_posts(limit=20)
        state["posts"] = posts
        print(f"Found {len(posts)} potential posts")
        return state
    
    async def assess_content(self, state: AgentState) -> AgentState:
        """Assess content quality using Claude"""
        print("🤖 Assessing content quality...")
        assessed_posts = self.content_assessor.assess_humor_quality(state["posts"])
        state["posts"] = assessed_posts
        print(f"Filtered to {len(assessed_posts)} high-quality posts")
        return state
    
    async def select_best_post(self, state: AgentState) -> AgentState:
        """Select the best post for video creation"""
        print("🎯 Selecting best post...")
        if state["posts"]:
            best_post = state["posts"][0]  # Highest rated
            state["selected_post"] = best_post
            print(f"Selected: {best_post['title'][:50]}...")
        return state
    
    async def generate_audio(self, state: AgentState) -> AgentState:
        """Generate TTS audio"""
        print("🎵 Generating audio...")
        post = state["selected_post"]
        script = self.tts_generator.create_engaging_script(post)
        
        audio_path = f"audio_{post['created_utc']}.mp3"
        await self.tts_generator.generate_speech_openai(script, audio_path)
        
        state["audio_path"] = audio_path
        print("Audio generated successfully")
        return state
    
    async def create_video(self, state: AgentState) -> AgentState:
        """Create TikTok video"""
        print("🎬 Creating video...")
        video_path = self.video_creator.create_tiktok_video(
            state["selected_post"], 
            state["audio_path"]
        )
        state["video_path"] = video_path
        print("Video created successfully")
        return state
    
    async def upload_to_tiktok(self, state: AgentState) -> AgentState:
        """Upload to TikTok"""
        print("📱 Uploading to TikTok...")
        
        post = state["selected_post"]
        caption = f"Reddit story from r/{post['subreddit']}"
        hashtags = ["reddit", "story", "funny", "viral", "foryou"]
        
        try:
            self.tiktok_uploader.setup_driver()
            self.tiktok_uploader.upload_video(
                state["video_path"], 
                caption, 
                hashtags
            )
            state["upload_status"] = "success"
        except Exception as e:
            print(f"Upload failed: {e}")
            state["upload_status"] = "failed"
        finally:
            self.tiktok_uploader.close()
        
        return state
    
    async def run(self):
        """Run the complete agent workflow"""
        print("🚀 Starting Reddit to TikTok Agent...")
        
        initial_state = AgentState(
            posts=[],
            selected_post={},
            audio_path="",
            video_path="",
            upload_status=""
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        
        print("✅ Agent workflow completed!")
        return final_state

# Main execution
async def main():
    agent = RedditTikTokAgent()
    result = await agent.run()
    print(f"Final result: {result['upload_status']}")

if __name__ == "__main__":
    asyncio.run(main())
