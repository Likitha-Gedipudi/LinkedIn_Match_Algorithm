"""
GitHub profile scraper using the official GitHub API.
Collects developer profiles, skills, and contributions.
"""

import json
from typing import Any, Dict, List, Optional

from .base_scraper import BaseScraper
from ..utils import generate_id, get_logger

logger = get_logger()


class GitHubScraper(BaseScraper):
    """
    Scraper for GitHub profiles using the official API.
    
    Requires: GitHub Personal Access Token
    Rate Limit: 5000 requests/hour (authenticated)
    """
    
    API_BASE_URL = "https://api.github.com"
    
    def __init__(self, api_token: str, **kwargs):
        """
        Initialize GitHub scraper.
        
        Args:
            api_token: GitHub Personal Access Token
        """
        self.api_token = api_token
        super().__init__(**kwargs)
        self.profiles_scraped = []
    
    def _get_headers(self) -> Dict[str, str]:
        """Override to add GitHub API authentication."""
        headers = super()._get_headers()
        headers.update({
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        })
        return headers
    
    def scrape_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a GitHub user profile.
        
        Args:
            username: GitHub username
            
        Returns:
            Profile data dictionary
        """
        try:
            # Get user data
            user_url = f"{self.API_BASE_URL}/users/{username}"
            user_response = self.fetch_url(user_url)
            
            if not user_response:
                return None
            
            user_data = user_response.json()
            
            # Get additional data
            repos = self._get_user_repos(username)
            languages = self._aggregate_languages(repos)
            
            profile = {
                "profile_id": generate_id(username),
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "location": user_data.get("location"),
                "company": user_data.get("company"),
                "email": user_data.get("email"),
                "blog": user_data.get("blog"),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at"),
                "repositories": repos[:10],  # Top 10 repos
                "primary_languages": languages[:15],  # Top 15 languages
                "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
                "source": "github",
            }
            
            self.profiles_scraped.append(profile)
            logger.info(f"Successfully scraped GitHub profile: {username}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to scrape GitHub profile {username}: {str(e)}")
            return None
    
    def _get_user_repos(self, username: str, max_repos: int = 100) -> List[Dict]:
        """Get user's public repositories."""
        repos = []
        
        try:
            repos_url = f"{self.API_BASE_URL}/users/{username}/repos"
            response = self.fetch_url(
                repos_url,
                params={"sort": "updated", "per_page": min(max_repos, 100)}
            )
            
            if response:
                repos_data = response.json()
                
                for repo in repos_data:
                    repos.append({
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "is_fork": repo.get("fork", False),
                        "created_at": repo.get("created_at"),
                        "updated_at": repo.get("updated_at"),
                    })
        
        except Exception as e:
            logger.warning(f"Could not fetch repos for {username}: {str(e)}")
        
        return repos
    
    def _aggregate_languages(self, repos: List[Dict]) -> List[str]:
        """Aggregate and rank programming languages from repositories."""
        language_counts = {}
        
        for repo in repos:
            lang = repo.get("language")
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # Sort by frequency
        sorted_languages = sorted(
            language_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [lang for lang, _ in sorted_languages]
    
    def search_users(
        self,
        query: str,
        max_results: int = 100
    ) -> List[str]:
        """
        Search for GitHub users.
        
        Args:
            query: Search query (e.g., "location:san-francisco language:python")
            max_results: Maximum number of results
            
        Returns:
            List of usernames
        """
        usernames = []
        
        try:
            search_url = f"{self.API_BASE_URL}/search/users"
            response = self.fetch_url(
                search_url,
                params={"q": query, "per_page": min(max_results, 100)}
            )
            
            if response:
                results = response.json()
                usernames = [user["login"] for user in results.get("items", [])]
                logger.info(f"Found {len(usernames)} users matching query: {query}")
        
        except Exception as e:
            logger.error(f"Failed to search users: {str(e)}")
        
        return usernames
    
    def scrape(
        self,
        usernames: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        max_profiles: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple GitHub profiles.
        
        Args:
            usernames: List of GitHub usernames
            search_query: Search query to find users
            max_profiles: Maximum profiles to scrape
            
        Returns:
            List of scraped profiles
        """
        if not usernames and not search_query:
            logger.warning("No usernames or search query provided")
            return []
        
        # Get usernames from search if needed
        if not usernames and search_query:
            usernames = self.search_users(search_query, max_profiles)
        
        profiles = []
        
        for i, username in enumerate(usernames[:max_profiles]):
            logger.info(f"Scraping GitHub profile {i+1}/{min(len(usernames), max_profiles)}")
            
            profile = self.scrape_user_profile(username)
            if profile:
                profiles.append(profile)
        
        logger.info(f"Successfully scraped {len(profiles)} GitHub profiles")
        return profiles
    
    def export_profiles(self, output_file: str):
        """Export scraped profiles to JSON."""
        with open(output_file, 'w') as f:
            json.dump(self.profiles_scraped, f, indent=2)
        
        logger.info(f"Exported {len(self.profiles_scraped)} profiles to {output_file}")
