"""
Compatibility feature engineering.
Calculates mutual benefit scores between profile pairs.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

from ..utils import calculate_similarity, safe_divide, get_logger

logger = get_logger()


class CompatibilityFeatureEngine:
    """
    Calculate compatibility features between profile pairs.
    
    Features include:
    - Skill complementarity
    - Network value
    - Career alignment
    - Geographic proximity
    """
    
    def __init__(self, config: Dict = None):
        """Initialize feature engine with config."""
        self.config = config or {}
        self.feature_weights = {
            "skill_complementarity": self.config.get("skill_weight", 0.40),
            "network_value": self.config.get("network_weight", 0.30),
            "career_alignment": self.config.get("career_weight", 0.20),
            "geographic_proximity": self.config.get("geographic_weight", 0.10),
        }
    
    def calculate_features(
        self,
        profile_a: pd.Series,
        profile_b: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate all compatibility features for a profile pair.
        
        Args:
            profile_a: First profile
            profile_b: Second profile
            
        Returns:
            Dictionary of feature scores
        """
        features = {
            "skill_match_score": self._calculate_skill_match(profile_a, profile_b),
            "skill_complementarity_score": self._calculate_skill_complementarity(profile_a, profile_b),
            "network_value_a_to_b": self._calculate_network_value(profile_a, profile_b),
            "network_value_b_to_a": self._calculate_network_value(profile_b, profile_a),
            "career_alignment_score": self._calculate_career_alignment(profile_a, profile_b),
            "experience_gap": self._calculate_experience_gap(profile_a, profile_b),
            "industry_match": self._calculate_industry_match(profile_a, profile_b),
            "geographic_score": self._calculate_geographic_score(profile_a, profile_b),
            "seniority_match": self._calculate_seniority_match(profile_a, profile_b),
        }
        
        # Calculate overall compatibility
        features["compatibility_score"] = self._calculate_overall_compatibility(features)
        
        # Add ROI predictors
        features["predicted_job_opportunity_score"] = self._predict_job_opportunity(profile_a, profile_b, features)
        features["predicted_mentorship_value"] = self._predict_mentorship_value(profile_a, profile_b, features)
        features["predicted_collaboration_potential"] = self._predict_collaboration(profile_a, profile_b, features)
        features["roi_timeframe"] = self._estimate_roi_timeframe(features)
        
        # Add explanations
        features["mutual_benefit_explanation"] = self._generate_explanation(profile_a, profile_b, features)
        
        return features
    
    def _calculate_skill_match(self, profile_a: pd.Series, profile_b: pd.Series) -> float:
        """Calculate skill overlap/similarity."""
        skills_a = set(profile_a.get("skills", []))
        skills_b = set(profile_b.get("skills", []))
        
        if not skills_a or not skills_b:
            return 0.0
        
        # Jaccard similarity
        intersection = len(skills_a.intersection(skills_b))
        union = len(skills_a.union(skills_b))
        
        return safe_divide(intersection * 100, union, 0.0)
    
    def _calculate_skill_complementarity(self, profile_a: pd.Series, profile_b: pd.Series) -> float:
        """Calculate how well skills complement each other."""
        needs_a = set(profile_a.get("needs", []))
        can_offer_b = set(profile_b.get("can_offer", []))
        
        needs_b = set(profile_b.get("needs", []))
        can_offer_a = set(profile_a.get("can_offer", []))
        
        # How many of A's needs can B fulfill?
        a_needs_met = len(needs_a.intersection(can_offer_b)) if needs_a else 0
        b_needs_met = len(needs_b.intersection(can_offer_a)) if needs_b else 0
        
        total_needs = len(needs_a) + len(needs_b)
        total_met = a_needs_met + b_needs_met
        
        return safe_divide(total_met * 100, total_needs, 0.0)
    
    def _calculate_network_value(self, profile_from: pd.Series, profile_to: pd.Series) -> float:
        """Calculate network value one profile provides to another."""
        # Based on connections, industry, seniority
        connections_from = profile_from.get("connections", 0)
        
        # More connections = more network value
        connection_score = min(connections_from / 1000 * 50, 50)  # Cap at 50
        
        # Same industry adds value
        industry_match = self._calculate_industry_match(profile_from, profile_to)
        industry_bonus = industry_match * 0.3
        
        # Senior people have more valuable networks
        seniority_from = profile_from.get("seniority_level", "mid")
        seniority_bonus = {
            "entry": 0,
            "mid": 10,
            "senior": 20,
            "executive": 30
        }.get(seniority_from, 10)
        
        return min(connection_score + industry_bonus + seniority_bonus, 100)
    
    def _calculate_career_alignment(self, profile_a: pd.Series, profile_b: pd.Series) -> float:
        """Calculate career stage alignment for mutual benefit."""
        years_a = profile_a.get("years_experience", 0)
        years_b = profile_b.get("years_experience", 0)
        
        experience_gap = abs(years_a - years_b)
        
        # Ideal mentor-mentee gap: 3-7 years
        if 3 <= experience_gap <= 7:
            return 90.0
        # Peer relationship: 0-2 years difference
        elif experience_gap <= 2:
            return 80.0
        # Large gap but still valuable
        elif experience_gap <= 15:
            return 60.0
        else:
            return 40.0
    
    def _calculate_experience_gap(self, profile_a: pd.Series, profile_b: pd.Series) -> int:
        """Calculate years of experience gap."""
        years_a = profile_a.get("years_experience", 0)
        years_b = profile_b.get("years_experience", 0)
        return abs(years_a - years_b)
    
    def _calculate_industry_match(self, profile_a: pd.Series, profile_b: pd.Series) -> float:
        """Calculate industry similarity."""
        industry_a = (profile_a.get("industry") or "").lower()
        industry_b = (profile_b.get("industry") or "").lower()
        
        if not industry_a or not industry_b:
            return 0.0
        
        # Exact match
        if industry_a == industry_b:
            return 100.0
        
        # Partial match (word overlap)
        similarity = calculate_similarity(industry_a, industry_b)
        return similarity * 100
    
    def _calculate_geographic_score(self, profile_a: pd.Series, profile_b: pd.Series) -> float:
        """Calculate geographic proximity score."""
        loc_a = (profile_a.get("location") or "").lower()
        loc_b = (profile_b.get("location") or "").lower()
        
        if not loc_a or not loc_b:
            return 50.0  # Neutral score
        
        # Same city
        if loc_a == loc_b:
            return 100.0
        
        # Same state/region (rough check)
        if any(word in loc_b for word in loc_a.split(",")[-1].split()):
            return 75.0
        
        # Different locations
        remote_pref_a = profile_a.get("remote_preference")
        remote_pref_b = profile_b.get("remote_preference")
        
        if remote_pref_a == "remote" or remote_pref_b == "remote":
            return 60.0  # Distance matters less
        
        return 30.0
    
    def _calculate_seniority_match(self, profile_a: pd.Series, profile_b: pd.Series) -> float:
        """Calculate seniority level compatibility."""
        seniority_levels = ["entry", "mid", "senior", "executive"]
        
        sen_a = profile_a.get("seniority_level", "mid")
        sen_b = profile_b.get("seniority_level", "mid")
        
        try:
            idx_a = seniority_levels.index(sen_a)
            idx_b = seniority_levels.index(sen_b)
            
            gap = abs(idx_a - idx_b)
            
            # 1 level difference is ideal (mentor-mentee)
            if gap == 1:
                return 100.0
            elif gap == 0:
                return 85.0
            elif gap == 2:
                return 70.0
            else:
                return 50.0
        except ValueError:
            return 50.0
    
    def _calculate_overall_compatibility(self, features: Dict[str, float]) -> float:
        """Calculate weighted overall compatibility score."""
        score = 0.0
        
        # Skill features
        skill_score = (features["skill_match_score"] + features["skill_complementarity_score"]) / 2
        score += skill_score * self.feature_weights["skill_complementarity"]
        
        # Network value (bidirectional)
        network_score = (features["network_value_a_to_b"] + features["network_value_b_to_a"]) / 2
        score += network_score * self.feature_weights["network_value"]
        
        # Career alignment
        score += features["career_alignment_score"] * self.feature_weights["career_alignment"]
        
        # Geographic
        score += features["geographic_score"] * self.feature_weights["geographic_proximity"]
        
        return min(round(score, 2), 100.0)
    
    def _predict_job_opportunity(self, profile_a: pd.Series, profile_b: pd.Series, features: Dict) -> float:
        """Predict likelihood of job opportunity arising from connection (0-100)."""
        score = 0.0
        
        # Higher if one is more senior (can hire or refer)
        exp_gap = features["experience_gap"]
        if exp_gap >= 3:
            score += 30
        
        # Same industry increases job opportunity likelihood
        if features["industry_match"] >= 70:
            score += 30
        
        # Network value matters
        network_avg = (features["network_value_a_to_b"] + features["network_value_b_to_a"]) / 2
        score += network_avg * 0.3
        
        # Complementary skills
        if features["skill_complementarity_score"] >= 60:
            score += 10
        
        return min(100, score)
    
    def _predict_mentorship_value(self, profile_a: pd.Series, profile_b: pd.Series, features: Dict) -> float:
        """Predict quality of mentorship relationship (0-100)."""
        score = 0.0
        
        # Experience gap is key
        exp_gap = features["experience_gap"]
        if 3 <= exp_gap <= 7:
            score += 50  # Ideal mentorship gap
        elif 7 < exp_gap <= 12:
            score += 35
        elif exp_gap > 12:
            score += 20
        else:
            score += 10  # Peer mentorship
        
        # Same industry helps
        if features["industry_match"] >= 70:
            score += 30
        
        # Senior person must have valuable experience
        network_avg = (features["network_value_a_to_b"] + features["network_value_b_to_a"]) / 2
        score += network_avg * 0.2
        
        return min(100, score)
    
    def _predict_collaboration(self, profile_a: pd.Series, profile_b: pd.Series, features: Dict) -> float:
        """Predict potential for collaboration/partnership (0-100)."""
        score = 0.0
        
        # Complementary skills are crucial
        if features["skill_complementarity_score"] >= 70:
            score += 40
        elif features["skill_complementarity_score"] >= 50:
            score += 25
        
        # Peers collaborate better
        if features["experience_gap"] <= 3:
            score += 30
        
        # Same or related industry
        if features["industry_match"] >= 60:
            score += 20
        
        # Geographic proximity helps
        if features["geographic_score"] >= 70:
            score += 10
        
        return min(100, score)
    
    def _estimate_roi_timeframe(self, features: Dict) -> str:
        """Estimate how quickly value will be realized from connection."""
        compatibility = features["compatibility_score"]
        
        if compatibility >= 80:
            return "weeks"  # High compatibility = fast value
        elif compatibility >= 60:
            return "months"
        elif compatibility >= 40:
            return "6-12 months"
        else:
            return "long-term"
    
    def _generate_explanation(
        self,
        profile_a: pd.Series,
        profile_b: pd.Series,
        features: Dict[str, float]
    ) -> str:
        """Generate detailed, actionable explanation of compatibility."""
        # Get profile details
        role_b = profile_b.get("current_role", "professional")
        company_b = profile_b.get("current_company", "their company")
        years_b = profile_b.get("years_experience", 0)
        industry_b = profile_b.get("industry", "their industry")
        
        role_a = profile_a.get("current_role", "professional")
        years_a = profile_a.get("years_experience", 0)
        
        # Build detailed explanation
        parts = []
        
        # Primary relationship type
        exp_gap = features["experience_gap"]
        if 3 <= exp_gap <= 7:
            if years_b > years_a:
                parts.append(f"MENTORSHIP: They're a {role_b} at {company_b} with {years_b} years experience. ")
                parts.append(f"Can mentor you on: career growth, industry insights, navigating challenges.")
            else:
                parts.append(f"REVERSE MENTORSHIP: You have {exp_gap} more years experience. ")
                parts.append(f"You can mentor them while learning fresh perspectives.")
        elif exp_gap <= 2:
            parts.append(f"PEER COLLABORATION: Similar experience levels ({years_a} vs {years_b} years). ")
            parts.append(f"Best for: exchanging ideas, co-learning, potential partnerships.")
        else:
            parts.append(f"ADVISORY: {exp_gap} year experience gap creates valuable perspective sharing. ")
        
        # What they can offer you
        needs_a = set(profile_a.get("needs", []))
        can_offer_b = set(profile_b.get("can_offer", []))
        mutual_needs = list(needs_a.intersection(can_offer_b))
        
        if mutual_needs:
            parts.append(f" They can help with: {', '.join(mutual_needs[:3])}.")
        
        # What you can offer them
        needs_b = set(profile_b.get("needs", []))
        can_offer_a = set(profile_a.get("can_offer", []))
        mutual_offers = list(needs_b.intersection(can_offer_a))
        
        if mutual_offers:
            parts.append(f" You can help with: {', '.join(mutual_offers[:3])}.")
        
        # Shared skills/interests
        skills_a = set(profile_a.get("skills", []))
        skills_b = set(profile_b.get("skills", []))
        shared_skills = list(skills_a.intersection(skills_b))
        
        if shared_skills:
            parts.append(f" Shared expertise: {', '.join(shared_skills[:3])}.")
        
        # Action items
        parts.append(" ACTION: ")
        if features["predicted_job_opportunity_score"] >= 60:
            parts.append("Ask about job opportunities/referrals. ")
        if features["predicted_mentorship_value"] >= 60:
            parts.append("Request coffee chat for career advice. ")
        if features["predicted_collaboration_potential"] >= 60:
            parts.append("Explore collaboration opportunities. ")
        
        # Geographic note
        if features["geographic_score"] >= 90:
            parts.append(" Same location - suggest in-person meeting.")
        
        return "".join(parts)


def calculate_batch_features(
    pairs_df: pd.DataFrame,
    profiles_df: pd.DataFrame,
    config: Dict = None
) -> pd.DataFrame:
    """
    Calculate features for a batch of profile pairs.
    
    Args:
        pairs_df: DataFrame with pair_id, profile_a_id, profile_b_id
        profiles_df: DataFrame with all profiles
        config: Configuration dict
        
    Returns:
        DataFrame with calculated features
    """
    logger.info(f"Calculating features for {len(pairs_df)} pairs...")
    
    engine = CompatibilityFeatureEngine(config)
    
    # Create profile lookup
    profiles_dict = profiles_df.set_index("profile_id").to_dict("index")
    
    results = []
    
    for _, pair in pairs_df.iterrows():
        profile_a_id = pair["profile_a_id"]
        profile_b_id = pair["profile_b_id"]
        
        if profile_a_id not in profiles_dict or profile_b_id not in profiles_dict:
            continue
        
        profile_a = pd.Series(profiles_dict[profile_a_id])
        profile_b = pd.Series(profiles_dict[profile_b_id])
        
        features = engine.calculate_features(profile_a, profile_b)
        features.update({
            "pair_id": pair["pair_id"],
            "profile_a_id": profile_a_id,
            "profile_b_id": profile_b_id,
        })
        
        results.append(features)
    
    logger.info(f"Calculated features for {len(results)} pairs")
    return pd.DataFrame(results)
