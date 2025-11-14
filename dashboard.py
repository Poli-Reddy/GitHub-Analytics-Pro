import streamlit as st
import plotly.graph_objects as go
from db import Database
from fetch_data import GitHubFetcher
from preprocess import DataPreprocessor
from visualizations import Visualizations
from config import MONGODB_CONNECTION_STRING

st.set_page_config(page_title="GitHub Analytics Pro", layout="wide", initial_sidebar_state="expanded")

def show_no_data_chart(title):
    """Create an empty chart with NO DATA message"""
    fig = go.Figure()
    
    fig.add_annotation(
        text="NO DATA",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=60, color="#e94560", family="Poppins"),
        opacity=0.3
    )
    
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    
    return fig

# Professional Light Mode CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Background */
    .main {
        background-color: #f6f8fa;
    }
    
    .stApp {
        background-color: #f6f8fa;
    }
    
    /* Project Header */
    .project-header {
        background: #ffffff;
        padding: 30px 40px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        border: 1px solid #d0d7de;
        text-align: center;
    }
    
    .project-title {
        font-size: 36px;
        font-weight: 700;
        color: #1f6feb;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .project-subtitle {
        font-size: 15px;
        color: #57606a;
        margin-top: 8px;
        font-weight: 400;
    }
    
    /* Username Display */
    .username-display {
        font-size: 24px;
        font-weight: 600;
        color: #24292f;
        margin-bottom: 20px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: #1f6feb;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 13px;
        font-weight: 600;
        color: #57606a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar */
    div[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #d0d7de;
    }
    
    div[data-testid="stSidebar"] > div:first-child {
        background-color: #ffffff;
    }
    
    /* Sidebar Headers */
    .sidebar-header {
        font-size: 14px;
        font-weight: 600;
        color: #24292f;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        padding: 8px 0;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1f6feb;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    
    .stButton > button:hover {
        background-color: #1158c7;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }
    
    /* Section Headers */
    h2 {
        color: #24292f;
        font-weight: 700;
        font-size: 28px;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #d0d7de;
    }
    
    h3 {
        color: #24292f;
        font-weight: 600;
        font-size: 20px;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        color: #24292f;
        padding: 8px 12px;
        font-size: 14px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1f6feb;
        box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.1);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #6e7781;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        color: #57606a;
        font-size: 14px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f6feb;
        color: #ffffff;
        border-color: #1f6feb;
    }
    
    /* Dataframe */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 6px;
    }
    
    /* Divider */
    hr {
        border-color: #d0d7de;
        margin: 24px 0;
    }
    
    /* Info/Success/Error boxes */
    .stAlert {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        border-left: 3px solid #1f6feb;
    }
    
    /* Section-specific colors */
    .section-overview {
        border-left-color: #1f6feb;
    }
    
    .section-repositories {
        border-left-color: #8250df;
    }
    
    .section-skills {
        border-left-color: #d29922;
    }
    
    .section-activity {
        border-left-color: #cf222e;
    }
    
    .section-productivity {
        border-left-color: #2ea043;
    }
    
    .section-growth {
        border-left-color: #1f6feb;
    }
</style>
""", unsafe_allow_html=True)

if 'username' not in st.session_state:
    st.session_state.username = ''
if 'section' not in st.session_state:
    st.session_state.section = 'Overview'


# Sidebar
with st.sidebar:
    st.markdown("### ⚙ Control Panel")
    
    username = st.text_input("GitHub Username", value=st.session_state.username)
    
    if st.button("↻ Fetch Data", use_container_width=True):
        if username:
            try:
                db = Database(MONGODB_CONNECTION_STRING)
                
                # Check if user already exists in database
                existing_user = db.users.find_one({'username': username})
                
                if existing_user:
                    # User exists, load from database
                    st.session_state.username = username
                    st.success(f"✅ Loaded {username} from database!")
                    st.rerun()
                else:
                    # User doesn't exist, fetch from API
                    with st.spinner(f"Fetching {username} from GitHub..."):
                        fetcher = GitHubFetcher(db)
                        fetcher.fetch_user(username)
                        repos = fetcher.fetch_repos(username)
                        fetcher.fetch_events(username)
                        fetcher.fetch_commits(username, repos)
                        fetcher.fetch_repo_topics(username, repos)
                        DataPreprocessor(db, username).aggregate_languages()
                        st.session_state.username = username
                        st.success("✅ Fetched and saved!")
                        st.rerun()
                
                db.close()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    st.markdown("### 📑 Navigation")
    
    sections = ['Overview', 'Repositories', 'Skills', 'Activity', 'Productivity', 'Growth']
    for section in sections:
        if st.button(section, use_container_width=True, key=f"nav_{section}"):
            st.session_state.section = section
            st.rerun()
    
    st.divider()
    
    # Refresh data option
    if st.session_state.username:
        if st.button("🔄 Refresh from GitHub", use_container_width=True):
            try:
                db = Database(MONGODB_CONNECTION_STRING)
                db.clear_user_data(st.session_state.username)
                
                with st.spinner(f"Refreshing {st.session_state.username}..."):
                    fetcher = GitHubFetcher(db)
                    fetcher.fetch_user(st.session_state.username)
                    repos = fetcher.fetch_repos(st.session_state.username)
                    fetcher.fetch_events(st.session_state.username)
                    fetcher.fetch_commits(st.session_state.username, repos)
                    fetcher.fetch_repo_topics(st.session_state.username, repos)
                    DataPreprocessor(db, st.session_state.username).aggregate_languages()
                    st.success("✅ Data refreshed!")
                    st.rerun()
                
                db.close()
            except Exception as e:
                st.error(f"Error: {str(e)}")


# Main Content
if st.session_state.username:
    try:
        db = Database(MONGODB_CONNECTION_STRING)
        user = db.users.find_one({'username': st.session_state.username})
        
        if user:
            st.markdown("""
            <div class="project-header">
                <div class="project-title">GitHub Analytics Pro</div>
                <div class="project-subtitle">Professional Developer Insights & Performance Metrics</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"### @{st.session_state.username}")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.image(user['avatar'], width=100)
            with col2:
                st.metric("Followers", user['followers'])
            with col3:
                st.metric("Following", user['following'])
            with col4:
                st.metric("Repositories", user['public_repos'])
            with col5:
                repos = list(db.repos.find({'username': st.session_state.username, 'is_fork': False}))
                st.metric("Total Stars", sum(r['stars'] for r in repos))
            
            st.divider()
            
            viz = Visualizations(db, st.session_state.username)
            section = st.session_state.section

            
            if section == 'Overview':
                st.markdown("## Overview Dashboard")
                col1, col2 = st.columns(2)
                with col1:
                    fig = viz.overview_star_growth_line()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Star Growth Over Time"), use_container_width=True)
                with col2:
                    fig = viz.overview_monthly_commits_bar()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Monthly Commits"), use_container_width=True)
                
                fig = viz.overview_contribution_calendar()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.plotly_chart(show_no_data_chart("Contribution Calendar"), use_container_width=True)
            
            elif section == 'Repositories':
                st.markdown("## Repository Analytics")
                
                leaderboards = viz.repo_leaderboard_table()
                if leaderboards:
                    tab1, tab2, tab3 = st.tabs(["★ Stars", "⑂ Forks", "📦 Size"])
                    with tab1:
                        st.dataframe(leaderboards['stars'], use_container_width=True, hide_index=True)
                    with tab2:
                        st.dataframe(leaderboards['forks'], use_container_width=True, hide_index=True)
                    with tab3:
                        st.dataframe(leaderboards['size'], use_container_width=True, hide_index=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = viz.repo_size_histogram()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Repository Size Distribution"), use_container_width=True)
                with col2:
                    fig = viz.repo_topics_treemap()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Repository Topics"), use_container_width=True)
                
                # New: Repository & Language Relationship
                fig = viz.repo_language_relationship()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.plotly_chart(show_no_data_chart("Repositories & Stars by Language"), use_container_width=True)

            
            elif section == 'Skills':
                st.markdown("## Skills & Expertise")
                col1, col2 = st.columns(2)
                with col1:
                    fig = viz.skills_language_pie()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Programming Languages"), use_container_width=True)
                with col2:
                    fig = viz.skills_radar_chart()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Developer Skill Radar"), use_container_width=True)
                
                fig = viz.skills_language_horizontal_bar()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.plotly_chart(show_no_data_chart("Languages by Repo Count"), use_container_width=True)
            
            elif section == 'Activity':
                st.markdown("## Activity Analytics")
                col1, col2 = st.columns(2)
                with col1:
                    fig = viz.activity_commit_heatmap()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Commit Activity Heatmap"), use_container_width=True)
                with col2:
                    fig = viz.activity_timeline_scatter()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Activity Timeline"), use_container_width=True)
                
                fig = viz.activity_event_bars()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.plotly_chart(show_no_data_chart("Event Type Breakdown"), use_container_width=True)
            
            elif section == 'Productivity':
                st.markdown("## Productivity Metrics")
                col1, col2 = st.columns(2)
                with col1:
                    fig = viz.productivity_commit_trend()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Commit Trend (7-Day Rolling Average)"), use_container_width=True)
                with col2:
                    fig = viz.productivity_pr_donut()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Issue Status"), use_container_width=True)
            
            elif section == 'Growth':
                st.markdown("## Growth Metrics")
                col1, col2 = st.columns(2)
                with col1:
                    fig = viz.growth_star_line()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Star Growth"), use_container_width=True)
                with col2:
                    fig = viz.growth_fork_line()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.plotly_chart(show_no_data_chart("Fork Growth"), use_container_width=True)
                
                fig = viz.growth_trending_repos()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.plotly_chart(show_no_data_chart("Trending Repositories"), use_container_width=True)
        
        db.close()
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.markdown("""
    <div class="project-header">
        <div class="project-title">GitHub Analytics Pro</div>
        <div class="project-subtitle">Professional Developer Insights & Performance Metrics</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("← Enter a GitHub username in the sidebar to begin")
