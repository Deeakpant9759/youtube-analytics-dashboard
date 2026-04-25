"""
Sidebar module for Streamlit dashboard
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple
from src.database.db import DatabaseManager
from src.etl.pipeline import YouTubeETLPipeline
from src.utils.logger import logger


def init_session_state():
    """
    Initialize session state variables
    """
    if "channels" not in st.session_state:
        st.session_state.channels = []
    
    if "videos" not in st.session_state:
        st.session_state.videos = []
    
    if "selected_channel" not in st.session_state:
        st.session_state.selected_channel = None
    
    if "db_manager" not in st.session_state:
        try:
            st.session_state.db_manager = DatabaseManager()
        except Exception as e:
            logger.error(f"Failed to initialize DB: {e}")
            st.session_state.db_manager = None


@st.cache_data(ttl=300)
def load_channels_from_db() -> List[Dict]:
    """
    Load channels from database with caching
    """
    try:
        db = DatabaseManager()
        channels = db.fetch_channels()
        logger.info(f"Loaded {len(channels)} channels from DB")
        return channels
    except Exception as e:
        logger.exception("Failed to load channels")
        return []


@st.cache_data(ttl=300)
def load_videos_from_db(channel_id: Optional[str] = None) -> List[Dict]:
    """
    Load videos from database with caching
    """
    try:
        db = DatabaseManager()
        videos = db.fetch_videos(channel_id)
        logger.info(f"Loaded {len(videos)} videos from DB")
        return videos
    except Exception as e:
        logger.exception("Failed to load videos")
        return []


def render_sidebar() -> Tuple[Optional[str], Dict]:
    """
    Render the sidebar and return user inputs
    Returns: (selected_page, filters_dict)
    """
    init_session_state()
    
    # Custom CSS for sidebar
    st.markdown("""
    <style>
    .sidebar-content {
        background: linear-gradient(180deg, #1e1e2f 0%, #0e1117 100%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.title("🎬 YouTube Analytics")
        st.markdown("---")
        
        # Channel input section
        st.subheader("📡 Channel Operations")
        
        channel_name = st.text_input(
            "Enter Channel Name",
            placeholder="e.g., MrBeast",
            help="Enter a YouTube channel name to fetch data"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            fetch_btn = st.button(
                "Fetch Data",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            refresh_btn = st.button(
                "Refresh",
                use_container_width=True
            )
        
        # Load existing data button
        load_existing = st.button(
            "📂 Load Existing Data",
            use_container_width=True
        )
        
        # Fetch top channels button
        top_channels_btn = st.button(
            "🔥 Fetch Top 50 Channels",
            use_container_width=True,
            help="Fetch top 50 popular channels from YouTube"
        )
        
        st.markdown("---")
        
        # Filters section
        st.subheader("🔍 Filters")
        
        # Load channels for filter
        channels = load_channels_from_db()
        
        if channels:
            channel_options = ["All Channels"] + [c["channel_title"] for c in channels]
            selected_channel = st.selectbox(
                "Select Channel",
                channel_options,
                index=0 if "All Channels" in channel_options else 1
            )
            
            # Get channel_id for selected
            channel_id = None
            if selected_channel != "All Channels":
                selected = next((c for c in channels if c["channel_title"] == selected_channel), None)
                channel_id = selected["channel_id"] if selected else None
        else:
            selected_channel = "All Channels"
            channel_id = None
            st.info("No channels in database. Fetch a channel first.")
        
        # Date range filter
        date_range = st.date_input(
            "Date Range",
            value=[],
            help="Filter videos by publish date"
        )
        
        # Top N videos
        top_n = st.slider(
            "Top N Videos",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
        
        # Sort metric
        sort_metric = st.selectbox(
            "Sort Metric",
            ["views", "likes", "comments", "published_at"],
            index=0
        )
        
        st.markdown("---")
        
        # Database status
        st.subheader("💾 Database Status")
        
        if channels is not None:
            total_channels = len(channels)
            total_videos = len(load_videos_from_db())
            
            st.success(f"✅ Connected")
            st.metric("Channels", total_channels)
            st.metric("Videos", total_videos)
        else:
            st.error("❌ Not Connected")
        
        st.markdown("---")
        
        # Page navigation
        st.subheader("📑 Navigation")
        
        page = st.radio(
            "Go to",
            [
                "Command Center",
                "Video Analytics",
                "Upload Trends",
                "Compare Channels",
                "Raw Data"
            ],
            index=0,
            label_visibility="collapsed"
        )
    
    # Handle button actions
    filters = {
        "channel_id": channel_id,
        "selected_channel": selected_channel,
        "date_range": date_range,
        "top_n": top_n,
        "sort_metric": sort_metric
    }
    
    # Fetch data action
    if fetch_btn and channel_name:
        with st.spinner(f"Fetching data for {channel_name}..."):
            try:
                pipeline = YouTubeETLPipeline()
                success = pipeline.run(channel_name, max_videos=50)
                
                if success:
                    st.success(f"✅ Successfully fetched data for {channel_name}!")
                    # Clear cache to reload data
                    load_channels_from_db.clear()
                    load_videos_from_db.clear()
                else:
                    st.error(f"❌ Failed to fetch data for {channel_name}")
                    
            except Exception as e:
                logger.exception("Fetch failed")
                st.error(f"❌ Error: {str(e)}")
    
    # Refresh action
    if refresh_btn and channel_name:
        with st.spinner(f"Refreshing {channel_name}..."):
            try:
                pipeline = YouTubeETLPipeline()
                success = pipeline.run(channel_name, max_videos=50)
                
                if success:
                    st.success(f"✅ Successfully refreshed {channel_name}!")
                    load_channels_from_db.clear()
                    load_videos_from_db.clear()
                else:
                    st.warning(f"⚠️ No data to refresh for {channel_name}")
                    
            except Exception as e:
                logger.exception("Refresh failed")
                st.error(f"❌ Error: {str(e)}")
    
    # Load existing data action
    if load_existing:
        with st.spinner("Loading existing data..."):
            try:
                channels = load_channels_from_db()
                videos = load_videos_from_db(channel_id)
                
                st.session_state.channels = channels
                st.session_state.videos = videos
                st.session_state.selected_channel = selected_channel
                
                st.success(f"✅ Loaded {len(channels)} channels and {len(videos)} videos!")
                
            except Exception as e:
                logger.exception("Load failed")
                st.error(f"❌ Error: {str(e)}")
    
    # Fetch top channels action
    if top_channels_btn:
        with st.spinner("🔥 Fetching top 50 channels from YouTube... This may take a while."):
            try:
                pipeline = YouTubeETLPipeline()
                success = pipeline.run_top_channels(max_channels=50)
                
                if success:
                    st.success("✅ Successfully fetched top 50 channels!")
                    load_channels_from_db.clear()
                    load_videos_from_db.clear()
                else:
                    st.warning("⚠️ Could not fetch top channels. Check API quota.")
                    
            except Exception as e:
                logger.exception("Top channels fetch failed")
                st.error(f"❌ Error: {str(e)}")
    
    return page, filters


def get_filtered_data(filters: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Get filtered channels and videos based on filters
    """
    channels = load_channels_from_db()
    channel_id = filters.get("channel_id")
    
    videos = load_videos_from_db(channel_id)
    
    # Apply date filter if set
    date_range = filters.get("date_range")
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        videos = [
            v for v in videos
            if v.get("published_at", "") >= str(start_date)
            and v.get("published_at", "") <= str(end_date)
        ]
    
    return channels, videos