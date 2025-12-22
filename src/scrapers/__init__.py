"""Web scraping modules for LinkedIn professional data."""

from .base_scraper import BaseScraper
from .github_scraper import GitHubScraper
from .linkedin_scraper import LinkedInScraper
from .synthetic_generator import SyntheticProfileGenerator

__all__ = [
    "BaseScraper",
    "LinkedInScraper",
    "GitHubScraper",
    "SyntheticProfileGenerator",
]
