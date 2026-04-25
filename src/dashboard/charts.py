"""
Charts module for Plotly visualizations
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional


# Color scheme
COLORS = {
    "primary": "#FF0000",  # YouTube red
    "secondary": "#282828",
    "accent": "#3ea6ff",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#f87171",
    "background": "#0e1117",
    "text": "#ffffff",
    "grid": "#2d2d44"
}


def get_chart_theme():
    """
    Return Plotly theme configuration
    """
    return {
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#ffffff", "size": 12},
        "xaxis": {
            "gridcolor": COLORS["grid"],
            "linecolor": COLORS["grid"],
            "tickfont": {"color": "#a0a0b0"}
        },
        "yaxis": {
            "gridcolor": COLORS["grid"],
            "linecolor": COLORS["grid"],
            "tickfont": {"color": "#a0a0b0"}
        }
    }


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    top_n: Optional[int] = None,
    color: str = COLORS["accent"]
) -> go.Figure:
    """
    Create a bar chart
    """
    if df.empty:
        return None
    
    chart_df = df.copy()
    
    if top_n:
        chart_df = chart_df.nlargest(top_n, y)
    
    fig = px.bar(
        chart_df,
        x=x,
        y=y,
        title=title,
        orientation=orientation,
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(marker_line_width=0, opacity=0.8)
    
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
    top_n: Optional[int] = None
) -> go.Figure:
    """
    Create a pie chart
    """
    if df.empty:
        return None
    
    chart_df = df.copy()
    
    if top_n:
        chart_df = chart_df.nlargest(top_n, values)
        other_value = df[~df.index.isin(chart_df.index)][values].sum()
        if other_value > 0:
            other_row = pd.DataFrame({names: ["Other"], values: [other_value]})
            chart_df = pd.concat([chart_df, other_row], ignore_index=True)
    
    fig = px.pie(
        chart_df,
        names=names,
        values=values,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(textposition="inside", textinfo="percent+label")
    
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: Optional[str] = None,
    hover_data: Optional[List[str]] = None,
    title: str = ""
) -> go.Figure:
    """
    Create a scatter plot
    """
    if df.empty:
        return None
    
    fig = px.scatter(
        df,
        x=x,
        y=y,
        size=size,
        hover_data=hover_data,
        title=title,
        color_discrete_sequence=[COLORS["accent"]]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color="white")))
    
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    markers: bool = True
) -> go.Figure:
    """
    Create a line chart
    """
    if df.empty:
        return None
    
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        markers=markers,
        color_discrete_sequence=[COLORS["accent"]]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    
    return fig


def create_horizontal_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    top_n: int = 10,
    color: str = COLORS["primary"]
) -> go.Figure:
    """
    Create a horizontal bar chart (good for rankings)
    """
    if df.empty:
        return None
    
    chart_df = df.nlargest(top_n, x).copy()
    
    fig = px.bar(
        chart_df,
        y=y,
        x=x,
        title=title,
        orientation="h",
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(marker_line_width=0, opacity=0.8)
    fig.update_yaxes(autorange="reversed")
    
    return fig


def create_bubble_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: str,
    hover_name: str,
    title: str = "Bubble Chart",
    color_column: Optional[str] = None
) -> go.Figure:
    """
    Create a bubble chart for ecosystem view
    X=Subscribers, Y=Views, Bubble Size=Total Videos
    """
    if df.empty:
        return None
    
    fig = px.scatter(
        df,
        x=x,
        y=y,
        size=size,
        hover_name=hover_name,
        title=title,
        color=color_column,
        color_discrete_sequence=px.colors.qualitative.Bold,
        size_max=80
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(
        marker=dict(
            opacity=0.7,
            line=dict(width=2, color="white")
        )
    )
    
    # Add annotations for channel names
    for idx, row in df.iterrows():
        fig.add_annotation(
            x=row[x],
            y=row[y],
            text=row[hover_name],
            showarrow=False,
            yshift=15,
            font=dict(size=10, color="white")
        )
    
    return fig


def create_scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "Scatter Plot",
    size: Optional[str] = None,
    hover_data: Optional[List[str]] = None,
    color_column: Optional[str] = None
) -> go.Figure:
    """
    Create a scatter plot (Likes vs Views, Comments vs Views)
    """
    if df.empty:
        return None
    
    fig = px.scatter(
        df,
        x=x,
        y=y,
        size=size,
        hover_data=hover_data,
        title=title,
        color=color_column,
        color_discrete_sequence=[COLORS["accent"]]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color="white")))
    
    return fig


def create_comparison_chart(
    channels: List[Dict],
    metrics: List[str],
    title: str = "Channel Comparison"
) -> go.Figure:
    """
    Create side-by-side comparison bar chart
    """
    if not channels or not metrics:
        return None
    
    channel_names = [c.get("channel_title", "Unknown") for c in channels]
    
    fig = go.Figure()
    
    colors = [COLORS["primary"], COLORS["accent"], COLORS["success"], COLORS["warning"]]
    
    for idx, metric in enumerate(metrics):
        values = [c.get(metric, 0) for c in channels]
        
        fig.add_trace(go.Bar(
            name=metric.replace("_", " ").title(),
            x=channel_names,
            y=values,
            marker_color=colors[idx % len(colors)],
            opacity=0.8
        ))
    
    fig.update_layout(
        **get_chart_theme(),
        title=title,
        barmode="group",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig


def create_monthly_uploads_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create monthly uploads trend chart
    """
    if df.empty or "published_datetime" not in df.columns:
        return None
    
    monthly = df.groupby(df["published_datetime"].dt.to_period("M")).size().reset_index()
    monthly["published_datetime"] = monthly["published_datetime"].astype(str)
    monthly.columns = ["month", "count"]
    
    fig = px.bar(
        monthly,
        x="month",
        y="count",
        title="Uploads by Month",
        color_discrete_sequence=[COLORS["primary"]]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_xaxes(tickangle=45)
    
    return fig


def create_weekday_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create weekday distribution chart
    """
    if df.empty or "publish_weekday" not in df.columns:
        return None
    
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    weekday_counts = df["publish_weekday"].value_counts()
    weekday_counts = weekday_counts.reindex(weekday_order).fillna(0)
    
    weekday_df = pd.DataFrame({
        "weekday": weekday_counts.index,
        "count": weekday_counts.values
    })
    
    fig = px.bar(
        weekday_df,
        x="weekday",
        y="count",
        title="Uploads by Weekday",
        color_discrete_sequence=[COLORS["accent"]]
    )
    
    fig.update_layout(**get_chart_theme())
    
    return fig


def create_views_by_month_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create views by month chart
    """
    if df.empty or "published_datetime" not in df.columns:
        return None
    
    monthly_views = df.groupby(df["published_datetime"].dt.to_period("M")).agg({
        "views": "sum"
    }).reset_index()
    monthly_views["published_datetime"] = monthly_views["published_datetime"].astype(str)
    monthly_views.columns = ["month", "views"]
    
    fig = px.line(
        monthly_views,
        x="month",
        y="views",
        title="Views by Month",
        markers=True,
        color_discrete_sequence=[COLORS["success"]]
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(line=dict(width=3), marker=dict(size=10))
    fig.update_xaxes(tickangle=45)
    
    return fig


def create_likes_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create likes distribution pie chart
    """
    if df.empty:
        return None
    
    # Bin likes into categories
    bins = [0, 1000, 10000, 100000, 1000000, float("inf")]
    labels = ["<1K", "1K-10K", "10K-100K", "100K-1M", "1M+"]
    
    df_copy = df.copy()
    df_copy["likes_category"] = pd.cut(
        df_copy["likes"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )
    
    likes_dist = df_copy["likes_category"].value_counts().reset_index()
    likes_dist.columns = ["category", "count"]
    
    fig = px.pie(
        likes_dist,
        names="category",
        values="count",
        title="Likes Distribution",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig.update_layout(**get_chart_theme())
    fig.update_traces(textposition="inside", textinfo="percent+label")
    
    return fig


def render_chart_container(fig: go.Figure, height: int = 400):
    """
    Render a chart in Streamlit with container styling
    """
    if fig:
        st.plotly_chart(fig, use_container_width=True, height=height)
    else:
        st.warning("No data available for chart.")