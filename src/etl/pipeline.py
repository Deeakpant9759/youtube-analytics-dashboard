import time
from typing import Optional

from src.utils.logger import logger
from src.api.youtube_api import YouTubeAPI
from src.database.db import DatabaseManager


class YouTubeETLPipeline:
    """
    Production-ready ETL pipeline
    Extract -> Transform -> Load
    """

    def __init__(self):
        self.api = YouTubeAPI()
        self.db = DatabaseManager()

    def run(self, channel_name: str, max_videos: int = 50) -> bool:
        """
        Run complete pipeline for one channel with full video analytics
        New flow:
        1. Search channel
        2. Fetch channel stats
        3. Get upload playlist
        4. Fetch playlist videos (basic info)
        5. Collect video_ids
        6. Batch fetch detailed stats (views, likes, comments, duration)
        7. Merge and insert into database
        """
        start_time = time.time()

        try:
            logger.info("=" * 60)
            logger.info(f"ETL Started for channel: {channel_name}")

            # STEP 1: Search Channel
            logger.info("STEP 1: Searching channel...")
            channel = self.api.search_channel(channel_name)

            if not channel:
                logger.warning("Channel not found.")
                return False

            channel_id = channel["channel_id"]
            logger.info(f"Channel found: {channel['channel_title']}")

            # STEP 2: Fetch Channel Stats
            logger.info("STEP 2: Fetching channel statistics...")
            stats = self.api.get_channel_stats(channel_id)

            if not stats:
                logger.warning("Channel stats unavailable.")
                return False

            # STEP 3: Save Channel to DB
            logger.info("STEP 3: Saving channel to database...")
            self.db.upsert_channel(stats)
            logger.info(f"Channel saved: {stats['channel_title']}")

            # STEP 4: Get Upload Playlist
            playlist_id = stats["uploads_playlist"]
            logger.info(f"Uploads playlist ID: {playlist_id}")

            # STEP 5: Fetch Playlist Videos (basic info)
            logger.info(f"STEP 5: Fetching playlist videos (max: {max_videos})...")
            basic_videos = self.api.get_playlist_videos(
                playlist_id=playlist_id,
                max_results=max_videos
            )

            if not basic_videos:
                logger.warning("No videos found in playlist.")
                return False

            logger.info(f"Fetched {len(basic_videos)} basic video records.")

            # STEP 6: Collect video_ids for batch fetch
            video_ids = [v["video_id"] for v in basic_videos]
            logger.info(f"Collected {len(video_ids)} video IDs for detailed fetch.")

            # STEP 7: Batch fetch detailed video analytics
            logger.info("STEP 7: Fetching detailed video analytics...")
            detailed_videos = self.api.get_video_details(video_ids)

            if not detailed_videos:
                logger.warning("Failed to fetch video details, using basic data.")
                detailed_videos = basic_videos

            logger.info(f"Fetched detailed analytics for {len(detailed_videos)} videos.")

            # STEP 8: Merge title/date from basic with analytics from detailed
            logger.info("STEP 8: Merging video data...")
            merged_videos = self._merge_video_data(basic_videos, detailed_videos)
            logger.info(f"Merged {len(merged_videos)} video records.")

            # STEP 9: Insert into database
            logger.info("STEP 9: Inserting videos into database...")
            self.db.insert_videos(
                channel_id=channel_id,
                videos=merged_videos
            )

            # Runtime summary
            runtime = round(time.time() - start_time, 2)

            logger.info(
                f"ETL Completed | "
                f"Channel: {stats['channel_title']} | "
                f"Videos: {len(merged_videos)} | "
                f"Time: {runtime}s"
            )
            logger.info("=" * 60)

            return True

        except Exception:
            logger.exception("ETL Pipeline failed.")
            return False

    def _merge_video_data(self, basic_videos: list, detailed_videos: list) -> list:
        """
        Merge basic video data (title, published_at) with detailed analytics
        Creates a unified list with all fields
        """
        try:
            # Build lookup from detailed videos
            detailed_lookup = {v["video_id"]: v for v in detailed_videos}

            merged = []

            for basic in basic_videos:
                video_id = basic["video_id"]

                # Start with basic data
                merged_video = {
                    "video_id": video_id,
                    "title": basic.get("title"),
                    "published_at": basic.get("published_at"),
                    "views": 0,
                    "likes": 0,
                    "comments": 0,
                    "duration": None,
                    "fetched_at": "CURRENT_TIMESTAMP"
                }

                # Overlay detailed data if available
                if video_id in detailed_lookup:
                    detail = detailed_lookup[video_id]
                    merged_video.update({
                        "views": detail.get("views", 0),
                        "likes": detail.get("likes", 0),
                        "comments": detail.get("comments", 0),
                        "duration": detail.get("duration"),
                        "fetched_at": detail.get("fetched_at")
                    })

                merged.append(merged_video)

            logger.info(f"Video data merged: {len(merged)} records.")
            return merged

        except Exception:
            logger.exception("Failed merging video data.")
            return basic_videos  # Fallback to basic data

    def run_top_channels(self, max_channels: int = 50) -> bool:
        """
        Fetch top channels from YouTube API and save to database
        """
        start_time = time.time()

        try:
            logger.info("=" * 60)
            logger.info(f"Fetching top {max_channels} channels...")

            # Fetch top channels
            channels = self.api.get_top_channels(max_results=max_channels)

            if not channels:
                logger.warning("No channels fetched.")
                return False

            # Save each channel to database
            saved_count = 0
            for channel in channels:
                try:
                    # Get full stats with uploads playlist
                    full_stats = self.api.get_channel_stats(channel["channel_id"])
                    
                    if full_stats:
                        self.db.upsert_channel(full_stats)
                        saved_count += 1
                        logger.info(f"Saved channel: {full_stats['channel_title']}")
                except Exception as e:
                    logger.warning(f"Error saving channel {channel.get('channel_title')}: {e}")
                    continue

            runtime = round(time.time() - start_time, 2)

            logger.info(
                f"Top Channels ETL Completed | "
                f"Channels: {saved_count}/{len(channels)} | "
                f"Time: {runtime}s"
            )
            logger.info("=" * 60)

            return saved_count > 0

        except Exception:
            logger.exception("Top Channels ETL failed.")
            return False


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "top-channels":
        # Fetch top channels
        pipeline = YouTubeETLPipeline()
        success = pipeline.run_top_channels(max_channels=50)
        print(f"Success: {success}")
    else:
        # Run single channel pipeline
        pipeline = YouTubeETLPipeline()
        pipeline.run("MrBeast", max_videos=25)