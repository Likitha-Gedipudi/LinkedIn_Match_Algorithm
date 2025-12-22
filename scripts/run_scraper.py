#!/usr/bin/env python3
"""
Script to run web scrapers and collect profile data.

Usage:
    python scripts/run_scraper.py --source linkedin --profiles 1000
    python scripts/run_scraper.py --source github --query "location:san-francisco language:python" --profiles 500
    python scripts/run_scraper.py --source synthetic --count 10000
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers import LinkedInScraper, GitHubScraper, SyntheticProfileGenerator
from src.utils import get_logger, get_config

logger = get_logger()


def run_linkedin_scraper(args):
    """Run LinkedIn scraper."""
    config = get_config()
    linkedin_config = config.scrapers.linkedin
    
    scraper = LinkedInScraper(
        rate_limit=linkedin_config.rate_limit,
        timeout=linkedin_config.timeout,
        max_retries=linkedin_config.retry_attempts,
        use_proxy=linkedin_config.use_proxy,
        proxy_list=linkedin_config.proxy_list,
        user_agents=linkedin_config.user_agents,
        delay_between_requests=linkedin_config.delay_between_requests,
    )
    
    # In production, you would load profile URLs from a source
    # For now, this requires manual input of profile URLs
    if args.profile_urls_file:
        with open(args.profile_urls_file, 'r') as f:
            profile_urls = [line.strip() for line in f if line.strip()]
    else:
        logger.error("LinkedIn scraper requires --profile-urls-file parameter")
        return None
    
    profiles = scraper.scrape(
        profile_urls=profile_urls,
        max_profiles=args.profiles
    )
    
    output_file = f"data/raw/linkedin_profiles_{len(profiles)}.json"
    scraper.export_profiles(output_file)
    
    scraper.close()
    return profiles


def run_github_scraper(args):
    """Run GitHub scraper."""
    config = get_config()
    github_config = config.scrapers.github
    
    if not github_config.api_token:
        logger.error("GitHub API token not configured. Set LINKEDIN_MATCH_SCRAPERS_GITHUB_API_TOKEN")
        return None
    
    scraper = GitHubScraper(
        api_token=github_config.api_token,
        rate_limit=github_config.rate_limit,
        timeout=github_config.timeout,
    )
    
    if args.usernames_file:
        with open(args.usernames_file, 'r') as f:
            usernames = [line.strip() for line in f if line.strip()]
        
        profiles = scraper.scrape(
            usernames=usernames,
            max_profiles=args.profiles
        )
    elif args.query:
        profiles = scraper.scrape(
            search_query=args.query,
            max_profiles=args.profiles
        )
    else:
        logger.error("GitHub scraper requires either --usernames-file or --query parameter")
        return None
    
    output_file = f"data/raw/github_profiles_{len(profiles)}.json"
    scraper.export_profiles(output_file)
    
    scraper.close()
    return profiles


def run_synthetic_generator(args):
    """Run synthetic profile generator."""
    config = get_config()
    synthetic_config = config.data.synthetic
    
    generator = SyntheticProfileGenerator(
        seed=synthetic_config.seed,
        quality_level=synthetic_config.quality_level
    )
    
    count = args.count or synthetic_config.generation_count
    profiles = generator.generate_batch(count)
    
    output_file = f"data/raw/synthetic_profiles_{len(profiles)}.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(profiles, f, indent=2)
    
    logger.info(f"Saved {len(profiles)} synthetic profiles to {output_file}")
    return profiles


def main():
    parser = argparse.ArgumentParser(description="Run web scrapers to collect profile data")
    
    parser.add_argument(
        "--source",
        required=True,
        choices=["linkedin", "github", "synthetic"],
        help="Data source to scrape"
    )
    
    parser.add_argument(
        "--profiles",
        type=int,
        default=100,
        help="Maximum number of profiles to scrape"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        help="Number of synthetic profiles to generate"
    )
    
    parser.add_argument(
        "--profile-urls-file",
        help="File containing LinkedIn profile URLs (one per line)"
    )
    
    parser.add_argument(
        "--usernames-file",
        help="File containing GitHub usernames (one per line)"
    )
    
    parser.add_argument(
        "--query",
        help="Search query for GitHub users"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting {args.source} scraper...")
    
    if args.source == "linkedin":
        profiles = run_linkedin_scraper(args)
    elif args.source == "github":
        profiles = run_github_scraper(args)
    elif args.source == "synthetic":
        profiles = run_synthetic_generator(args)
    else:
        logger.error(f"Unknown source: {args.source}")
        return
    
    if profiles:
        logger.info(f"Successfully collected {len(profiles)} profiles")
    else:
        logger.error("Failed to collect profiles")


if __name__ == "__main__":
    main()
