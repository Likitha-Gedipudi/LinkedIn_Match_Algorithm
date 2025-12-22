"""
LinkedIn profile scraper - PUBLIC DATA ONLY.
Respects LinkedIn TOS and only scrapes publicly accessible information.

IMPORTANT: This scraper ONLY accesses public profiles without authentication.
It respects rate limits and robots.txt directives.
"""

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from .base_scraper import BaseScraper
from ..utils import generate_id, sanitize_string, get_logger

logger = get_logger()


class LinkedInScraper(BaseScraper):
    """
    Scraper for public LinkedIn profiles.
    
    Ethical Guidelines:
    - Only scrapes PUBLIC profile data
    - No authentication/login required
    - Respects robots.txt
    - Conservative rate limiting
    - User consent assumed for public profiles
    """
    
    BASE_URL = "https://www.linkedin.com"
    
    def __init__(self, **kwargs):
        """Initialize LinkedIn scraper with conservative defaults."""
        # Override with conservative defaults for LinkedIn
        kwargs.setdefault("rate_limit", 5)  # Very conservative
        kwargs.setdefault("delay_between_requests", 3)
        kwargs.setdefault("respect_robots_txt", True)
        
        super().__init__(**kwargs)
        self.profiles_scraped = []
    
    def scrape_profile_from_public_url(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a public LinkedIn profile.
        
        Args:
            profile_url: Public LinkedIn profile URL
            
        Returns:
            Profile data dictionary or None
        """
        try:
            response = self.fetch_url(profile_url)
            if not response:
                return None
            
            soup = self.parse_html(response.text)
            profile_data = self._extract_profile_data(soup, profile_url)
            
            if profile_data:
                profile_data["profile_id"] = generate_id(profile_url)
                profile_data["source_url"] = profile_url
                self.profiles_scraped.append(profile_data)
                
                logger.info(f"Successfully scraped profile: {profile_url}")
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Failed to scrape profile {profile_url}: {str(e)}")
            return None
    
    def _extract_profile_data(self, soup, url: str) -> Dict[str, Any]:
        """
        Extract profile data from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            url: Profile URL
            
        Returns:
            Extracted profile data
        """
        profile = {
            "name": self._extract_name(soup),
            "headline": self._extract_headline(soup),
            "location": self._extract_location(soup),
            "about": self._extract_about(soup),
            "experience": self._extract_experience(soup),
            "education": self._extract_education(soup),
            "skills": self._extract_skills(soup),
            "connections": self._extract_connections(soup),
        }
        
        # Filter out None values
        return {k: v for k, v in profile.items() if v is not None}
    
    def _extract_name(self, soup) -> Optional[str]:
        """Extract profile name."""
        # Multiple selectors for robustness
        selectors = [
            "h1.text-heading-xlarge",
            "h1.top-card-layout__title",
            ".pv-text-details__left-panel h1",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return sanitize_string(element.get_text())
        
        return None
    
    def _extract_headline(self, soup) -> Optional[str]:
        """Extract profile headline/title."""
        selectors = [
            ".text-body-medium",
            ".top-card-layout__headline",
            ".pv-text-details__left-panel .text-body-medium",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return sanitize_string(element.get_text())
        
        return None
    
    def _extract_location(self, soup) -> Optional[str]:
        """Extract location."""
        selectors = [
            ".text-body-small.inline.t-black--light.break-words",
            ".top-card__subline-item",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = sanitize_string(element.get_text())
                if text and len(text) > 2:
                    return text
        
        return None
    
    def _extract_about(self, soup) -> Optional[str]:
        """Extract about/summary section."""
        selectors = [
            "#about ~ * .inline-show-more-text",
            ".pv-about__summary-text",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return sanitize_string(element.get_text())
        
        return None
    
    def _extract_experience(self, soup) -> List[Dict[str, Any]]:
        """Extract work experience."""
        experience_list = []
        
        # Look for experience section
        exp_section = soup.find(id="experience")
        if not exp_section:
            return experience_list
        
        # Find experience items
        exp_items = exp_section.find_all("li", class_=re.compile("pvs-list__paged-list-item"))
        
        for item in exp_items:
            exp_data = {
                "title": None,
                "company": None,
                "duration": None,
                "description": None,
            }
            
            # Extract title
            title_elem = item.select_one(".t-bold span")
            if title_elem:
                exp_data["title"] = sanitize_string(title_elem.get_text())
            
            # Extract company
            company_elem = item.select_one(".t-14.t-normal span")
            if company_elem:
                exp_data["company"] = sanitize_string(company_elem.get_text())
            
            # Extract duration
            duration_elem = item.select_one(".t-black--light span")
            if duration_elem:
                exp_data["duration"] = sanitize_string(duration_elem.get_text())
            
            if exp_data["title"] or exp_data["company"]:
                experience_list.append(exp_data)
        
        return experience_list
    
    def _extract_education(self, soup) -> List[Dict[str, Any]]:
        """Extract education history."""
        education_list = []
        
        edu_section = soup.find(id="education")
        if not edu_section:
            return education_list
        
        edu_items = edu_section.find_all("li", class_=re.compile("pvs-list__paged-list-item"))
        
        for item in edu_items:
            edu_data = {
                "school": None,
                "degree": None,
                "field": None,
                "years": None,
            }
            
            # Extract school name
            school_elem = item.select_one(".t-bold span")
            if school_elem:
                edu_data["school"] = sanitize_string(school_elem.get_text())
            
            # Extract degree
            degree_elem = item.select_one(".t-14.t-normal span")
            if degree_elem:
                edu_data["degree"] = sanitize_string(degree_elem.get_text())
            
            if edu_data["school"]:
                education_list.append(edu_data)
        
        return education_list
    
    def _extract_skills(self, soup) -> List[str]:
        """Extract skills list."""
        skills = []
        
        skills_section = soup.find(id="skills")
        if not skills_section:
            return skills
        
        skill_items = skills_section.find_all("li", class_=re.compile("pvs-list__paged-list-item"))
        
        for item in skill_items:
            skill_elem = item.select_one(".t-bold span")
            if skill_elem:
                skill = sanitize_string(skill_elem.get_text())
                if skill:
                    skills.append(skill)
        
        return skills
    
    def _extract_connections(self, soup) -> Optional[int]:
        """Extract number of connections (approximation from public data)."""
        # Look for connection count in various places
        connection_text_patterns = [
            r'(\d+)\+?\s*connections?',
            r'(\d+)\s*followers?',
        ]
        
        text_content = soup.get_text()
        
        for pattern in connection_text_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass
        
        return None
    
    def scrape(
        self,
        profile_urls: Optional[List[str]] = None,
        max_profiles: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple LinkedIn profiles.
        
        Args:
            profile_urls: List of public profile URLs
            max_profiles: Maximum number of profiles to scrape
            
        Returns:
            List of scraped profiles
        """
        if not profile_urls:
            logger.warning("No profile URLs provided to scrape")
            return []
        
        profiles = []
        
        for i, url in enumerate(profile_urls[:max_profiles]):
            logger.info(f"Scraping profile {i+1}/{min(len(profile_urls), max_profiles)}")
            
            profile_data = self.scrape_profile_from_public_url(url)
            if profile_data:
                profiles.append(profile_data)
        
        logger.info(f"Successfully scraped {len(profiles)} profiles")
        return profiles
    
    def export_profiles(self, output_file: str):
        """
        Export scraped profiles to JSON file.
        
        Args:
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(self.profiles_scraped, f, indent=2)
        
        logger.info(f"Exported {len(self.profiles_scraped)} profiles to {output_file}")
