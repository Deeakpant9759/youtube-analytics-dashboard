import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import logger


class DatabaseManager:
    """
    Production-ready SQLite database manager
    """

    def __init__(self, db_path: str = "data/youtube.db"):
        self.db_path = db_path
        self._ensure_folder()
        self.create_tables()

    def _ensure_folder(self):
        """
        Create data folder if missing
        """
        Path("data").mkdir(parents=True, exist_ok=True)

    def connect(self):
        """
        Create DB connection
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            logger.info("Database connection established.")
            return conn

        except Exception:
            logger.exception("Failed to connect database.")
            raise

    def create_tables(self):
        """
        Create required tables with safe migration for existing databases
        """
        try:
            conn = self.connect()
            cur = conn.cursor()

            # Create channels table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                channel_title TEXT,
                published_at TEXT,
                subscribers INTEGER,
                views INTEGER,
                total_videos INTEGER,
                uploads_playlist TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create videos table with new schema
            cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                channel_id TEXT,
                title TEXT,
                published_at TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                duration TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(channel_id) REFERENCES channels(channel_id)
            )
            """)

            # Safe migration: Add missing columns to existing database
            self._migrate_videos_table(cur)

            conn.commit()
            conn.close()

            logger.info("Tables created/updated successfully.")

        except Exception:
            logger.exception("Failed creating tables.")
            raise

    def _migrate_videos_table(self, cur):
        """
        Safely migrate videos table: add missing columns without breaking old DB
        """
        try:
            # Get current schema
            cur.execute("PRAGMA table_info(videos)")
            columns = {row[1] for row in cur.fetchall()}

            migrations = []

            if "views" not in columns:
                migrations.append("ADD COLUMN views INTEGER DEFAULT 0")
            if "likes" not in columns:
                migrations.append("ADD COLUMN likes INTEGER DEFAULT 0")
            if "comments" not in columns:
                migrations.append("ADD COLUMN comments INTEGER DEFAULT 0")
            if "duration" not in columns:
                migrations.append("ADD COLUMN duration TEXT")
            if "fetched_at" not in columns:
                migrations.append("ADD COLUMN fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            for migration in migrations:
                try:
                    cur.execute(f"ALTER TABLE videos {migration}")
                    logger.info(f"Migration applied: {migration}")
                except Exception as e:
                    logger.warning(f"Migration skipped or already applied: {e}")

            logger.info("Videos table migration completed.")

        except Exception:
            logger.exception("Migration failed.")
            # Continue - table may already have columns

    def upsert_channel(self, data: Dict):
        """
        Insert or update channel data
        """
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO channels (
                channel_id, channel_title, published_at,
                subscribers, views, total_videos, uploads_playlist
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(channel_id) DO UPDATE SET
                channel_title=excluded.channel_title,
                published_at=excluded.published_at,
                subscribers=excluded.subscribers,
                views=excluded.views,
                total_videos=excluded.total_videos,
                uploads_playlist=excluded.uploads_playlist
            """, (
                data["channel_id"],
                data["channel_title"],
                data["published_at"],
                data["subscribers"],
                data["views"],
                data["total_videos"],
                data["uploads_playlist"]
            ))

            conn.commit()
            conn.close()

            logger.info(f"Channel saved: {data['channel_title']}")

        except Exception:
            logger.exception("Failed saving channel.")

    def insert_videos(self, channel_id: str, videos: List[Dict]):
        """
        Insert multiple videos with full analytics data
        Uses INSERT OR REPLACE for upsert behavior
        """
        try:
            conn = self.connect()
            cur = conn.cursor()

            rows = []

            for video in videos:
                rows.append((
                    video.get("video_id"),
                    channel_id,
                    video.get("title"),
                    video.get("published_at"),
                    video.get("views", 0),
                    video.get("likes", 0),
                    video.get("comments", 0),
                    video.get("duration"),
                    video.get("fetched_at")  # Can be None, uses DEFAULT
                ))

            cur.executemany("""
            INSERT OR REPLACE INTO videos (
                video_id, channel_id, title, published_at,
                views, likes, comments, duration, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """, rows)

            conn.commit()
            conn.close()

            logger.info(f"{len(videos)} videos inserted/updated with analytics.")

        except Exception:
            logger.exception("Failed inserting videos.")

    def fetch_channels(self) -> List[Dict]:
        """
        Return all channels
        """
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("SELECT * FROM channels ORDER BY subscribers DESC")

            rows = cur.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception:
            logger.exception("Failed fetching channels.")
            return []

    def fetch_videos(self, channel_id: Optional[str] = None) -> List[Dict]:
        """
        Return videos (all or by channel)
        """
        try:
            conn = self.connect()
            cur = conn.cursor()

            if channel_id:
                cur.execute("""
                    SELECT * FROM videos
                    WHERE channel_id = ?
                    ORDER BY published_at DESC
                """, (channel_id,))
            else:
                cur.execute("""
                    SELECT * FROM videos
                    ORDER BY published_at DESC
                """)

            rows = cur.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception:
            logger.exception("Failed fetching videos.")
            return []