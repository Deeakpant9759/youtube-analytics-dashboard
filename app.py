"""
YouTube Creator Intelligence Dashboard
Production-ready Streamlit Analytics Dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dashboard modules
from src.dashboard.sidebar import render_sidebar, get_filtered_data, load_channels_from_db, load_videos_from_db
from src.dashboard.metrics import (
    format_number,
    calculate_engagement_rate,
    render_kpi_card,
    render_kpi_row,
    calculate_channel_metrics,
    calculate_video_metrics,
    get_top_videos,
    prepare_video_dataframe
)
from src.dashboard.charts import (
    create_bar_chart,
    create_pie_chart,
    create_scatter_chart,
    create_scatter_plot,
    create_line_chart,
    create_horizontal_bar_chart,
    create_bubble_chart,
    create_comparison_chart,
    create_monthly_uploads_chart,
    create_weekday_distribution_chart,
    create_views_by_month_chart,
    create_likes_distribution_chart,
    render_chart_container
)

# Page configuration
st.set_page_config(
    page_title="YouTube Creator Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: #0e1117;
    }
    
    /* KPI cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #3d3d5c;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e2f 0%, #0e1117 100%);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* DataFrames */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning {
        border-radius: 8px;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def render_command_center(channels, videos):
    """
    Command Center - Cross-channel ecosystem view
    Shows ALL tracked channels with comparative bubble chart
    """
    st.header("🎯 Command Center")
    st.markdown("### Cross-Channel Ecosystem View")
    
    if not channels:
        st.info("📭 No channels in database yet. Use the sidebar to fetch your first channel!")
        return
    
    # Aggregate metrics across all channels
    total_subscribers = sum(c.get("subscribers", 0) for c in channels)
    total_views = sum(c.get("views", 0) for c in channels)
    total_videos = sum(c.get("total_videos", 0) for c in channels)
    channel_count = len(channels)
    
    # KPI Row - Ecosystem Overview
    st.subheader("🌐 Ecosystem Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tracked Channels", channel_count)
    with col2:
        st.metric("Total Subscribers", format_number(total_subscribers))
    with col3:
        st.metric("Total Views", format_number(total_views))
    with col4:
        st.metric("Total Videos", format_number(total_videos))
    
    st.markdown("---")
    
    # Bubble Chart - Market Positioning
    st.subheader("📊 Market Positioning")
    st.caption("Bubble Size = Total Videos | X = Subscribers | Y = Total Views")
    
    if channels:
        df = pd.DataFrame(channels)
        
        # Create bubble chart
        fig = create_bubble_chart(
            df,
            x="subscribers",
            y="views",
            size="total_videos",
            hover_name="channel_title",
            title="Channel Ecosystem - Market Positioning"
        )
        
        if fig:
            st.plotly_chart(fig, use_container_width=True, height=500)
    
    st.markdown("---")
    
    # Leaderboard
    st.subheader("🏆 Channel Leaderboard")
    
    if channels:
        # Create leaderboard dataframe
        leaderboard = pd.DataFrame(channels)
        
        if not leaderboard.empty:
            # Add rank columns
            leaderboard["Rank"] = leaderboard.sort_values("subscribers", ascending=False).groupby("subscribers").ngroup() + 1
            
            # Select and rename columns for display
            display_cols = ["channel_title", "subscribers", "views", "total_videos", "published_at"]
            display_df = leaderboard[display_cols].copy()
            display_df.columns = ["Channel", "Subscribers", "Total Views", "Total Videos", "Created"]
            
            # Format numbers
            display_df["Subscribers"] = display_df["Subscribers"].apply(format_number)
            display_df["Total Views"] = display_df["Total Views"].apply(format_number)
            display_df["Total Videos"] = display_df["Total Videos"].apply(format_number)
            
            # Sort by subscribers
            display_df = display_df.sort_values("Subscribers", ascending=False)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
    
    st.markdown("---")
    
    # Channel breakdown
    st.subheader("📈 Channel Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Subscribers distribution
        if channels:
            sub_df = pd.DataFrame(channels)[["channel_title", "subscribers"]].sort_values("subscribers", ascending=False)
            sub_df["subscribers"] = sub_df["subscribers"].apply(format_number)
            fig = create_horizontal_bar_chart(
                pd.DataFrame(channels).sort_values("subscribers", ascending=False),
                "subscribers",
                "channel_title",
                "Subscribers by Channel",
                top_n=len(channels),
                color="#FF0000"
            )
            render_chart_container(fig, height=400)
    
    with col2:
        # Views distribution
        if channels:
            fig = create_horizontal_bar_chart(
                pd.DataFrame(channels).sort_values("views", ascending=False),
                "views",
                "channel_title",
                "Total Views by Channel",
                top_n=len(channels),
                color="#3ea6ff"
            )
            render_chart_container(fig, height=400)


def render_overview_page(channels, videos):
    """
    Overview page with KPI cards and summary charts
    """
    st.header("📊 Channel Overview")
    
    if not channels:
        st.warning("No channel data available. Fetch a channel first using the sidebar.")
        return
    
    if not videos:
        st.warning("No video data available.")
        return
    
    # Calculate metrics
    channel_metrics = calculate_channel_metrics(channels)
    video_metrics = calculate_video_metrics(videos)
    
    # Get selected channel info
    selected = channels[0] if channels else {}
    
    # KPI Row 1 - Channel Stats
    st.subheader(f"📈 {selected.get('channel_title', 'Channel')} Statistics")
    
    kpi_metrics = {
        "Subscribers": (format_number(selected.get("subscribers", 0)), None, "👥"),
        "Total Views": (format_number(selected.get("views", 0)), None, "👁️"),
        "Total Videos": (format_number(selected.get("total_videos", 0)), None, "🎥"),
        "Avg Views/Video": (format_number(video_metrics["avg_views"]), None, "📊")
    }
    
    render_kpi_row(kpi_metrics, columns=4)
    
    st.markdown("---")
    
    # KPI Row 2 - Video Engagement
    st.subheader("🔥 Video Engagement")
    
    engagement_metrics = {
        "Total Likes": (format_number(video_metrics["total_likes"]), None, "❤️"),
        "Total Comments": (format_number(video_metrics["total_comments"]), None, "💬"),
        "Avg Likes/Video": (format_number(video_metrics["avg_likes"]), None, "👍"),
        "Avg Engagement": (f"{video_metrics['avg_engagement']}%", None, "📈")
    }
    
    render_kpi_row(engagement_metrics, columns=4)
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top Videos by Views")
        df = prepare_video_dataframe(videos)
        if not df.empty:
            top_videos = get_top_videos(videos, "views", 10)
            top_df = prepare_video_dataframe(top_videos)
            fig = create_horizontal_bar_chart(
                top_df,
                "views",
                "title",
                "Top 10 Videos",
                top_n=10
            )
            render_chart_container(fig, height=400)
    
    with col2:
        st.subheader("❤️ Likes Distribution")
        if not df.empty:
            fig = create_likes_distribution_chart(df)
            render_chart_container(fig, height=400)
    
    st.markdown("---")
    
    # Monthly uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Monthly Uploads")
        if not df.empty:
            fig = create_monthly_uploads_chart(df)
            render_chart_container(fig, height=350)
    
    with col2:
        st.subheader("📊 Uploads by Weekday")
        if not df.empty:
            fig = create_weekday_distribution_chart(df)
            render_chart_container(fig, height=350)


def render_video_analytics_page(channels, videos):
    """
    Video Analytics page with detailed charts
    """
    st.header("🎬 Video Analytics")
    
    if not videos:
        st.warning("No video data available. Fetch a channel first.")
        return
    
    df = prepare_video_dataframe(videos)
    
    # Top 10 videos by views
    st.subheader("🏆 Top 10 Videos by Views")
    
    top_videos = get_top_videos(videos, "views", 10)
    top_df = prepare_video_dataframe(top_videos)
    
    if not top_df.empty:
        fig = create_horizontal_bar_chart(
            top_df,
            "views",
            "title",
            "Top 10 Videos by Views",
            top_n=10,
            color="#FF0000"
        )
        render_chart_container(fig, height=450)
    
    st.markdown("---")
    
    # Scatter plots
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💗 Likes vs Views")
        if not df.empty:
            fig = create_scatter_chart(
                df,
                "views",
                "likes",
                size="comments",
                hover_data=["title"],
                title="Likes vs Views"
            )
            render_chart_container(fig, height=400)
    
    with col2:
        st.subheader("💬 Comments vs Views")
        if not df.empty:
            fig = create_scatter_chart(
                df,
                "views",
                "comments",
                size="likes",
                hover_data=["title"],
                title="Comments vs Views"
            )
            render_chart_container(fig, height=400)
    
    st.markdown("---")
    
    # Engagement Rate ranking
    st.subheader("📈 Engagement Rate Ranking")
    
    if not df.empty:
        # Calculate engagement rate
        df["engagement_rate"] = df.apply(
            lambda x: calculate_engagement_rate(
                x.get("views", 0),
                x.get("likes", 0),
                x.get("comments", 0)
            ),
            axis=1
        )
        
        # Top by engagement
        engagement_df = df.nlargest(15, "engagement_rate")[
            ["title", "views", "likes", "comments", "engagement_rate"]
        ]
        
        fig = create_horizontal_bar_chart(
            engagement_df,
            "engagement_rate",
            "title",
            "Top 15 by Engagement Rate (%)",
            top_n=15,
            color="#4ade80"
        )
        render_chart_container(fig, height=500)
    
    st.markdown("---")
    
    # Video table
    st.subheader("📋 Video Data Table")
    
    if not df.empty:
        # Prepare display dataframe
        display_df = df[[
            "title", "published_at", "views", "likes", "comments", "duration_parsed", "engagement_rate"
        ]].copy()
        
        display_df.columns = [
            "Title", "Published", "Views", "Likes", "Comments", "Duration", "Engagement %"
        ]
        
        # Sort by views by default
        display_df = display_df.sort_values("Views", ascending=False)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )


def render_upload_trends_page(channels, videos):
    """
    Upload Trends page with time-based analysis
    """
    st.header("📅 Upload Trends")
    
    if not videos:
        st.warning("No video data available. Fetch a channel first.")
        return
    
    df = prepare_video_dataframe(videos)
    
    if df.empty:
        st.warning("Not enough data for trends analysis.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Uploads by Month")
        fig = create_monthly_uploads_chart(df)
        render_chart_container(fig, height=400)
    
    with col2:
        st.subheader("📈 Views by Month")
        fig = create_views_by_month_chart(df)
        render_chart_container(fig, height=400)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Uploads by Weekday")
        fig = create_weekday_distribution_chart(df)
        render_chart_container(fig, height=400)
    
    with col2:
        st.subheader("📅 Uploads by Year")
        if "publish_year" in df.columns:
            yearly = df["publish_year"].value_counts().sort_index().reset_index()
            yearly.columns = ["year", "count"]
            fig = px.bar(
                yearly,
                x="year",
                y="count",
                title="Uploads by Year",
                color_discrete_sequence=["#3ea6ff"]
            )
            from src.dashboard.charts import get_chart_theme
            fig.update_layout(**get_chart_theme())
            render_chart_container(fig, height=400)
    
    st.markdown("---")
    
    # Summary stats
    st.subheader("📋 Trend Summary")
    
    if "publish_month_name" in df.columns:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            most_active_month = df["publish_month_name"].mode().iloc[0] if not df["publish_month_name"].mode().empty else "N/A"
            st.metric("Most Active Month", most_active_month)
        
        with col2:
            most_active_weekday = df["publish_weekday"].mode().iloc[0] if not df["publish_weekday"].mode().empty else "N/A"
            st.metric("Most Active Day", most_active_weekday)
        
        with col3:
            if "publish_year" in df.columns:
                latest_year = df["publish_year"].max()
                st.metric("Latest Year", str(latest_year) if pd.notna(latest_year) else "N/A")


def render_compare_channels_page(channels, videos):
    """
    Compare Channels page
    """
    st.header("🔄 Compare Channels")
    
    if len(channels) < 2:
        st.warning("Need at least 2 channels to compare. Fetch more channels first.")
        return
    
    # Channel selection for comparison
    col1, col2 = st.columns(2)
    
    with col1:
        channel1 = st.selectbox(
            "Select Channel 1",
            [c["channel_title"] for c in channels],
            index=0
        )
    
    with col2:
        channel2 = st.selectbox(
            "Select Channel 2",
            [c["channel_title"] for c in channels],
            index=1 if len(channels) > 1 else 0
        )
    
    if channel1 == channel2:
        st.warning("Please select two different channels.")
        return
    
    # Get channel data
    ch1_data = next((c for c in channels if c["channel_title"] == channel1), None)
    ch2_data = next((c for c in channels if c["channel_title"] == channel2), None)
    
    if not ch1_data or not ch2_data:
        st.error("Could not load channel data.")
        return
    
    # Comparison metrics
    st.markdown("---")
    st.subheader("📊 Channel Comparison")
    
    comparison_data = [ch1_data, ch2_data]
    metrics = ["subscribers", "views", "total_videos"]
    
    fig = create_comparison_chart(
        comparison_data,
        metrics,
        "Channel Metrics Comparison"
    )
    render_chart_container(fig, height=400)
    
    st.markdown("---")
    
    # Detailed comparison table
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📈 {channel1}")
        st.metric("Subscribers", format_number(ch1_data.get("subscribers", 0)))
        st.metric("Total Views", format_number(ch1_data.get("views", 0)))
        st.metric("Total Videos", format_number(ch1_data.get("total_videos", 0)))
        
        # Get videos for this channel
        ch1_videos = [v for v in videos if v.get("channel_id") == ch1_data.get("channel_id")]
        if ch1_videos:
            ch1_video_metrics = calculate_video_metrics(ch1_videos)
            st.metric("Avg Views/Video", format_number(ch1_video_metrics["avg_views"]))
            st.metric("Avg Likes/Video", format_number(ch1_video_metrics["avg_likes"]))
    
    with col2:
        st.subheader(f"📈 {channel2}")
        st.metric("Subscribers", format_number(ch2_data.get("subscribers", 0)))
        st.metric("Total Views", format_number(ch2_data.get("views", 0)))
        st.metric("Total Videos", format_number(ch2_data.get("total_videos", 0)))
        
        # Get videos for this channel
        ch2_videos = [v for v in videos if v.get("channel_id") == ch2_data.get("channel_id")]
        if ch2_videos:
            ch2_video_metrics = calculate_video_metrics(ch2_videos)
            st.metric("Avg Views/Video", format_number(ch2_video_metrics["avg_views"]))
            st.metric("Avg Likes/Video", format_number(ch2_video_metrics["avg_likes"]))


def render_raw_data_page(channels, videos):
    """
    Raw Data page with tables and export
    """
    st.header("📋 Raw Data")
    
    tab1, tab2 = st.tabs(["Channels", "Videos"])
    
    with tab1:
        st.subheader("📡 Channel Data")
        
        if channels:
            df = pd.DataFrame(channels)
            
            # Display
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )
            
            # Export
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Channels CSV",
                data=csv,
                file_name="channels.csv",
                mime="text/csv"
            )
        else:
            st.warning("No channel data available.")
    
    with tab2:
        st.subheader("🎬 Video Data")
        
        if videos:
            df = prepare_video_dataframe(videos)
            
            # Select columns for display
            display_cols = ["video_id", "title", "published_at", "views", "likes", "comments", "duration_parsed"]
            display_df = df[display_cols] if not df.empty else pd.DataFrame()
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            # Export
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Videos CSV",
                data=csv,
                file_name="videos.csv",
                mime="text/csv"
            )
        else:
            st.warning("No video data available.")


def main():
    """
    Main application entry point
    """
    try:
        # Render sidebar and get page/filters
        page, filters = render_sidebar()
        
        # Load data based on filters
        channels = load_channels_from_db()
        channel_id = filters.get("channel_id")
        videos = load_videos_from_db(channel_id)
        
        # Route to appropriate page
        if page == "Command Center":
            render_command_center(channels, videos)
        
        elif page == "Video Analytics":
            render_video_analytics_page(channels, videos)
        
        elif page == "Upload Trends":
            render_upload_trends_page(channels, videos)
        
        elif page == "Compare Channels":
            render_compare_channels_page(channels, videos)
        
        elif page == "Raw Data":
            render_raw_data_page(channels, videos)
    
    except Exception as e:
        logger.exception("Application error")
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please refresh the page or check your database connection.")


if __name__ == "__main__":
    main()