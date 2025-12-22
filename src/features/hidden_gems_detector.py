"""
Hidden gems detection system for professional profiles.
Identifies undervalued profiles with high potential for valuable connections.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Set
from collections import Counter

from ..utils import get_logger

logger = get_logger()


class HiddenGemsDetector:
    """
    Identify hidden gem profiles - undervalued professionals with high potential.
    
    Hidden gems are profiles that:
    - Have valuable skills but small networks
    - Show rapid career growth trajectory
    - Are super-connectors in niche areas
    - Have rare, in-demand skills
    """
    
    def __init__(self, config: Dict = None, all_profiles: pd.DataFrame = None):
        """
        Initialize detector with config and dataset context.
        
        Args:
            config: Optional configuration
            all_profiles: Full dataset of profiles for skill rarity calculation
        """
        self.config = config or {}
        self.all_profiles = all_profiles
        
        # Calculate skill rarity if we have the full dataset
        self.skill_rarity_map = {}
        if all_profiles is not None:
            self._calculate_skill_rarity(all_profiles)
        
        # Define high-value skills (in-demand)
        self.high_value_skills = {
            "Machine Learning", "Deep Learning", "AI", "Data Science",
            "Python", "Cloud Architecture", "Kubernetes", "AWS",
            "Product Management", "Fundraising", "Growth Marketing",
            "UI/UX Design", "React", "TypeScript", "Go", "Rust"
        }
    
    def _calculate_skill_rarity(self, profiles_df: pd.DataFrame):
        """Calculate skill rarity across all profiles."""
        logger.info("Calculating skill rarity scores...")
        
        all_skills = []
        for skills in profiles_df.get("skills", []):
            if isinstance(skills, list):
                all_skills.extend(skills)
        
        total_profiles = len(profiles_df)
        skill_counts = Counter(all_skills)
        
        # Rarity score: inverse of frequency (0-100)
        for skill, count in skill_counts.items():
            frequency = count / total_profiles
            # Rare skills (< 5% of profiles) get high scores
            if frequency < 0.05:
                self.skill_rarity_map[skill] = 90 + (0.05 - frequency) * 200
            elif frequency < 0.15:
                self.skill_rarity_map[skill] = 70 + (0.15 - frequency) * 100
            elif frequency < 0.30:
                self.skill_rarity_map[skill] = 40 + (0.30 - frequency) * 100
            else:
                self.skill_rarity_map[skill] = max(10, 40 - frequency * 50)
        
        logger.info(f"Calculated rarity for {len(self.skill_rarity_map)} unique skills")
    
    def analyze_profile(self, profile: pd.Series) -> Dict[str, Any]:
        """
        Analyze a profile and return hidden gem scores.
        
        Args:
            profile: Profile data
            
        Returns:
            Dictionary with gem scores and indicators
        """
        gem_features = {
            "undervalued_score": self._calculate_undervalued_score(profile),
            "rising_star_score": self._calculate_rising_star_score(profile),
            "super_connector_score": self._calculate_super_connector_score(profile),
            "skill_rarity_score": self._calculate_skill_rarity_score(profile),
        }
        
        # Calculate overall gem score
        gem_features["gem_score"] = self._calculate_overall_gem_score(gem_features)
        
        # Add explanation
        gem_features["gem_reason"] = self._generate_gem_explanation(gem_features, profile)
        
        # Categorize gem type
        gem_features["gem_type"] = self._categorize_gem_type(gem_features)
        
        return gem_features
    
    def _calculate_undervalued_score(self, profile: pd.Series) -> float:
        """
        Calculate how undervalued a profile is (0-100).
        
        High score = great skills/experience but small network
        """
        score = 0.0
        
        # Check experience vs. connections
        years_exp = profile.get("years_experience", 0)
        connections = profile.get("connections", 0)
        
        # Expected connections based on experience
        expected_connections = years_exp * 100  # Rough heuristic
        
        if connections < expected_connections * 0.3 and years_exp >= 3:
            # Much fewer connections than expected
            score += 40
        elif connections < expected_connections * 0.5 and years_exp >= 2:
            score += 25
        
        # High-quality profile with low visibility
        skills_count = len(profile.get("skills", []))
        if skills_count >= 12 and connections < 500:
            score += 30
        
        # Good education but small network
        education = profile.get("education", [])
        if len(education) >= 1 and connections < 300:
            score += 15
        
        # Senior level but not widely connected
        seniority = profile.get("seniority_level", "mid")
        if seniority in ["senior", "executive"] and connections < 1000:
            score += 15
        
        return min(100, score)
    
    def _calculate_rising_star_score(self, profile: pd.Series) -> float:
        """
        Calculate rising star indicator (rapid career growth).
        
        Signs:
        - Junior to mid/senior transition
        - Fast promotions
        - High-quality skills for experience level
        """
        score = 0.0
        
        years_exp = profile.get("years_experience", 0)
        seniority = profile.get("seniority_level", "mid")
        skills_count = len(profile.get("skills", []))
        
        # Fast progression (senior level with low experience)
        if seniority == "senior" and 5 <= years_exp <= 8:
            score += 40  # Fast track to senior
        elif seniority == "executive" and 10 <= years_exp <= 15:
            score += 50  # Very fast to executive
        
        # Many skills for experience level
        expected_skills = 5 + (years_exp * 1.5)
        if skills_count > expected_skills * 1.5:
            score += 30
        
        # Working at top company early in career
        company = profile.get("current_company", "")
        top_companies = ["Google", "Microsoft", "Amazon", "Meta", "Apple", 
                        "Netflix", "Tesla", "Uber", "Airbnb", "Stripe"]
        if any(top in company for top in top_companies) and years_exp < 5:
            score += 30
        
        return min(100, score)
    
    def _calculate_super_connector_score(self, profile: pd.Series) -> float:
        """
        Calculate super-connector score (well-connected in specific niche).
        
        High connections + specialized skills = valuable network access
        """
        score = 0.0
        
        connections = profile.get("connections", 0)
        skills = set(profile.get("skills", []))
        industry = profile.get("industry", "")
        
        # Good connection count (not too high to be spam)
        if 1000 <= connections <= 4000:
            score += 40
        elif 500 <= connections <= 1000:
            score += 25
        
        # Specialized in specific domain
        specialized_domains = [
            {"Machine Learning", "Deep Learning", "AI"},
            {"Product Management", "Strategy", "Growth"},
            {"Fundraising", "VC", "Investment"},
            {"Design", "UI/UX Design", "Figma"},
        ]
        
        for domain in specialized_domains:
            if len(skills.intersection(domain)) >= 2:
                score += 30
                break
        
        # Senior level = more valuable network
        seniority = profile.get("seniority_level", "mid")
        if seniority == "executive":
            score += 20
        elif seniority == "senior":
            score += 10
        
        # Specific valuable industries
        valuable_industries = ["Technology", "Finance", "Consulting"]
        if any(ind in industry for ind in valuable_industries):
            score += 10
        
        return min(100, score)
    
    def _calculate_skill_rarity_score(self, profile: pd.Series) -> float:
        """
        Calculate skill rarity score based on dataset.
        
        Profiles with rare, in-demand skills are gems.
        """
        if not self.skill_rarity_map:
            # Fallback if no dataset provided
            return self._calculate_skill_rarity_fallback(profile)
        
        skills = profile.get("skills", [])
        if not skills:
            return 0.0
        
        # Calculate average rarity of profile's skills
        rarity_scores = [self.skill_rarity_map.get(skill, 30) for skill in skills]
        avg_rarity = np.mean(rarity_scores) if rarity_scores else 0
        
        # Bonus for having multiple rare skills
        rare_skills = [s for s in skills if self.skill_rarity_map.get(s, 0) > 70]
        if len(rare_skills) >= 3:
            avg_rarity = min(100, avg_rarity * 1.3)
        elif len(rare_skills) >= 2:
            avg_rarity = min(100, avg_rarity * 1.2)
        
        return avg_rarity
    
    def _calculate_skill_rarity_fallback(self, profile: pd.Series) -> float:
        """Fallback skill rarity calculation without dataset."""
        skills = set(profile.get("skills", []))
        
        # Check for high-value skills
        valuable_skills = skills.intersection(self.high_value_skills)
        
        if len(valuable_skills) >= 4:
            return 80
        elif len(valuable_skills) >= 2:
            return 60
        elif len(valuable_skills) >= 1:
            return 40
        
        return 20
    
    def _calculate_overall_gem_score(self, gem_features: Dict[str, Any]) -> float:
        """
        Calculate overall hidden gem score (0-100).
        
        Weighted combination of gem indicators.
        """
        weights = {
            "undervalued_score": 0.30,
            "rising_star_score": 0.25,
            "super_connector_score": 0.25,
            "skill_rarity_score": 0.20,
        }
        
        score = sum(
            gem_features.get(key, 0) * weight
            for key, weight in weights.items()
        )
        
        return min(100, score)
    
    def _categorize_gem_type(self, gem_features: Dict[str, Any]) -> str:
        """Categorize the type of hidden gem."""
        scores = {
            "undervalued": gem_features.get("undervalued_score", 0),
            "rising_star": gem_features.get("rising_star_score", 0),
            "super_connector": gem_features.get("super_connector_score", 0),
            "rare_skills": gem_features.get("skill_rarity_score", 0),
        }
        
        # Find dominant characteristic
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        if max_score < 40:
            return "none"
        
        return max_type.replace("_", " ").title()
    
    def _generate_gem_explanation(self, gem_features: Dict[str, Any], profile: pd.Series) -> str:
        """Generate human-readable explanation of why this is a gem."""
        reasons = []
        
        undervalued = gem_features.get("undervalued_score", 0)
        if undervalued > 50:
            years_exp = profile.get("years_experience", 0)
            connections = profile.get("connections", 0)
            reasons.append(f"Undervalued: {years_exp} years experience but only {connections} connections")
        
        rising_star = gem_features.get("rising_star_score", 0)
        if rising_star > 50:
            seniority = profile.get("seniority_level", "mid")
            years_exp = profile.get("years_experience", 0)
            reasons.append(f"Rising star: {seniority} level at {years_exp} years")
        
        super_connector = gem_features.get("super_connector_score", 0)
        if super_connector > 50:
            connections = profile.get("connections", 0)
            industry = profile.get("industry", "")
            reasons.append(f"Super connector: {connections:,} connections in {industry}")
        
        skill_rarity = gem_features.get("skill_rarity_score", 0)
        if skill_rarity > 60:
            reasons.append(f"Rare skills: has in-demand, uncommon expertise")
        
        if not reasons:
            return "Not a significant hidden gem"
        
        return " | ".join(reasons)
    
    def batch_analyze(self, profiles_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze multiple profiles and add gem columns.
        
        Args:
            profiles_df: DataFrame of profiles
            
        Returns:
            DataFrame with added gem columns
        """
        logger.info(f"Analyzing {len(profiles_df)} profiles for hidden gems...")
        
        # If we don't have skill rarity yet, calculate it
        if not self.skill_rarity_map:
            self._calculate_skill_rarity(profiles_df)
        
        # Analyze each profile
        gem_data = []
        for idx, profile in profiles_df.iterrows():
            gems = self.analyze_profile(profile)
            gem_data.append(gems)
        
        # Convert to DataFrame
        gems_df = pd.DataFrame(gem_data)
        
        # Combine with original profiles
        result_df = pd.concat([profiles_df.reset_index(drop=True), gems_df], axis=1)
        
        # Log statistics
        high_gems = (gems_df["gem_score"] > 70).sum()
        logger.info(f"Hidden gems analysis complete. {high_gems} high-potential profiles found (gem_score > 70)")
        
        return result_df


def analyze_profiles_for_gems(profiles_df: pd.DataFrame, config: Dict = None) -> pd.DataFrame:
    """
    Convenience function to analyze profiles for hidden gems.
    
    Args:
        profiles_df: DataFrame of profiles
        config: Optional configuration
        
    Returns:
        DataFrame with gem columns added
    """
    detector = HiddenGemsDetector(config, all_profiles=profiles_df)
    return detector.batch_analyze(profiles_df)
