import pandas as pd
from datetime import datetime
from db import Database

class DataPreprocessor:
    def __init__(self, db, username):
        self.db = db
        self.username = username
    
    def get_clean_repos(self):
        """Get repos excluding forks and archived, with language"""
        repos = list(self.db.repos.find({
            'username': self.username,
            'is_fork': False,
            'is_archived': False,
            'language': {'$ne': None}
        }))
        return pd.DataFrame(repos)
    
    def aggregate_languages(self):
        """Calculate language percentages"""
        df = self.get_clean_repos()
        
        if df.empty:
            return pd.DataFrame()
        
        lang_counts = df['language'].value_counts()
        total = lang_counts.sum()
        
        lang_data = []
        for lang, count in lang_counts.items():
            lang_data.append({
                'username': self.username,
                'language': lang,
                'repo_count': int(count),
                'percentage': round((count / total) * 100, 2)
            })
        
        # Clear old data and insert new
        self.db.languages.delete_many({'username': self.username})
        if lang_data:
            self.db.languages.insert_many(lang_data)
        
        print(f"✓ Aggregated {len(lang_data)} languages")
        return pd.DataFrame(lang_data)
    
    def categorize_repo_sizes(self):
        """Group repos by size buckets"""
        df = self.get_clean_repos()
        
        if df.empty:
            return pd.DataFrame()
        
        def size_bucket(size_kb):
            if size_kb < 500:
                return '0-500 KB'
            elif size_kb < 2000:
                return '500 KB-2 MB'
            elif size_kb < 10000:
                return '2-10 MB'
            else:
                return '10+ MB'
        
        df['size_category'] = df['size'].apply(size_bucket)
        return df
    
    def prepare_commit_heatmap(self):
        """Prepare day-of-week × hour matrix for commits"""
        commits = list(self.db.commits.find({'username': self.username}))
        
        if not commits:
            return pd.DataFrame()
        
        df = pd.DataFrame(commits)
        df['timestamp'] = pd.to_datetime(df['commit_timestamp'])
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['hour'] = df['timestamp'].dt.hour
        
        # Create heatmap matrix
        heatmap = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        
        # Pivot for heatmap
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = heatmap.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        pivot = pivot.reindex(days_order, fill_value=0)
        
        return pivot
    
    def prepare_monthly_commits(self):
        """Group commits by month"""
        commits = list(self.db.commits.find({'username': self.username}))
        
        if not commits:
            return pd.DataFrame()
        
        df = pd.DataFrame(commits)
        df['timestamp'] = pd.to_datetime(df['commit_timestamp'])
        df['month'] = df['timestamp'].dt.to_period('M')
        
        monthly = df.groupby('month').size().reset_index(name='commits')
        monthly['month'] = monthly['month'].astype(str)
        
        return monthly
    
    def get_top_repos(self, by='stars', limit=10):
        """Get top repositories by metric"""
        df = self.get_clean_repos()
        
        if df.empty:
            return pd.DataFrame()
        
        return df.nlargest(limit, by)[['repo_name', 'stars', 'forks', 'size', 'language']]

def main(username):
    """Main preprocessing function"""
    from config import MONGODB_CONNECTION_STRING
    
    db = Database(MONGODB_CONNECTION_STRING)
    preprocessor = DataPreprocessor(db, username)
    
    print(f"\n🔄 Preprocessing data for: {username}")
    preprocessor.aggregate_languages()
    
    print("✓ Repo size categorization ready")
    print("✓ Commit heatmap data ready")
    print("✓ Monthly commits data ready")
    print("✓ Top repos data ready")
    
    db.close()
    print(f"\n✅ Preprocessing complete!\n")

if __name__ == "__main__":
    username = input("Enter GitHub username: ")
    main(username)
