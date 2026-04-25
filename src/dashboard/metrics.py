"""
Metrics module for KPI cards and calculations
"""
import streamlit as st
from typing import Dict, List, Optional
import pandas as pd


def format_number(num: int) -> str:
    """
    Format large numbers with K, M, B suffixes
    """
    if num is None or num == 0:
        return "0"
    
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def calculate_engagement_rate(views: int, likes: int, comments: int) -> float:
    """
    Calculate engagement rate: (likes + comments) / views * 100
    """
    if views == 0:
        return 0.0
    return round((likes + comments) / views * 100, 2)


def render_kpi_card(title: str, value: str, delta: Optional[str] = None, icon: Optional[str] = None):
    """
    Render a single KPI card with optional delta
    """
    icon_html = f"{icon} " if icon else ""
    
    if delta:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #3d3d5c;
            margin-bottom: 10px;
        ">
            <p style="color: #a0a0b0; font-size: 14px; margin: 0;">{icon_html}{title}</p>
            <h2 style="color: #ffffff; font-size: 28px; margin: 8px 0 0 0; font-weight: 600;">{value}</h2>
            <p style="color: #4ade80; font-size: 14px; margin: 4px 0 0 0;">{delta}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #3d3d5c;
            margin-bottom: 10px;
        ">
            <p style="color: #a0a0b0; font-size: 14px; margin: 0;">{icon_html}{title}</p>
            <h2 style="color: #ffffff; font-size: 28px; margin: 8px 0 0 0; font-weight: 600;">{value}</h2>
        </div>
        """, unsafe_allow_html=True)


def render_kpi_row(metrics: Dict[str, tuple], columns: int = 4):
    """
    Render a row of KPI cards
    metrics: dict of {title: (value, delta, icon)}
    """
    cols = st.columns(columns)
    
    for idx, (title, (value, delta, icon)) in enumerate(metrics.items()):
        with cols[idx]:
            render_kpi_card(title, value, delta, icon)


def calculate_channel_metrics(channels: List[Dict]) -> Dict:
    """
    Calculate aggregate metrics from channels
    """
    if not channels:
        return {
            "total_channels": 0,
            "total_subscribers": 0,
            "total_views": 0,
            "total_videos": 0
        }
    
    return {
        "total_channels": len(channels),
        "total_subscribers": sum(c.get("subscribers", 0) for c in channels),
        "total_views": sum(c.get("views", 0) for c in channels),
        "total_videos": sum(c.get("total_videos", 0) for c in channels)
    }


def calculate_video_metrics(videos: List[Dict]) -> Dict:
    """
    Calculate aggregate metrics from videos
    """
    if not videos:
        return {
            "total_videos": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "avg_views": 0,
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_engagement": 0
        }
    
    total_views = sum(v.get("views", 0) for v in videos)
    total_likes = sum(v.get("likes", 0) for v in videos)
    total_comments = sum(v.get("comments", 0) for v in videos)
    count = len(videos)
    
    avg_engagement = 0
    if total_views > 0:
        avg_engagement = round((total_likes + total_comments) / total_views * 100, 2)
    
    return {
        "total_videos": count,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "avg_views": total_views // count if count > 0 else 0,
        "avg_likes": total_likes // count if count > 0 else 0,
        "avg_comments": total_comments // count if count > 0 else 0,
        "avg_engagement": avg_engagement
    }


def get_top_videos(videos: List[Dict], metric: str = "views", n: int = 10) -> List[Dict]:
    """
    Get top N videos by specified metric
    """
    if not videos:
        return []
    
    sorted_videos = sorted(
        videos,
        key=lambda x: x.get(metric, 0),
        reverse=True
    )
    
    return sorted_videos[:n]


def parse_iso_duration(duration_str: str) -> str:
    """
    Parse ISO 8601 duration (PT#H#M#S) to human readable format
    """
    if not duration_str:
        return "N/A"
    
    try:
        # Remove 'PT' prefix
        duration_str = duration_str.replace("PT", "")
        
        hours = 0
        minutes = 0
        seconds = 0
        
        if "H" in duration_str:
            parts = duration_str.split("H")
            hours = int(parts[0])
            duration_str = parts[1] if len(parts) > 1 else ""
        
        if "M" in duration_str:
            parts = duration_str.split("M")
            minutes = int(parts[0])
            duration_str = parts[1] if len(parts) > 1 else ""
        
        if "S" in duration_str:
            seconds = int(duration_str.replace("S", ""))
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    except Exception:
        return duration_str


def prepare_video_dataframe(videos: List[Dict]) -> pd.DataFrame:
    """
    Convert videos list to DataFrame with computed columns
    """
    if not videos:
        return pd.DataFrame()
    
    df = pd.DataFrame(videos)
    
    # Add computed columns
    if not df.empty:
        df["engagement_rate"] = df.apply(
            lambda x: calculate_engagement_rate(
                x.get("views", 0),
                x.get("likes", 0),
                x.get("comments", 0)
            ),
            axis=1
        )
        
        # Parse duration
        df["duration_parsed"] = df["duration"].apply(parse_iso_duration)
        
        # Parse published_at to datetime
        df["published_datetime"] = pd.to_datetime(
            df["published_at"],
            errors="coerce"
        )
        df["publish_year"] = df["published_datetime"].dt.year
        df["publish_month"] = df["published_datetime"].dt.month
        df["publish_month_name"] = df["published_datetime"].dt.month_name()
        df["publish_weekday"] = df["published_datetime"].dt.day_name()
    
    return df