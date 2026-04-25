import os
from typing import Optional, Dict, List

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import logger


load_dotenv()


class YouTubeAPI:
    """
    Production-ready YouTube API handler
    """

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")

        if not self.api_key:
            logger.error("YOUTUBE_API_KEY missing in .env")
            raise ValueError("YOUTUBE_API_KEY not found")

        try:
            self.youtube = build(
                "youtube",
                "v3",
                developerKey=self.api_key
            )
            logger.info("YouTube service initialized.")
        except Exception as e:
            logger.exception("Failed to initialize YouTube service.")
            raise e

    def search_channel(self, channel_name: str) -> Optional[Dict]:
        """
        Search channel by name
        """
        try:
            logger.info(f"Searching channel: {channel_name}")

            request = self.youtube.search().list(
                q=channel_name,
                part="snippet",
                type="channel",
                maxResults=1
            )

            response = request.execute()

            items = response.get("items", [])

            if not items:
                logger.warning(f"No channel found for {channel_name}")
                return None

            item = items[0]

            result = {
                "channel_id": item["snippet"]["channelId"],
                "channel_title": item["snippet"]["title"]
            }

            logger.info(f"Channel found: {result['channel_title']}")
            return result

        except HttpError:
            logger.exception("HTTP error while searching channel.")
            return None

        except Exception:
            logger.exception("Unexpected error in search_channel.")
            return None

    def get_channel_stats(self, channel_id: str) -> Optional[Dict]:
        """
        Get channel statistics
        """
        try:
            logger.info(f"Fetching stats for channel_id: {channel_id}")

            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )

            response = request.execute()

            items = response.get("items", [])

            if not items:
                logger.warning("No stats found.")
                return None

            item = items[0]

            result = {
                "channel_id": channel_id,
                "channel_title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
                "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                "views": int(item["statistics"].get("viewCount", 0)),
                "total_videos": int(item["statistics"].get("videoCount", 0)),
                "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"]
            }

            logger.info(f"Stats fetched for {result['channel_title']}")
            return result

        except HttpError:
            logger.exception("HTTP error in get_channel_stats.")
            return None

        except Exception:
            logger.exception("Unexpected error in get_channel_stats.")
            return None

    def get_playlist_videos(
        self,
        playlist_id: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Get videos from playlist
        """
        videos = []

        try:
            logger.info(f"Fetching playlist videos: {playlist_id}")

            request = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=max_results
            )

            response = request.execute()

            for item in response.get("items", []):

                snippet = item["snippet"]

                videos.append({
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "published_at": snippet["publishedAt"]
                })

            logger.info(f"Fetched {len(videos)} videos.")
            return videos

        except HttpError:
            logger.exception("HTTP error in get_playlist_videos.")
            return videos

        except Exception:
            logger.exception("Unexpected error in get_playlist_videos.")
            return videos

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Fetch detailed analytics for multiple videos in batch
        Uses YouTube Data API v3 videos.list endpoint
        Returns: video_id, title, published_at, views, likes, comments, duration
        """
        if not video_ids:
            logger.warning("No video IDs provided.")
            return []

        videos = []
        batch_size = 50

        try:
            logger.info(f"Fetching details for {len(video_ids)} videos.")

            # Process in batches (API limit is 50 per request)
            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i:i + batch_size]
                video_ids_str = ",".join(batch)

                request = self.youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=video_ids_str
                )

                response = request.execute()

                for item in response.get("items", []):
                    snippet = item["snippet"]
                    statistics = item["statistics"]
                    content_details = item["contentDetails"]

                    # Parse ISO 8601 duration (PT#H#M#S format)
                    duration = content_details.get("duration", "PT0S0M0S")
                    # Keep as ISO format for storage

                    videos.append({
                        "video_id": item["id"],
                        "title": snippet["title"],
                        "published_at": snippet["publishedAt"],
                        "views": int(statistics.get("viewCount", 0)),
                        "likes": int(statistics.get("likeCount", 0)),
                        "comments": int(statistics.get("commentCount", 0)),
                        "duration": duration,
                        "fetched_at": "CURRENT_TIMESTAMP"
                    })

                logger.info(f"Batch {i//batch_size + 1}: {len(batch)} videos processed.")

            logger.info(f"Video details fetched: {len(videos)} videos.")
            return videos

        except HttpError as e:
            logger.exception(f"HTTP error in get_video_details: {e}")
            return videos

        except Exception:
            logger.exception("Unexpected error in get_video_details.")
            return videos

    def get_top_channels(self, max_results: int = 50) -> List[Dict]:
        """
        Fetch top channels using YouTube search with popular queries
        Returns channel_id, channel_title, subscriber count, etc.
        """
        channels = []
        
        # Popular channel keywords to search for
        search_queries = [
            "MrBeast", "PewDiePie", "Cocomelon", "SET India", 
            "Kids TV", "Zee Music", "WWE", "6ix9ine",
            "Taylor Swift", "Ed Sheeran", "Billie Eilish",
            "NASA", "Marvel", "DC", "Star Wars",
            "NBA", "FIFA", "LaLiga", "Premier League",
            "TechGuyz", "MKBHD", "Linus Tech Tips"
        ]
        
        try:
            logger.info(f"Fetching top {max_results} channels...")
            
            # Search for channels using different queries
            for query in search_queries:
                if len(channels) >= max_results:
                    break
                    
                try:
                    request = self.youtube.search().list(
                        q=query,
                        part="snippet",
                        type="channel",
                        maxResults=5
                    )
                    
                    response = request.execute()
                    items = response.get("items", [])
                    
                    for item in items:
                        channel_id = item["snippet"]["channelId"]
                        channel_title = item["snippet"]["title"]
                        
                        # Skip if already added
                        if any(c.get("channel_id") == channel_id for c in channels):
                            continue
                        
                        # Get channel stats
                        stats = self._get_channel_stats_simple(channel_id)
                        
                        if stats:
                            channels.append(stats)
                            logger.info(f"Added channel: {channel_title}")
                            
                except Exception as e:
                    logger.warning(f"Error fetching channel for query '{query}': {e}")
                    continue
            
            logger.info(f"Top {len(channels)} channels fetched successfully.")
            return channels[:max_results]
            
        except Exception as e:
            logger.exception(f"Error in get_top_channels: {e}")
            return channels

    def _get_channel_stats_simple(self, channel_id: str) -> Optional[Dict]:
        """
        Helper to get simple channel stats
        """
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            
            response = request.execute()
            items = response.get("items", [])
            
            if not items:
                return None
                
            item = items[0]
            
            return {
                "channel_id": channel_id,
                "channel_title": item["snippet"]["title"],
                "published_at": item["snippet"].get("publishedAt", ""),
                "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                "views": int(item["statistics"].get("viewCount", 0)),
                "total_videos": int(item["statistics"].get("videoCount", 0)),
                "uploads_playlist": ""  # Will be fetched separately if needed
            }
            
        except Exception as e:
            logger.warning(f"Error getting stats for channel {channel_id}: {e}")
            return None