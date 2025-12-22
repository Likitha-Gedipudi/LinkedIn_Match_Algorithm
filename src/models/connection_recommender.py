"""
Production-grade Connection Recommender System.
Recommends best professional connections for users.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path


class ConnectionRecommender:
    """
    Production-ready recommender for professional connections.
    
    Features:
    - Hybrid filtering (content + collaborative)
    - Red flag filtering
    - Ranking by multiple criteria
    - Configurable recommendation strategies
    """
    
    def __init__(
        self,
        pairs_df: pd.DataFrame,
        profiles_df: pd.DataFrame,
        filter_red_flags: bool = True,
        red_flag_threshold: float = 50.0
    ):
        """
        Initialize recommender.
        
        Args:
            pairs_df: Compatibility pairs dataset
            profiles_df: Profiles dataset
            filter_red_flags: Whether to filter out red flag profiles
            red_flag_threshold: Red flag score threshold for filtering
        """
        self.pairs_df = pairs_df
        self.profiles_df = profiles_df
        self.filter_red_flags = filter_red_flags
        self.red_flag_threshold = red_flag_threshold
        
        # Create lookups
        self.profile_lookup = profiles_df.set_index('profile_id')
        
    def recommend_for_user(
        self,
        user_id: str,
        top_n: int = 10,
        min_compatibility: float = 40.0,
        strategy: str = 'balanced'
    ) -> pd.DataFrame:
        """
        Recommend connections for a user.
        
        Args:
            user_id: Profile ID to recommend for
            top_n: Number of recommendations
            min_compatibility: Minimum compatibility score
            strategy: 'balanced', 'compatibility', 'roi', 'mentorship', 'collaboration'
            
        Returns:
            DataFrame with recommended connections and scores
        """
        # Get all pairs involving this user
        user_pairs = self.pairs_df[
            (self.pairs_df['profile_a_id'] == user_id) |
            (self.pairs_df['profile_b_id'] == user_id)
        ].copy()
        
        if len(user_pairs) == 0:
            return pd.DataFrame()
        
        # Normalize direction (user is always profile_a)
        user_pairs['candidate_id'] = user_pairs.apply(
            lambda row: row['profile_b_id'] if row['profile_a_id'] == user_id else row['profile_a_id'],
            axis=1
        )
        
        # Filter by minimum compatibility
        user_pairs = user_pairs[user_pairs['compatibility_score'] >= min_compatibility]
        
        # Filter red flags
        if self.filter_red_flags and 'red_flag_score' in self.profiles_df.columns:
            red_flag_profiles = set(
                self.profiles_df[
                    self.profiles_df['red_flag_score'] > self.red_flag_threshold
                ]['profile_id']
            )
            user_pairs = user_pairs[~user_pairs['candidate_id'].isin(red_flag_profiles)]
        
        # Calculate ranking score based on strategy
        user_pairs['ranking_score'] = self._calculate_ranking_score(user_pairs, strategy)
        
        # Sort and get top N
        recommendations = user_pairs.nlargest(top_n, 'ranking_score')
        
        # Add profile info
        recommendations = self._enrich_recommendations(recommendations)
        
        # Format output
        output_cols = [
            'candidate_id', 'ranking_score', 'compatibility_score',
            'predicted_job_opportunity_score', 'predicted_mentorship_value',
            'predicted_collaboration_potential', 'roi_timeframe',
            'candidate_name', 'candidate_role', 'candidate_company',
            'candidate_seniority', 'candidate_industry'
        ]
        
        available_cols = [col for col in output_cols if col in recommendations.columns]
        
        return recommendations[available_cols].reset_index(drop=True)
    
    def _calculate_ranking_score(self, pairs_df: pd.DataFrame, strategy: str) -> pd.Series:
        """Calculate ranking score based on strategy."""
        
        if strategy == 'compatibility':
            # Pure compatibility
            return pairs_df['compatibility_score']
        
        elif strategy == 'roi':
            # Weighted by ROI potential
            job_score = pairs_df.get('predicted_job_opportunity_score', 0)
            mentor_score = pairs_df.get('predicted_mentorship_value', 0)
            collab_score = pairs_df.get('predicted_collaboration_potential', 0)
            
            return (
                pairs_df['compatibility_score'] * 0.4 +
                job_score * 0.25 +
                mentor_score * 0.2 +
                collab_score * 0.15
            )
        
        elif strategy == 'mentorship':
            # Prioritize mentorship value
            mentor_score = pairs_df.get('predicted_mentorship_value', 0)
            return (
                mentor_score * 0.6 +
                pairs_df['compatibility_score'] * 0.4
            )
        
        elif strategy == 'collaboration':
            # Prioritize collaboration potential
            collab_score = pairs_df.get('predicted_collaboration_potential', 0)
            return (
                collab_score * 0.6 +
                pairs_df['compatibility_score'] * 0.4
            )
        
        else:  # 'balanced' (default)
            # Balanced approach
            return pairs_df['compatibility_score']
    
    def _enrich_recommendations(self, recommendations: pd.DataFrame) -> pd.DataFrame:
        """Add profile information to recommendations."""
        enriched = recommendations.copy()
        
        # Add candidate profile info
        for idx, row in enriched.iterrows():
            candidate_id = row['candidate_id']
            
            if candidate_id in self.profile_lookup.index:
                profile = self.profile_lookup.loc[candidate_id]
                
                enriched.at[idx, 'candidate_name'] = profile.get('name', 'Unknown')
                enriched.at[idx, 'candidate_role'] = profile.get('current_role', 'Unknown')
                enriched.at[idx, 'candidate_company'] = profile.get('current_company', 'Unknown')
                enriched.at[idx, 'candidate_seniority'] = profile.get('seniority_level', 'Unknown')
                enriched.at[idx, 'candidate_industry'] = profile.get('industry', 'Unknown')
        
        return enriched
    
    def batch_recommend(
        self,
        user_ids: List[str],
        top_n: int = 10,
        strategy: str = 'balanced'
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate recommendations for multiple users.
        
        Args:
            user_ids: List of profile IDs
            top_n: Number of recommendations per user
            strategy: Recommendation strategy
            
        Returns:
            Dictionary mapping user_id to recommendations DataFrame
        """
        recommendations = {}
        
        for user_id in user_ids:
            recs = self.recommend_for_user(user_id, top_n=top_n, strategy=strategy)
            if len(recs) > 0:
                recommendations[user_id] = recs
        
        return recommendations
    
    def get_hidden_gems(
        self,
        user_id: str,
        top_n: int = 10,
        min_gem_score: float = 60.0
    ) -> pd.DataFrame:
        """
        Recommend hidden gem profiles for a user.
        
        Args:
            user_id: Profile ID
            top_n: Number of gems to return
            min_gem_score: Minimum gem score threshold
            
        Returns:
            DataFrame with hidden gem recommendations
        """
        # Get all compatible pairs
        user_pairs = self.pairs_df[
            (self.pairs_df['profile_a_id'] == user_id) |
            (self.pairs_df['profile_b_id'] == user_id)
        ].copy()
        
        if len(user_pairs) == 0:
            return pd.DataFrame()
        
        # Get candidate IDs
        user_pairs['candidate_id'] = user_pairs.apply(
            lambda row: row['profile_b_id'] if row['profile_a_id'] == user_id else row['profile_a_id'],
            axis=1
        )
        
        # Filter by gem score
        if 'gem_score' in self.profiles_df.columns:
            gem_profiles = self.profiles_df[
                self.profiles_df['gem_score'] >= min_gem_score
            ]['profile_id'].tolist()
            
            user_pairs = user_pairs[user_pairs['candidate_id'].isin(gem_profiles)]
        
        # Merge with profile gem data
        gems = user_pairs.merge(
            self.profiles_df[['profile_id', 'gem_score', 'gem_type', 'gem_reason']],
            left_on='candidate_id',
            right_on='profile_id',
            how='left'
        )
        
        # Rank by gem score
        gems = gems.nlargest(top_n, 'gem_score')
        
        # Enrich
        gems = self._enrich_recommendations(gems)
        
        return gems.reset_index(drop=True)
    
    def evaluate_connection(
        self,
        user_id: str,
        candidate_id: str
    ) -> Dict[str, any]:
        """
        Evaluate a specific potential connection (production API).
        
        Args:
            user_id: User profile ID
            candidate_id: Candidate profile ID
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Find the pair
        pair = self.pairs_df[
            ((self.pairs_df['profile_a_id'] == user_id) & 
             (self.pairs_df['profile_b_id'] == candidate_id)) |
            ((self.pairs_df['profile_a_id'] == candidate_id) & 
             (self.pairs_df['profile_b_id'] == user_id))
        ]
        
        if len(pair) == 0:
            return {'error': 'Connection pair not found'}
        
        pair = pair.iloc[0]
        
        # Get candidate profile
        if candidate_id not in self.profile_lookup.index:
            return {'error': 'Candidate profile not found'}
        
        candidate = self.profile_lookup.loc[candidate_id]
        
        # Build evaluation
        evaluation = {
            'compatibility_score': float(pair['compatibility_score']),
            'recommendation': 'CONNECT' if pair['compatibility_score'] >= 70 else 
                            'CONSIDER' if pair['compatibility_score'] >= 50 else 'SKIP',
            
            'roi_metrics': {
                'job_opportunity': float(pair.get('predicted_job_opportunity_score', 0)),
                'mentorship_value': float(pair.get('predicted_mentorship_value', 0)),
                'collaboration_potential': float(pair.get('predicted_collaboration_potential', 0)),
                'expected_timeframe': pair.get('roi_timeframe', 'unknown')
            },
            
            'candidate_info': {
                'name': candidate.get('name', 'Unknown'),
                'role': candidate.get('current_role', 'Unknown'),
                'company': candidate.get('current_company', 'Unknown'),
                'seniority': candidate.get('seniority_level', 'Unknown'),
                'industry': candidate.get('industry', 'Unknown'),
                'years_experience': int(candidate.get('years_experience', 0))
            },
            
            'red_flags': {
                'has_red_flags': bool(candidate.get('red_flag_score', 0) > 50),
                'red_flag_score': float(candidate.get('red_flag_score', 0)),
                'reasons': candidate.get('red_flag_reasons', 'None')
            },
            
            'hidden_gem': {
                'is_gem': bool(candidate.get('gem_score', 0) > 70),
                'gem_score': float(candidate.get('gem_score', 0)),
                'gem_type': candidate.get('gem_type', 'None')
            },
            
            'explanation': pair.get('mutual_benefit_explanation', '')
        }
        
        return evaluation


def create_recommender(
    pairs_path: str = 'data/processed/compatibility_pairs_enhanced.csv',
    profiles_path: str = 'data/processed/profiles_enhanced.csv',
    **kwargs
) -> ConnectionRecommender:
    """
    Convenience function to create recommender from CSV files.
    
    Args:
        pairs_path: Path to pairs CSV
        profiles_path: Path to profiles CSV
        **kwargs: Additional arguments for ConnectionRecommender
        
    Returns:
        Initialized recommender
    """
    print(f"Loading data for recommender...")
    pairs = pd.read_csv(pairs_path)
    profiles = pd.read_csv(profiles_path)
    
    recommender = ConnectionRecommender(pairs, profiles, **kwargs)
    print(f"✅ Recommender ready with {len(profiles)} profiles and {len(pairs)} pairs")
    
    return recommender
