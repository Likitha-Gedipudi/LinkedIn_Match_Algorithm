"""
Red flags detection system for professional profiles.
Identifies connection collectors, job hoppers, ghost profiles, and spam.
"""

import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import re

from ..utils import get_logger

logger = get_logger()


class RedFlagsDetector:
    """
    Detect red flags in professional profiles that indicate low-value connections.
    
    Red flags include:
    - Connection collectors (many connections but low engagement)
    - Job hoppers (frequent job changes)
    - Ghost profiles (minimal information/activity)
    - Spam likelihood (MLM, recruiters, etc.)
    """
    
    def __init__(self, config: Dict = None):
        """Initialize detector with config."""
        self.config = config or {}
        
        # Thresholds for detection
        self.thresholds = {
            "connection_collector_min": 5000,
            "job_hopper_months": 6,
            "min_experience_entries": 2,
            "min_skills": 5,
            "ghost_profile_skill_threshold": 3,
        }
        
        # Spam keywords
        self.spam_keywords = [
            "mlm", "multi-level", "network marketing", "be your own boss",
            "financial freedom", "unlimited income", "work from home opportunity",
            "crypto trading", "forex signals", "insurance agent recruiting"
        ]
        
        # Generic/vague titles that indicate ghost profiles
        self.vague_titles = [
            "professional", "consultant", "freelancer", "entrepreneur",
            "expert", "specialist", "strategist", "advisor"
        ]
    
    def analyze_profile(self, profile: pd.Series) -> Dict[str, Any]:
        """
        Analyze a profile and return red flag scores.
        
        Args:
            profile: Profile data
            
        Returns:
            Dictionary with red flag scores and indicators
        """
        red_flags = {
            "is_connection_collector": self._is_connection_collector(profile),
            "is_job_hopper": self._is_job_hopper(profile),
            "is_ghost_profile": self._is_ghost_profile(profile),
            "engagement_quality_score": self._calculate_engagement_quality(profile),
            "spam_likelihood": self._calculate_spam_likelihood(profile),
        }
        
        # Calculate overall red flag score
        red_flags["red_flag_score"] = self._calculate_overall_red_flag_score(red_flags)
        
        # Add explanation
        red_flags["red_flag_reasons"] = self._generate_red_flag_explanation(red_flags, profile)
        
        return red_flags
    
    def _is_connection_collector(self, profile: pd.Series) -> bool:
        """
        Detect connection collectors (many connections, low value).
        
        Signs:
        - 5000+ connections
        - Generic title
        - Low engagement quality
        """
        connections = profile.get("connections", 0)
        
        if connections < self.thresholds["connection_collector_min"]:
            return False
        
        # High connections alone isn't enough - check for other signs
        title = (profile.get("current_role") or "").lower()
        is_generic = any(vague in title for vague in self.vague_titles)
        
        return connections >= self.thresholds["connection_collector_min"] and is_generic
    
    def _is_job_hopper(self, profile: pd.Series) -> bool:
        """
        Detect job hoppers (frequent job changes).
        
        Signs:
        - 3+ jobs in last 2 years
        - Average tenure < 6 months
        """
        experience = profile.get("experience", [])
        
        if not experience or len(experience) < 3:
            return False
        
        # Calculate average tenure
        if isinstance(experience, list) and len(experience) >= 3:
            # Count jobs in recent years
            recent_jobs = 0
            for job in experience[:5]:  # Look at 5 most recent jobs
                if isinstance(job, dict):
                    # Check if duration is short
                    duration_months = job.get("duration_months", 12)
                    if duration_months < self.thresholds["job_hopper_months"]:
                        recent_jobs += 1
            
            return recent_jobs >= 3
        
        return False
    
    def _is_ghost_profile(self, profile: pd.Series) -> bool:
        """
        Detect ghost profiles (minimal information).
        
        Signs:
        - Few skills (< 3)
        - Vague title
        - No about section or very short
        - Minimal experience entries
        """
        skills = profile.get("skills", [])
        title = (profile.get("current_role") or "").lower()
        about = profile.get("about", "")
        experience = profile.get("experience", [])
        
        # Count ghost indicators
        ghost_signals = 0
        
        if len(skills) < self.thresholds["ghost_profile_skill_threshold"]:
            ghost_signals += 1
        
        if any(vague in title for vague in self.vague_titles) and len(title.split()) <= 2:
            ghost_signals += 1
        
        if len(about) < 50:
            ghost_signals += 1
        
        if len(experience) < self.thresholds["min_experience_entries"]:
            ghost_signals += 1
        
        return ghost_signals >= 3
    
    def _calculate_engagement_quality(self, profile: pd.Series) -> float:
        """
        Calculate engagement quality score (0-100).
        
        Higher score = more authentic, active profile
        Lower score = low engagement or fake
        """
        score = 50.0  # Start neutral
        
        # Skills count (good signal)
        skills = profile.get("skills", [])
        if len(skills) >= 15:
            score += 15
        elif len(skills) >= 10:
            score += 10
        elif len(skills) < 5:
            score -= 15
        
        # Experience detail (good signal)
        experience = profile.get("experience", [])
        if len(experience) >= 4:
            score += 15
        elif len(experience) <= 1:
            score -= 15
        
        # About section (good signal)
        about = profile.get("about", "")
        if len(about) > 200:
            score += 10
        elif len(about) < 50:
            score -= 10
        
        # Education (good signal)
        education = profile.get("education", [])
        if len(education) >= 1:
            score += 10
        
        # Connection count (moderate is good)
        connections = profile.get("connections", 0)
        if 500 <= connections <= 3000:
            score += 10  # Sweet spot
        elif connections > 5000:
            score -= 10  # Possible collector
        elif connections < 50:
            score -= 10  # Very new or inactive
        
        return max(0, min(100, score))
    
    def _calculate_spam_likelihood(self, profile: pd.Series) -> float:
        """
        Calculate spam/scam likelihood (0-100).
        
        Higher score = more likely spam
        """
        score = 0.0
        
        # Check headline for spam keywords
        headline = (profile.get("headline") or "").lower()
        about = (profile.get("about") or "").lower()
        title = (profile.get("current_role") or "").lower()
        
        combined_text = f"{headline} {about} {title}"
        
        # Count spam keywords
        spam_count = sum(1 for keyword in self.spam_keywords if keyword in combined_text)
        score += spam_count * 20
        
        # Check for suspicious patterns
        if "dm me" in combined_text or "message me" in combined_text:
            score += 15
        
        if "opportunity" in combined_text and "financial" in combined_text:
            score += 20
        
        # Check title
        if "recruiter" in title and "insurance" in combined_text:
            score += 15
        
        # Very high connection count + generic title = recruiter/spam
        connections = profile.get("connections", 0)
        if connections > 8000 and any(vague in title for vague in self.vague_titles):
            score += 25
        
        return min(100, score)
    
    def _calculate_overall_red_flag_score(self, red_flags: Dict[str, Any]) -> float:
        """
        Calculate overall red flag score (0-100).
        
        Higher score = more red flags
        """
        score = 0.0
        
        # Boolean flags
        if red_flags.get("is_connection_collector"):
            score += 25
        
        if red_flags.get("is_job_hopper"):
            score += 20
        
        if red_flags.get("is_ghost_profile"):
            score += 30
        
        # Engagement quality (inverse)
        engagement = red_flags.get("engagement_quality_score", 50)
        score += (100 - engagement) * 0.15
        
        # Spam likelihood
        spam = red_flags.get("spam_likelihood", 0)
        score += spam * 0.20
        
        return min(100, score)
    
    def _generate_red_flag_explanation(self, red_flags: Dict[str, Any], profile: pd.Series) -> str:
        """Generate human-readable explanation of red flags."""
        reasons = []
        
        if red_flags.get("is_connection_collector"):
            connections = profile.get("connections", 0)
            reasons.append(f"Connection collector ({connections:,} connections with generic title)")
        
        if red_flags.get("is_job_hopper"):
            reasons.append("Job hopper (3+ jobs in short period)")
        
        if red_flags.get("is_ghost_profile"):
            reasons.append("Ghost profile (minimal information and activity)")
        
        engagement = red_flags.get("engagement_quality_score", 50)
        if engagement < 40:
            reasons.append(f"Low engagement quality ({engagement:.0f}/100)")
        
        spam = red_flags.get("spam_likelihood", 0)
        if spam > 30:
            reasons.append(f"Possible spam/MLM ({spam:.0f}% likelihood)")
        
        if not reasons:
            return "No significant red flags"
        
        return " | ".join(reasons)
    
    def batch_analyze(self, profiles_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze multiple profiles and add red flag columns.
        
        Args:
            profiles_df: DataFrame of profiles
            
        Returns:
            DataFrame with added red flag columns
        """
        logger.info(f"Analyzing {len(profiles_df)} profiles for red flags...")
        
        # Analyze each profile
        red_flag_data = []
        for idx, profile in profiles_df.iterrows():
            red_flags = self.analyze_profile(profile)
            red_flag_data.append(red_flags)
        
        # Convert to DataFrame
        red_flags_df = pd.DataFrame(red_flag_data)
        
        # Combine with original profiles
        result_df = pd.concat([profiles_df.reset_index(drop=True), red_flags_df], axis=1)
        
        logger.info(f"Red flag analysis complete. {red_flags_df['is_connection_collector'].sum()} collectors, "
                   f"{red_flags_df['is_job_hopper'].sum()} job hoppers, "
                   f"{red_flags_df['is_ghost_profile'].sum()} ghost profiles detected.")
        
        return result_df


def analyze_profiles_for_red_flags(profiles_df: pd.DataFrame, config: Dict = None) -> pd.DataFrame:
    """
    Convenience function to analyze profiles for red flags.
    
    Args:
        profiles_df: DataFrame of profiles
        config: Optional configuration
        
    Returns:
        DataFrame with red flag columns added
    """
    detector = RedFlagsDetector(config)
    return detector.batch_analyze(profiles_df)
