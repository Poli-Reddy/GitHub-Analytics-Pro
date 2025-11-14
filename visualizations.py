import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from db import Database
from preprocess import DataPreprocessor

def get_now():
    """Get current datetime without timezone info"""
    return pd.Timestamp.now().tz_localize(None)

LANGUAGE_COLORS = {
    'Python': '#3776ab', 'JavaScript': '#f7df1e', 'TypeScript': '#3178c6',
    'Java': '#b07219', 'C++': '#f34b7d', 'C': '#555555', 'C#': '#178600',
    'Go': '#00add8', 'Rust': '#dea584', 'Ruby': '#701516', 'PHP': '#4f5d95',
    'Swift': '#ffac45', 'Kotlin': '#a97bff', 'Dart': '#00b4ab',
    'HTML': '#e34c26', 'CSS': '#563d7c', 'Shell': '#89e051'
}

class Visualizations:
    def __init__(self, db, username):
        self.db = db
        self.username = username
        self.preprocessor = DataPreprocessor(db, username)
    
    # ========== OVERVIEW SECTION ==========
    
    def overview_star_growth_line(self):
        """Line Chart: Star Growth Over Time"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at')
        df['cumulative_stars'] = df['stars'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['created_at'], 
            y=df['cumulative_stars'],
            mode='lines+markers',
            line=dict(color='#e94560', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(233, 69, 96, 0.2)'
        ))
        
        fig.update_layout(
            title='Star Growth Over Time',
            xaxis_title='Date',
            yaxis_title='Cumulative Stars',
            template='plotly_white',
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            font=dict(family='Inter, sans-serif', color='#24292f'),
            title_font=dict(size=18, color='#1f6feb', family='Inter, sans-serif')
        )
        return fig

    
    def overview_monthly_commits_bar(self):
        """Simple Bar Chart: Monthly Commits"""
        commits = list(self.db.commits.find({'username': self.username}))
        if not commits:
            return None
        
        df = pd.DataFrame(commits)
        df['timestamp'] = pd.to_datetime(df['commit_timestamp'])
        df['month'] = df['timestamp'].dt.to_period('M')
        monthly = df.groupby('month').size().reset_index(name='commits')
        monthly['month'] = monthly['month'].astype(str)
        
        fig = go.Figure(data=[
            go.Bar(x=monthly['month'], y=monthly['commits'], marker_color='#1f6feb')
        ])
        
        fig.update_layout(
            title='Monthly Commits',
            xaxis_title='Month',
            yaxis_title='Commits',
            template='plotly_white',
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            font=dict(family='Inter, sans-serif', color='#24292f'),
            title_font=dict(size=18, color='#1f6feb', family='Inter, sans-serif')
        )
        return fig
    
    def overview_contribution_calendar(self):
        """Calendar Heatmap: Contribution Calendar"""
        commits = list(self.db.commits.find({'username': self.username}))
        if not commits:
            return None
        
        df = pd.DataFrame(commits)
        df['date'] = pd.to_datetime(df['commit_timestamp']).dt.date
        daily_commits = df.groupby('date').size().reset_index(name='commits')
        daily_commits['date'] = pd.to_datetime(daily_commits['date'])
        daily_commits['week'] = daily_commits['date'].dt.isocalendar().week
        daily_commits['day_of_week'] = daily_commits['date'].dt.dayofweek
        
        # Aggregate by week and day to handle duplicates
        weekly_commits = daily_commits.groupby(['day_of_week', 'week'])['commits'].sum().reset_index()
        pivot = weekly_commits.pivot(index='day_of_week', columns='week', values='commits').fillna(0)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            colorscale='Reds',
            showscale=True
        ))
        
        fig.update_layout(
            title='Contribution Calendar',
            xaxis_title='Week of Year',
            yaxis_title='Day of Week',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    
    # ========== REPOSITORIES SECTION ==========
    
    def repo_leaderboard_table(self):
        """Leaderboard Table: Top Repos"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
        df['age_days'] = (get_now() - df['created_at']).dt.days + 1
        df['star_velocity'] = (df['stars'] / df['age_days'] * 30).round(2)
        
        return {
            'stars': df.nlargest(10, 'stars')[['repo_name', 'stars', 'forks', 'language']],
            'forks': df.nlargest(10, 'forks')[['repo_name', 'stars', 'forks', 'language']],
            'size': df.nlargest(10, 'size')[['repo_name', 'size', 'language']]
        }
    
    def repo_size_histogram(self):
        """Histogram: Repository Size Distribution"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        fig = go.Figure(data=[
            go.Histogram(x=df['size'], nbinsx=20, marker_color='#e94560')
        ])
        
        fig.update_layout(
            title='Repository Size Distribution',
            xaxis_title='Size (KB)',
            yaxis_title='Number of Repos',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def repo_topics_treemap(self):
        """Treemap: Repository Topics"""
        topics_data = list(self.db.topics.find({'username': self.username}))
        if not topics_data:
            return None
        
        topic_list = []
        for item in topics_data:
            for topic in item['topics']:
                topic_list.append({'topic': topic, 'repo': item['repo']})
        
        if not topic_list:
            return None
        
        df = pd.DataFrame(topic_list)
        topic_counts = df.groupby('topic').size().reset_index(name='count')
        
        fig = px.treemap(
            topic_counts,
            path=['topic'],
            values='count',
            title='Repository Topics',
            color='count',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    
    # ========== SKILLS SECTION ==========
    
    def skills_language_pie(self):
        """Pie Chart: Language Usage %"""
        langs = list(self.db.languages.find({'username': self.username}))
        if not langs:
            return None
        
        df = pd.DataFrame(langs)
        
        fig = px.pie(
            df, 
            values='repo_count', 
            names='language',
            title='Programming Languages',
            color='language',
            color_discrete_map=LANGUAGE_COLORS
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def skills_radar_chart(self):
        """Radar Chart: Developer Skill Profile"""
        user = self.db.users.find_one({'username': self.username})
        repos = list(self.db.repos.find({'username': self.username, 'is_fork': False}))
        commits = list(self.db.commits.find({'username': self.username}))
        langs = list(self.db.languages.find({'username': self.username}))
        
        if not user or not repos:
            return None
        
        metrics = {
            'Stars': min(sum(r['stars'] for r in repos) / 10, 100),
            'Forks': min(sum(r['forks'] for r in repos) / 5, 100),
            'Repos': min(len(repos) * 5, 100),
            'Commits': min(len(commits) / 10, 100),
            'Languages': min(len(langs) * 10, 100),
            'Followers': min(user['followers'] / 2, 100)
        }
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(metrics.values()),
            theta=list(metrics.keys()),
            fill='toself',
            line_color='#e94560',
            fillcolor='rgba(233, 69, 96, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title='Developer Skill Radar',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def skills_language_horizontal_bar(self):
        """Horizontal Bar: Language Popularity"""
        langs = list(self.db.languages.find({'username': self.username}))
        if not langs:
            return None
        
        df = pd.DataFrame(langs).sort_values('repo_count', ascending=True)
        
        fig = go.Figure(data=[
            go.Bar(
                y=df['language'], 
                x=df['repo_count'], 
                orientation='h',
                marker_color='#e94560'
            )
        ])
        
        fig.update_layout(
            title='Languages by Repo Count',
            xaxis_title='Number of Repos',
            yaxis_title='Language',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    
    # ========== ACTIVITY SECTION ==========
    
    def activity_commit_heatmap(self):
        """Day × Hour Heatmap: Commit Activity"""
        commits = list(self.db.commits.find({'username': self.username}))
        if not commits:
            return None
        
        df = pd.DataFrame(commits)
        df['timestamp'] = pd.to_datetime(df['commit_timestamp'])
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['hour'] = df['timestamp'].dt.hour
        
        heatmap = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = heatmap.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        pivot = pivot.reindex(days_order, fill_value=0)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=list(range(24)),
            y=days_order,
            colorscale='Reds'
        ))
        
        fig.update_layout(
            title='Commit Activity Heatmap',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def activity_timeline_scatter(self):
        """Scatter Timeline: GitHub Activity"""
        events = list(self.db.activity.find({'username': self.username}))
        if not events:
            return None
        
        df = pd.DataFrame(events)
        df['created_at'] = pd.to_datetime(df['created_at'])
        event_counts = df.groupby(['created_at', 'event_type']).size().reset_index(name='count')
        
        fig = px.scatter(
            event_counts, 
            x='created_at', 
            y='event_type', 
            size='count',
            color='event_type',
            title='Activity Timeline'
        )
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Event Type',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def activity_event_bars(self):
        """Bar Chart: Event Type Breakdown"""
        events = list(self.db.activity.find({'username': self.username}))
        if not events:
            return None
        
        df = pd.DataFrame(events)
        event_counts = df['event_type'].value_counts()
        
        fig = go.Figure(data=[
            go.Bar(x=event_counts.index, y=event_counts.values, marker_color='#e94560')
        ])
        
        fig.update_layout(
            title='Event Type Breakdown',
            xaxis_title='Event Type',
            yaxis_title='Count',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    
    # ========== PRODUCTIVITY SECTION ==========
    
    def productivity_commit_trend(self):
        """Smoothed Line: Commit Trend with Rolling Average"""
        commits = list(self.db.commits.find({'username': self.username}))
        if not commits:
            return None
        
        df = pd.DataFrame(commits)
        df['timestamp'] = pd.to_datetime(df['commit_timestamp'])
        df['date'] = df['timestamp'].dt.date
        daily = df.groupby('date').size().reset_index(name='commits')
        daily['date'] = pd.to_datetime(daily['date'])
        daily['rolling_avg'] = daily['commits'].rolling(window=7, min_periods=1).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily['date'], 
            y=daily['commits'], 
            mode='lines',
            name='Daily',
            line=dict(color='rgba(233, 69, 96, 0.3)', width=1)
        ))
        fig.add_trace(go.Scatter(
            x=daily['date'], 
            y=daily['rolling_avg'], 
            mode='lines',
            name='7-Day Avg',
            line=dict(color='#e94560', width=3)
        ))
        
        fig.update_layout(
            title='Commit Trend (7-Day Rolling Average)',
            xaxis_title='Date',
            yaxis_title='Commits',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def productivity_pr_donut(self):
        """Donut Chart: Issue Status"""
        repos = list(self.db.repos.find({'username': self.username, 'is_fork': False}))
        if not repos:
            return None
        
        total_issues = sum(r.get('open_issues', 0) for r in repos)
        
        if total_issues == 0:
            return None
        
        # Estimate closed issues (GitHub API limitation)
        closed_issues = total_issues * 2
        
        fig = go.Figure(data=[go.Pie(
            labels=['Open Issues', 'Closed Issues (Est.)'],
            values=[total_issues, closed_issues],
            hole=.4,
            marker_colors=['#e94560', '#4ecca3']
        )])
        
        fig.update_layout(
            title='Issue Status',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    
    # ========== GROWTH SECTION ==========
    
    def growth_star_line(self):
        """Line Chart: Star Growth"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at')
        df['cumulative_stars'] = df['stars'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['created_at'], 
            y=df['cumulative_stars'],
            mode='lines+markers',
            line=dict(color='#e94560', width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title='Star Growth',
            xaxis_title='Date',
            yaxis_title='Total Stars',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def growth_fork_line(self):
        """Line Chart: Fork Growth"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at')
        df['cumulative_forks'] = df['forks'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['created_at'], 
            y=df['cumulative_forks'],
            mode='lines+markers',
            line=dict(color='#4ecca3', width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title='Fork Growth',
            xaxis_title='Date',
            yaxis_title='Total Forks',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def growth_trending_repos(self):
        """Bubble Chart: Trending Repos"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        # Filter repos with at least 1 star
        df = df[df['stars'] > 0].copy()
        if df.empty:
            return None
        
        try:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
            df['age_days'] = (get_now() - df['created_at']).dt.days + 1
            df['star_velocity'] = (df['stars'] / df['age_days'] * 30).round(2)
            
            # Filter out repos with 0 velocity
            df = df[df['star_velocity'] > 0]
            if df.empty:
                return None
            
            # Fill missing languages
            df['language'] = df['language'].fillna('Unknown')
            
            fig = px.scatter(
                df,
                x='created_at',
                y='star_velocity',
                size='stars',
                color='language',
                hover_data=['repo_name'],
                title='Trending Repositories',
                color_discrete_map=LANGUAGE_COLORS
            )
            
            fig.update_layout(
                xaxis_title='Creation Date',
                yaxis_title='Stars per Month',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            return fig
        except Exception as e:
            print(f"Error in growth_trending_repos: {str(e)}")
            return None

    
    def repo_language_relationship(self):
        """Grouped Bar Chart: Repositories by Language"""
        df = self.preprocessor.get_clean_repos()
        if df.empty:
            return None
        
        # Group by language and count repos
        lang_repos = df.groupby('language').agg({
            'repo_name': 'count',
            'stars': 'sum',
            'forks': 'sum'
        }).reset_index()
        
        lang_repos.columns = ['language', 'repo_count', 'total_stars', 'total_forks']
        lang_repos = lang_repos.sort_values('repo_count', ascending=False).head(10)
        
        if lang_repos.empty:
            return None
        
        fig = go.Figure()
        
        # Add bars for repo count
        fig.add_trace(go.Bar(
            name='Repositories',
            x=lang_repos['language'],
            y=lang_repos['repo_count'],
            marker_color='#e94560',
            yaxis='y',
            offsetgroup=1
        ))
        
        # Add bars for stars
        fig.add_trace(go.Bar(
            name='Total Stars',
            x=lang_repos['language'],
            y=lang_repos['total_stars'],
            marker_color='#4ecca3',
            yaxis='y2',
            offsetgroup=2
        ))
        
        fig.update_layout(
            title='Repositories & Stars by Language',
            xaxis_title='Programming Language',
            yaxis=dict(
                title='Number of Repositories',
                titlefont=dict(color='#e94560'),
                tickfont=dict(color='#e94560')
            ),
            yaxis2=dict(
                title='Total Stars',
                titlefont=dict(color='#4ecca3'),
                tickfont=dict(color='#4ecca3'),
                anchor='x',
                overlaying='y',
                side='right'
            ),
            barmode='group',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(x=0.01, y=0.99)
        )
        
        return fig
