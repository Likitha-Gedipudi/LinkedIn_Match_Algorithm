"""
Base scraper class with common functionality for all scrapers.
Includes rate limiting, error handling, proxy rotation, and retry logic.
"""

import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib3.util.retry import Retry

from ..utils import get_logger, get_random_user_agent

logger = get_logger()


class BaseScraper(ABC):
    """
    Base class for all web scrapers with common functionality.
    
    Features:
    - Rate limiting
    - Proxy rotation
    - User agent rotation
    - Automatic retries
    - Error handling
    - Respect for robots.txt
    """
    
    def __init__(
        self,
        rate_limit: int = 10,
        timeout: int = 30,
        max_retries: int = 3,
        use_proxy: bool = False,
        proxy_list: Optional[List[str]] = None,
        user_agents: Optional[List[str]] = None,
        delay_between_requests: int = 2,
        respect_robots_txt: bool = True,
    ):
        """
        Initialize base scraper.
        
        Args:
            rate_limit: Requests per minute
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            use_proxy: Whether to use proxy rotation
            proxy_list: List of proxy URLs
            user_agents: List of user agent strings
            delay_between_requests: Delay between requests in seconds
            respect_robots_txt: Whether to respect robots.txt
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.user_agents = user_agents or []
        self.delay_between_requests = delay_between_requests
        self.respect_robots_txt = respect_robots_txt
        
        self.session = self._create_session()
        self.last_request_time = 0
        self.request_count = 0
        
        logger.info(f"Initialized {self.__class__.__name__} scraper")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry configuration."""
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent."""
        user_agent = (
            random.choice(self.user_agents)
            if self.user_agents
            else get_random_user_agent()
        )
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get random proxy from proxy list."""
        if not self.use_proxy or not self.proxy_list:
            return None
        
        proxy_url = random.choice(self.proxy_list)
        return {
            "http": proxy_url,
            "https": proxy_url,
        }
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.rate_limit > 0:
            min_interval = 60.0 / self.rate_limit  # Convert to seconds
            elapsed = time.time() - self.last_request_time
            
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        
        # Additional delay between requests
        if self.delay_between_requests > 0:
            time.sleep(self.delay_between_requests)
        
        self.last_request_time = time.time()
    
    def _can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        if not self.respect_robots_txt:
            return True
        
        # Simple implementation - in production, use urllib.robotparser
        # For now, allow all requests
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_url(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[requests.Response]:
        """
        Fetch URL with rate limiting and error handling.
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            params: URL parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            Response object or None if failed
        """
        # Check robots.txt
        if not self._can_fetch(url):
            logger.warning(f"URL blocked by robots.txt: {url}")
            return None
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        proxy = self._get_proxy()
        
        try:
            logger.debug(f"Fetching: {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=request_headers,
                proxies=proxy,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            self.request_count += 1
            
            logger.debug(f"Successfully fetched: {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            raise
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.
        
        Args:
            html_content: Raw HTML string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    @abstractmethod
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Main scraping method to be implemented by subclasses.
        
        Returns:
            List of scraped data dictionaries
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraper statistics.
        
        Returns:
            Dictionary with scraper stats
        """
        return {
            "scraper": self.__class__.__name__,
            "total_requests": self.request_count,
            "rate_limit": self.rate_limit,
            "using_proxy": self.use_proxy,
        }
    
    def close(self):
        """Close scraper and cleanup resources."""
        self.session.close()
        logger.info(f"Closed {self.__class__.__name__} scraper")
