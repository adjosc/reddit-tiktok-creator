"""
Automated Scheduler for Reddit to TikTok Video Creator

Runs the video creation agent on a scheduled basis with configurable timing and settings.
"""

import schedule
import time
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main_agent import RedditTikTokAgent
from config.settings import get_config, load_preset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output_videos/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class VideoCreationScheduler:
    """Handles scheduled video creation with intelligent timing and error recovery."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize the scheduler.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config = get_config()
        self.agent = None
        self.stats_file = Path("output_videos/scheduler_stats.json")
        self.last_run_file = Path("output_videos/last_run.json")
        
        # Scheduling configuration
        self.schedule_config = {
            'interval_hours': int(os.getenv('SCHEDULE_INTERVAL_HOURS', '4')),
            'max_videos_per_day': int(os.getenv('SCHEDULE_MAX_VIDEOS_PER_DAY', '6')),
            'retry_failed_after_hours': int(os.getenv('SCHEDULE_RETRY_HOURS', '2')),
            'skip_low_quality': os.getenv('SCHEDULE_SKIP_LOW_QUALITY', 'true').lower() == 'true',
            'min_gap_minutes': int(os.getenv('SCHEDULE_MIN_GAP_MINUTES', '30')),
            'peak_hours': self._parse_peak_hours(os.getenv('SCHEDULE_PEAK_HOURS', '12-14,19-21')),
            'quiet_hours': self._parse_quiet_hours(os.getenv('SCHEDULE_QUIET_HOURS', '23-6')),
            'weekend_schedule': os.getenv('SCHEDULE_WEEKEND_ENABLED', 'true').lower() == 'true'
        }
        
        # Create stats file if it doesn't exist
        if not self.stats_file.exists():
            self._init_stats_file()
        
        logger.info("📅 Video Creation Scheduler initialized")
        self._print_schedule_config()
    
    def _parse_peak_hours(self, peak_hours_str: str) -> list:
        """Parse peak hours string into list of hour ranges."""
        ranges = []
        for time_range in peak_hours_str.split(','):
            start, end = map(int, time_range.split('-'))
            ranges.append((start, end))
        return ranges
    
    def _parse_quiet_hours(self, quiet_hours_str: str) -> tuple:
        """Parse quiet hours string into tuple."""
        start, end = map(int, quiet_hours_str.split('-'))
        return (start, end)
    
    def _init_stats_file(self):
        """Initialize the stats tracking file."""
        stats = {
            'total_scheduled_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'videos_created': 0,
            'average_humor_rating': 0,
            'last_successful_run': None,
            'last_failed_run': None,
            'daily_video_count': {},
            'created_at': datetime.now().isoformat()
        }
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def _load_stats(self) -> dict:
        """Load scheduler statistics."""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load stats: {e}")
            self._init_stats_file()
            return self._load_stats()
    
    def _save_stats(self, stats: dict):
        """Save scheduler statistics."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save stats: {e}")
    
    def _update_stats(self, success: bool, video_count: int = 0, humor_rating: float = 0):
        """Update scheduler statistics."""
        stats = self._load_stats()
        
        stats['total_scheduled_runs'] += 1
        
        if success:
            stats['successful_runs'] += 1
            stats['videos_created'] += video_count
            stats['last_successful_run'] = datetime.now().isoformat()
            
            if humor_rating > 0:
                current_avg = stats['average_humor_rating']
                total_videos = stats['videos_created']
                if total_videos > 1:
                    stats['average_humor_rating'] = (current_avg * (total_videos - 1) + humor_rating) / total_videos
                else:
                    stats['average_humor_rating'] = humor_rating
        else:
            stats['failed_runs'] += 1
            stats['last_failed_run'] = datetime.now().isoformat()
        
        # Update daily count
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in stats['daily_video_count']:
            stats['daily_video_count'][today] = 0
        stats['daily_video_count'][today] += video_count
        
        self._save_stats(stats)
    
    def _can_create_video_now(self) -> tuple[bool, str]:
        """
        Check if a video can be created right now based on various constraints.
        
        Returns:
            Tuple of (can_create, reason)
        """
        now = datetime.now()
        current_hour = now.hour
        today = now.strftime('%Y-%m-%d')
        
        # Check quiet hours
        quiet_start, quiet_end = self.schedule_config['quiet_hours']
        if quiet_start > quiet_end:  # Spans midnight
            if current_hour >= quiet_start or current_hour < quiet_end:
                return False, f"Quiet hours ({quiet_start}:00-{quiet_end}:00)"
        else:
            if quiet_start <= current_hour < quiet_end:
                return False, f"Quiet hours ({quiet_start}:00-{quiet_end}:00)"
        
        # Check weekend schedule
        if not self.schedule_config['weekend_schedule'] and now.weekday() >= 5:
            return False, "Weekend creation disabled"
        
        # Check daily video limit
        stats = self._load_stats()
        daily_count = stats['daily_video_count'].get(today, 0)
        if daily_count >= self.schedule_config['max_videos_per_day']:
            return False, f"Daily limit reached ({daily_count}/{self.schedule_config['max_videos_per_day']})"
        
        # Check minimum gap since last run
        if self.last_run_file.exists():
            try:
                with open(self.last_run_file, 'r') as f:
                    last_run_data = json.load(f)
                last_run_time = datetime.fromisoformat(last_run_data['timestamp'])
                
                gap_minutes = (now - last_run_time).total_seconds() / 60
                if gap_minutes < self.schedule_config['min_gap_minutes']:
                    return False, f"Too soon since last run ({gap_minutes:.1f} < {self.schedule_config['min_gap_minutes']} min)"
            except Exception as e:
                logger.warning(f"Could not check last run time: {e}")
        
        return True, "All checks passed"
    
    def _is_peak_time(self) -> bool:
        """Check if current time is during peak hours for video creation."""
        current_hour = datetime.now().hour
        
        for start, end in self.schedule_config['peak_hours']:
            if start <= current_hour < end:
                return True
        
        return False
    
    def _get_optimal_config(self) -> dict:
        """Get optimal configuration based on current time and conditions."""
        base_config = self.config.get_agent_config()
        
        # Adjust based on peak time
        if self._is_peak_time():
            # Use higher quality settings during peak hours
            base_config.update({
                'min_humor_rating': max(7.5, base_config.get('min_humor_rating', 7.0)),
                'post_limit': min(15, base_config.get('post_limit', 20)),
                'video_style': 'dynamic'
            })
            logger.info("🔥 Using peak-time high-quality settings")
        else:
            # Use standard settings during off-peak
            base_config.update({
                'min_humor_rating': base_config.get('min_humor_rating', 7.0),
                'video_style': 'modern'
            })
            logger.info("⚡ Using standard quality settings")
        
        return base_config
    
    def _record_run(self, result: dict):
        """Record information about the current run."""
        run_data = {
            'timestamp': datetime.now().isoformat(),
            'status': result.get('creation_status', 'unknown'),
            'error': result.get('error_message', ''),
            'video_path': result.get('video_path', ''),
            'humor_rating': 0,
            'processing_time': 0
        }
        
        # Extract additional details if successful
        if result.get('creation_status') == 'success' and 'metadata' in result:
            metadata = result['metadata']
            run_data.update({
                'humor_rating': metadata.get('reddit_data', {}).get('humor_rating', 0),
                'processing_time': result.get('creation_stats', {}).get('total_time', 0),
                'subreddit': metadata.get('reddit_data', {}).get('subreddit', ''),
                'reddit_score': metadata.get('reddit_data', {}).get('score', 0)
            })
        
        # Save run data
        with open(self.last_run_file, 'w') as f:
            json.dump(run_data, f, indent=2)
    
    async def create_scheduled_video(self):
        """Create a video as part of the scheduled workflow."""
        
        logger.info("⏰ Scheduled video creation starting...")
        
        # Check if we can create a video now
        can_create, reason = self._can_create_video_now()
        if not can_create:
            logger.info(f"⏸️  Skipping scheduled run: {reason}")
            return
        
        try:
            # Initialize agent if needed
            if self.agent is None:
                self.agent = RedditTikTokAgent()
            
            # Get optimal configuration
            config = self._get_optimal_config()
            
            # Create video
            logger.info("🎬 Starting scheduled video creation...")
            result = await self.agent.run(**config)
            
            # Record the run
            self._record_run(result)
            
            # Update statistics
            if result['creation_status'] == 'success':
                humor_rating = 0
                if 'metadata' in result:
                    humor_rating = result['metadata'].get('reddit_data', {}).get('humor_rating', 0)
                
                self._update_stats(True, 1, humor_rating)
                logger.info("✅ Scheduled video creation completed successfully!")
                
                # Print summary
                self._print_run_summary(result, True)
                
            else:
                self._update_stats(False, 0, 0)
                logger.error(f"❌ Scheduled video creation failed: {result.get('error_message', 'Unknown error')}")
                self._print_run_summary(result, False)
        
        except Exception as e:
            logger.error(f"💥 Scheduled video creation crashed: {e}")
            self._update_stats(False, 0, 0)
            
            # Record crash
            crash_result = {
                'creation_status': 'crashed',
                'error_message': str(e)
            }
            self._record_run(crash_result)
    
    def _print_run_summary(self, result: dict, success: bool):
        """Print a summary of the run."""
        
        print(f"\n{'='*50}")
        print(f"📊 SCHEDULED RUN SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        if success:
            metadata = result.get('metadata', {})
            reddit_data = metadata.get('reddit_data', {})
            video_info = metadata.get('video_info', {})
            stats = result.get('creation_stats', {})
            
            print(f"✅ Status: SUCCESS")
            print(f"📹 Video: {Path(video_info.get('video_path', '')).name}")
            print(f"📊 Rating: {reddit_data.get('humor_rating', 0)}/10")
            print(f"⏱️  Duration: {video_info.get('duration_seconds', 0):.1f}s")
            print(f"🕒 Processing: {stats.get('total_time', 0):.1f}s")
            print(f"🎯 Subreddit: r/{reddit_data.get('subreddit', 'unknown')}")
            print(f"🔥 Reddit Score: {reddit_data.get('score', 0):,}")
        else:
            print(f"❌ Status: FAILED")
            print(f"💬 Error: {result.get('error_message', 'Unknown error')}")
        
        # Show daily statistics
        stats = self._load_stats()
        today = datetime.now().strftime('%Y-%m-%d')
        daily_count = stats['daily_video_count'].get(today, 0)
        
        print(f"\n📈 Today's Progress: {daily_count}/{self.schedule_config['max_videos_per_day']} videos")
        print(f"🎯 Total Created: {stats['videos_created']} videos")
        print(f"📊 Success Rate: {stats['successful_runs']}/{stats['total_scheduled_runs']} ({stats['successful_runs']/max(1,stats['total_scheduled_runs'])*100:.1f}%)")
        
        print(f"{'='*50}\n")
    
    def _print_schedule_config(self):
        """Print the current schedule configuration."""
        
        print(f"\n📅 SCHEDULER CONFIGURATION")
        print(f"⏰ Interval: Every {self.schedule_config['interval_hours']} hours")
        print(f"📊 Daily Limit: {self.schedule_config['max_videos_per_day']} videos")
        print(f"⏸️  Min Gap: {self.schedule_config['min_gap_minutes']} minutes")
        print(f"🔥 Peak Hours: {', '.join([f'{s}-{e}' for s, e in self.schedule_config['peak_hours']])}")
        print(f"😴 Quiet Hours: {self.schedule_config['quiet_hours'][0]}-{self.schedule_config['quiet_hours'][1]}")
        print(f"📅 Weekends: {'Enabled' if self.schedule_config['weekend_schedule'] else 'Disabled'}")
        print()
    
    def setup_schedule(self):
        """Set up the scheduled jobs."""
        
        # Main scheduled job
        schedule.every(self.schedule_config['interval_hours']).hours.do(
            lambda: asyncio.run(self.create_scheduled_video())
        )
        
        # Daily cleanup job (runs at 3 AM)
        schedule.every().day.at("03:00").do(self.daily_cleanup)
        
        # Weekly stats report (runs Sunday at 9 AM)
        schedule.every().sunday.at("09:00").do(self.weekly_report)
        
        logger.info(f"✅ Schedule configured: Creating videos every {self.schedule_config['interval_hours']} hours")
    
    def daily_cleanup(self):
        """Perform daily cleanup tasks."""
        logger.info("🧹 Performing daily cleanup...")
        
        try:
            # Clean up old temporary files
            temp_dir = Path("output_videos") / "temp"
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    if file.is_file() and file.stat().st_mtime < time.time() - 86400:  # 24 hours
                        file.unlink()
                        logger.info(f"🗑️  Cleaned up temp file: {file.name}")
            
            # Archive old logs
            logs_dir = Path("output_videos") / "logs"
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                        archive_name = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d')}.log")
                        log_file.rename(archive_name)
                        log_file.touch()  # Create new empty log
                        logger.info(f"📦 Archived large log: {archive_name.name}")
            
            logger.info("✅ Daily cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Daily cleanup failed: {e}")
    
    def weekly_report(self):
        """Generate weekly performance report."""
        logger.info("📊 Generating weekly report...")
        
        try:
            stats = self._load_stats()
            
            # Calculate weekly stats
            one_week_ago = datetime.now() - timedelta(days=7)
            week_videos = 0
            
            for date_str, count in stats['daily_video_count'].items():
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if date >= one_week_ago:
                    week_videos += count
            
            report = f"""
📊 WEEKLY PERFORMANCE REPORT - {datetime.now().strftime('%Y-%m-%d')}
{'='*60}

📈 This Week's Performance:
   Videos Created: {week_videos}
   Success Rate: {stats['successful_runs']}/{stats['total_scheduled_runs']} ({stats['successful_runs']/max(1,stats['total_scheduled_runs'])*100:.1f}%)
   Average Rating: {stats['average_humor_rating']:.1f}/10

🎯 All-Time Stats:
   Total Videos: {stats['videos_created']}
   Total Runs: {stats['total_scheduled_runs']}
   Last Success: {stats.get('last_successful_run', 'Never')}

{'='*60}
"""
            
            print(report)
            logger.info("✅ Weekly report generated")
            
        except Exception as e:
            logger.error(f"❌ Weekly report failed: {e}")
    
    def run_continuous(self):
        """Run the scheduler continuously."""
        
        logger.info("🚀 Starting continuous scheduler...")
        print(f"⏰ Scheduler running - Next video creation in {self.schedule_config['interval_hours']} hours")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
            print("\n👋 Scheduler stopped gracefully")
        except Exception as e:
            logger.error(f"💥 Scheduler crashed: {e}")
            raise
    
    def run_once(self):
        """Run video creation once immediately."""
        logger.info("⚡ Running video creation once...")
        asyncio.run(self.create_scheduled_video())
    
    def status(self):
        """Show current scheduler status."""
        stats = self._load_stats()
        
        print(f"\n📊 SCHEDULER STATUS")
        print(f"{'='*40}")
        print(f"🎬 Total Videos Created: {stats['videos_created']}")
        print(f"✅ Successful Runs: {stats['successful_runs']}")
        print(f"❌ Failed Runs: {stats['failed_runs']}")
        print(f"📊 Average Quality: {stats['average_humor_rating']:.1f}/10")
        
        if stats.get('last_successful_run'):
            last_success = datetime.fromisoformat(stats['last_successful_run'])
            print(f"🕒 Last Success: {last_success.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show today's progress
        today = datetime.now().strftime('%Y-%m-%d')
        daily_count = stats['daily_video_count'].get(today, 0)
        print(f"📅 Today: {daily_count}/{self.schedule_config['max_videos_per_day']} videos")
        
        # Check if we can run now
        can_create, reason = self._can_create_video_now()
        print(f"🎯 Can Create Now: {'Yes' if can_create else f'No ({reason})'}")
        print(f"{'='*40}\n")


def main():
    """Main function for scheduler CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reddit to TikTok Video Creation Scheduler")
    parser.add_argument('command', choices=['start', 'once', 'status', 'config'], 
                       help='Command to execute')
    parser.add_argument('--preset', choices=['high_quality', 'high_volume', 'family_friendly'],
                       help='Use a preset configuration')
    parser.add_argument('--config', help='Path to custom config file')
    
    args = parser.parse_args()
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize scheduler
        scheduler = VideoCreationScheduler(args.config)
        
        if args.command == 'start':
            scheduler.setup_schedule()
            scheduler.run_continuous()
            
        elif args.command == 'once':
            scheduler.run_once()
            
        elif args.command == 'status':
            scheduler.status()
            
        elif args.command == 'config':
            scheduler._print_schedule_config()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"💥 Scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
