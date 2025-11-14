import requests
from datetime import datetime
from db import Database

class GitHubFetcher:
    def __init__(self, db):
        self.db = db
        self.base_url = "https://api.github.com"
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
    
    def fetch_user(self, username):
        """Fetch user profile data"""
        url = f"{self.base_url}/users/{username}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 403:
            error_msg = response.json().get('message', 'API rate limit exceeded')
            raise Exception(f"GitHub API Error: {error_msg}. Wait 1 hour or use GitHub token for higher limits.")
        
        if response.status_code == 404:
            raise Exception(f"User not found: {username}. Check the username spelling.")
        
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Unknown error')
            raise Exception(f"GitHub API Error ({response.status_code}): {error_msg}")
        
        data = response.json()
        user_doc = {
            'username': username,
            'followers': data.get('followers', 0),
            'following': data.get('following', 0),
            'public_repos': data.get('public_repos', 0),
            'avatar': data.get('avatar_url', ''),
            'updated_at': datetime.utcnow()
        }
        
        self.db.users.insert_one(user_doc)
        print(f"✓ Fetched user: {username}")
        return user_doc
    
    def fetch_repos(self, username):
        """Fetch all repositories with pagination"""
        repos = []
        page = 1
        
        try:
            while True:
                url = f"{self.base_url}/users/{username}/repos?per_page=100&page={page}"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data or not isinstance(data, list):
                    break
                
                for repo in data:
                    repo_doc = {
                        'username': username,
                        'repo_name': repo['name'],
                        'stars': repo.get('stargazers_count', 0),
                        'forks': repo.get('forks_count', 0),
                        'size': repo.get('size', 0),
                        'language': repo.get('language'),
                        'created_at': repo.get('created_at'),
                        'updated_at': repo.get('updated_at'),
                        'is_fork': repo.get('fork', False),
                        'is_archived': repo.get('archived', False),
                        'topics': repo.get('topics', []),
                        'open_issues': repo.get('open_issues_count', 0)
                    }
                    repos.append(repo_doc)
                
                page += 1
            
            if repos:
                self.db.repos.insert_many(repos)
            print(f"✓ Fetched {len(repos)} repositories")
        except Exception as e:
            print(f"Error fetching repos: {str(e)}")
        
        return repos
    
    def fetch_events(self, username):
        """Fetch user activity events"""
        url = f"{self.base_url}/users/{username}/events?per_page=100"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
        
        events = []
        for event in response.json():
            event_doc = {
                'username': username,
                'event_type': event.get('type'),
                'repo': event.get('repo', {}).get('name'),
                'created_at': event.get('created_at')
            }
            events.append(event_doc)
        
        if events:
            self.db.activity.insert_many(events)
        print(f"✓ Fetched {len(events)} activity events")
        return events
    
    def fetch_commits(self, username, repos):
        """Fetch commits for each repository"""
        commits = []
        
        if not repos or not isinstance(repos, list):
            print("No repos to fetch commits from")
            return commits
        
        try:
            for repo in repos[:10]:  # Limit to first 10 repos to avoid rate limits
                if not isinstance(repo, dict):
                    continue
                    
                if repo.get('is_fork') or repo.get('is_archived'):
                    continue
                
                repo_name = repo.get('repo_name')
                if not repo_name:
                    continue
                    
                url = f"{self.base_url}/repos/{username}/{repo_name}/commits?per_page=100"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    continue
                
                commit_data = response.json()
                if not isinstance(commit_data, list):
                    continue
                
                for commit in commit_data:
                    commit_doc = {
                        'username': username,
                        'repo': repo_name,
                        'commit_timestamp': commit.get('commit', {}).get('author', {}).get('date'),
                        'message': commit.get('commit', {}).get('message', '')[:100]
                    }
                    commits.append(commit_doc)
            
            if commits:
                self.db.commits.insert_many(commits)
            print(f"✓ Fetched {len(commits)} commits")
        except Exception as e:
            print(f"Error fetching commits: {str(e)}")
        
        return commits
    
    def fetch_repo_topics(self, username, repos):
        """Fetch topics for repositories"""
        topics_data = []
        
        if not repos or not isinstance(repos, list):
            print("No repos to fetch topics from")
            return topics_data
        
        try:
            for repo in repos[:20]:
                if not isinstance(repo, dict):
                    continue
                    
                if repo.get('is_fork') or repo.get('is_archived'):
                    continue
                
                repo_name = repo.get('repo_name')
                if not repo_name:
                    continue
                    
                url = f"{self.base_url}/repos/{username}/{repo_name}/topics"
                headers = {**self.headers, 'Accept': 'application/vnd.github.mercy-preview+json'}
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    topics = response.json().get('names', [])
                    if topics:
                        topics_data.append({
                            'username': username,
                            'repo': repo_name,
                            'topics': topics
                        })
            
            if topics_data:
                self.db.topics.insert_many(topics_data)
            print(f"✓ Fetched topics for {len(topics_data)} repos")
        except Exception as e:
            print(f"Error fetching topics: {str(e)}")
        
        return topics_data

def main(username):
    """Main function to fetch all data"""
    from config import MONGODB_CONNECTION_STRING
    
    db = Database(MONGODB_CONNECTION_STRING)
    db.clear_user_data(username)
    
    fetcher = GitHubFetcher(db)
    
    print(f"\n🔄 Fetching data for: {username}")
    fetcher.fetch_user(username)
    repos = fetcher.fetch_repos(username)
    fetcher.fetch_events(username)
    fetcher.fetch_commits(username, repos)
    fetcher.fetch_repo_topics(username, repos)
    
    db.close()
    print(f"\n✅ Data fetch complete!\n")

if __name__ == "__main__":
    username = input("Enter GitHub username: ")
    main(username)
