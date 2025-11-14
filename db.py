from pymongo import MongoClient
from datetime import datetime

class Database:
    def __init__(self, connection_string):
        """Initialize MongoDB Atlas connection"""
        self.client = MongoClient(connection_string)
        self.db = self.client['github_dashboard']
        
        # Collections
        self.users = self.db['users']
        self.repos = self.db['repos']
        self.commits = self.db['commits']
        self.languages = self.db['languages']
        self.activity = self.db['activity']
        self.topics = self.db['topics']
    
    def clear_user_data(self, username):
        """Clear all data for a specific user (for refresh)"""
        self.users.delete_many({'username': username})
        self.repos.delete_many({'username': username})
        self.commits.delete_many({'username': username})
        self.languages.delete_many({'username': username})
        self.activity.delete_many({'username': username})
        self.topics.delete_many({'username': username})
    
    def user_exists(self, username):
        """Check if user data exists in database"""
        return self.users.find_one({'username': username}) is not None
    
    def close(self):
        """Close database connection"""
        self.client.close()
