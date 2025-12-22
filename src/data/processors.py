"""
Data processing pipeline for profile data.
Handles cleaning, normalization, deduplication, and feature extraction.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from tqdm import tqdm

from ..utils import generate_id, get_logger, sanitize_string

logger = get_logger()


class ProfileProcessor:
    """
    Process and normalize profile data from multiple sources.
    
    Handles:
    - Data cleaning and validation
    - Schema normalization
    - Deduplication
    - Feature extraction
    """
    
    def __init__(
        self,
        min_fields_required: int = 5,
        require_skills: bool = True,
        deduplication: bool = True
    ):
        """
        Initialize profile processor.
        
        Args:
            min_fields_required: Minimum required non-null fields
            require_skills: Whether skills are required
            deduplication: Whether to deduplicate profiles
        """
        self.min_fields_required = min_fields_required
        self.require_skills = require_skills
        self.deduplication = deduplication
        
        self.processed_profiles = []
        self.seen_ids = set()
    
    def process_profiles(self, profiles: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Process a list of profiles.
        
        Args:
            profiles: List of raw profile dictionaries
            
        Returns:
            DataFrame with processed profiles
        """
        logger.info(f"Processing {len(profiles)} profiles...")
        
        processed = []
        skipped = 0
        
        for profile in tqdm(profiles, desc="Processing profiles"):
            # Clean and validate
            cleaned = self._clean_profile(profile)
            
            if not self._validate_profile(cleaned):
                skipped += 1
                continue
            
            # Check for duplicates
            if self.deduplication:
                profile_id = cleaned.get("profile_id")
                if profile_id in self.seen_ids:
                    skipped += 1
                    continue
                self.seen_ids.add(profile_id)
            
            # Normalize schema
            normalized = self._normalize_profile(cleaned)
            processed.append(normalized)
            self.processed_profiles.append(normalized)
        
        logger.info(f"Successfully processed {len(processed)} profiles (skipped {skipped})")
        
        return pd.DataFrame(processed)
    
    def _clean_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and sanitize profile data."""
        cleaned = {}
        
        # Generate ID if missing
        if "profile_id" not in profile or not profile["profile_id"]:
            profile["profile_id"] = generate_id(json.dumps(profile, sort_keys=True))
        
        for key, value in profile.items():
            # Clean strings
            if isinstance(value, str):
                cleaned[key] = sanitize_string(value)
            # Clean lists
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    cleaned[key] = [sanitize_string(item) for item in value if item]
                else:
                    cleaned[key] = value
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _validate_profile(self, profile: Dict[str, Any]) -> bool:
        """Validate profile meets minimum requirements."""
        # Check minimum fields
        non_null_fields = sum(1 for v in profile.values() if v is not None and v != "")
        if non_null_fields < self.min_fields_required:
            return False
        
        # Check skills requirement
        if self.require_skills:
            skills = profile.get("skills", [])
            if not skills or len(skills) == 0:
                return False
        
        # Check required fields
        required_fields = ["profile_id"]
        if not all(field in profile for field in required_fields):
            return False
        
        return True
    
    def _normalize_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize profile to consistent schema."""
        normalized = {
            "profile_id": profile.get("profile_id"),
            "name": profile.get("name"),
            "email": profile.get("email"),
            "location": profile.get("location"),
            "headline": profile.get("headline") or profile.get("bio"),
            "about": profile.get("about") or profile.get("bio"),
            "current_role": profile.get("current_role") or self._extract_current_role(profile),
            "current_company": profile.get("current_company") or self._extract_current_company(profile),
            "industry": profile.get("industry"),
            "years_experience": profile.get("years_experience") or self._estimate_experience(profile),
            "seniority_level": profile.get("seniority_level") or self._infer_seniority(profile),
            "skills": profile.get("skills") or profile.get("primary_languages", []),
            "experience": profile.get("experience", []),
            "education": profile.get("education", []),
            "connections": profile.get("connections") or profile.get("followers", 0),
            "goals": profile.get("goals", []),
            "needs": profile.get("needs", []),
            "can_offer": profile.get("can_offer", []),
            "remote_preference": profile.get("remote_preference"),
            "source": profile.get("source", "unknown"),
        }
        
        return {k: v for k, v in normalized.items() if v is not None}
    
    def _extract_current_role(self, profile: Dict) -> Optional[str]:
        """Extract current role from experience."""
        experience = profile.get("experience", [])
        if experience and len(experience) > 0:
            return experience[0].get("title")
        return None
    
    def _extract_current_company(self, profile: Dict) -> Optional[str]:
        """Extract current company from experience."""
        experience = profile.get("experience", [])
        if experience and len(experience) > 0:
            return experience[0].get("company")
        return None
    
    def _estimate_experience(self, profile: Dict) -> int:
        """Estimate years of experience."""
        experience = profile.get("experience", [])
        if not experience:
            return 0
        
        # Simple estimation: count number of jobs * 2 years average
        return min(len(experience) * 2, 30)
    
    def _infer_seniority(self, profile: Dict) -> str:
        """Infer seniority level from role title and experience."""
        role = (profile.get("current_role") or "").lower()
        years = self._estimate_experience(profile)
        
        # Check title keywords
        if any(word in role for word in ["vp", "cto", "ceo", "cfo", "chief", "head of"]):
            return "executive"
        elif any(word in role for word in ["senior", "lead", "principal", "staff"]):
            return "senior"
        elif any(word in role for word in ["junior", "associate", "entry"]):
            return "entry"
        
        # Fall back to years
        if years >= 15:
            return "executive"
        elif years >= 8:
            return "senior"
        elif years >= 3:
            return "mid"
        else:
            return "entry"
    
    def save_processed_data(self, output_file: str):
        """Save processed profiles to file."""
        df = pd.DataFrame(self.processed_profiles)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_file.endswith('.csv'):
            df.to_csv(output_file, index=False)
        elif output_file.endswith('.parquet'):
            df.to_parquet(output_file, index=False)
        elif output_file.endswith('.json'):
            df.to_json(output_file, orient='records', indent=2)
        
        logger.info(f"Saved {len(df)} processed profiles to {output_file}")


class CompatibilityPairGenerator:
    """Generate compatibility pairs from processed profiles."""
    
    def __init__(self, max_pairs_per_profile: int = 100):
        """
        Initialize pair generator.
        
        Args:
            max_pairs_per_profile: Maximum pairs to generate per profile
        """
        self.max_pairs_per_profile = max_pairs_per_profile
    
    def generate_pairs(
        self,
        profiles: pd.DataFrame,
        sample_size: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generate profile pairs for compatibility scoring.
        
        Args:
            profiles: DataFrame of profiles
            sample_size: Optional sample size to limit pairs
            
        Returns:
            DataFrame of profile pairs
        """
        logger.info(f"Generating compatibility pairs from {len(profiles)} profiles...")
        
        pairs = []
        profile_ids = profiles["profile_id"].tolist()
        
        for i, profile_a_id in enumerate(tqdm(profile_ids, desc="Generating pairs")):
            # Randomly sample other profiles for pairing
            num_pairs = min(self.max_pairs_per_profile, len(profile_ids) - 1)
            
            for profile_b_id in pd.Series(profile_ids).sample(n=num_pairs, random_state=i).tolist():
                if profile_a_id == profile_b_id:
                    continue
                
                pairs.append({
                    "pair_id": generate_id(f"{profile_a_id}_{profile_b_id}"),
                    "profile_a_id": profile_a_id,
                    "profile_b_id": profile_b_id,
                })
                
                # Limit total pairs if sample_size specified
                if sample_size and len(pairs) >= sample_size:
                    break
            
            if sample_size and len(pairs) >= sample_size:
                break
        
        logger.info(f"Generated {len(pairs)} profile pairs")
        return pd.DataFrame(pairs)
