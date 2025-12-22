#!/usr/bin/env python3
"""
Regenerate enhanced LinkedIn compatibility dataset with new features.

This script:
1. Loads existing profiles or generates new ones
2. Analyzes profiles for red flags and hidden gems
3. Generates compatibility pairs with enhanced explanations and ROI predictions
4. Creates conversation starters for high-value pairs
5. Generates skills network analysis
6. Exports enhanced datasets
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.synthetic_generator import SyntheticProfileGenerator
from src.features.red_flags_detector import RedFlagsDetector
from src.features.hidden_gems_detector import HiddenGemsDetector
from src.features.compatibility_features import CompatibilityFeatureEngine
from src.features.conversation_generator import ConversationStarterGenerator
from src.utils import get_logger

logger = get_logger()


def load_or_generate_profiles(num_profiles: int = 50000) -> pd.DataFrame:
    """Load existing profiles or generate new ones."""
    profiles_path = Path("data/processed/profiles.csv")
    
    if profiles_path.exists():
        logger.info(f"Loading existing profiles from {profiles_path}")
        df = pd.read_csv(profiles_path)
        
        # Parse JSON columns - handle different formats
        json_columns = ['skills', 'experience', 'education', 'goals', 'needs', 'can_offer']
        for col in json_columns:
            if col in df.columns:
                def safe_parse(x):
                    if pd.isna(x) or x == '' or x == '[]':
                        return []
                    try:
                        # Try parsing as JSON
                        parsed = json.loads(x)
                        return parsed if isinstance(parsed, list) else []
                    except (json.JSONDecodeError, TypeError):
                        # If already a list or other format, return as is or empty list
                        return [] if not isinstance(x, list) else x
                
                df[col] = df[col].apply(safe_parse)
        
        logger.info(f"Loaded {len(df)} profiles")
        return df
    else:
        logger.info(f"Generating {num_profiles} new profiles...")
        generator = SyntheticProfileGenerator(seed=42)
        profiles = generator.generate_batch(num_profiles)
        df = pd.DataFrame(profiles)
        logger.info(f"Generated {len(df)} profiles")
        return df


def analyze_profiles_for_red_flags_and_gems(profiles_df: pd.DataFrame) -> pd.DataFrame:
    """Add red flag and gem analysis to profiles."""
    logger.info("Analyzing profiles for red flags...")
    red_flags_detector = RedFlagsDetector()
    profiles_df = red_flags_detector.batch_analyze(profiles_df)
    
    logger.info("Analyzing profiles for hidden gems...")
    gems_detector = HiddenGemsDetector(all_profiles=profiles_df)
    profiles_df = gems_detector.batch_analyze(profiles_df)
    
    return profiles_df


def generate_compatibility_pairs(
    profiles_df: pd.DataFrame,
    max_pairs: int = 500000,
    sample_rate: float = 0.1
) -> pd.DataFrame:
    """Generate compatibility pairs with enhanced features."""
    logger.info(f"Generating compatibility pairs (targeting {max_pairs} pairs)...")
    
    # Sample profiles for pairing to keep dataset manageable
    num_profiles = len(profiles_df)
    pairs_to_generate_per_profile = int(max_pairs / num_profiles)
    
    logger.info(f"Will generate ~{pairs_to_generate_per_profile} pairs per profile")
    
    # Create pairs
    pairs = []
    profile_ids = profiles_df['profile_id'].tolist()
    
    engine = CompatibilityFeatureEngine()
    
    # Create profile lookup
    profiles_dict = profiles_df.set_index('profile_id')
    
    for idx, profile_a_id in enumerate(profile_ids):
        if (idx + 1) % 1000 == 0:
            logger.info(f"Processed {idx + 1}/{num_profiles} profiles...")
        
        # Sample potential matches
        import random
        potential_matches = random.sample(
            [pid for pid in profile_ids if pid != profile_a_id],
            min(pairs_to_generate_per_profile, num_profiles - 1)
        )
        
        for profile_b_id in potential_matches:
            profile_a = profiles_dict.loc[profile_a_id]
            profile_b = profiles_dict.loc[profile_b_id]
            
            # Calculate features
            features = engine.calculate_features(profile_a, profile_b)
            features['pair_id'] = f"{profile_a_id}_{profile_b_id}"
            features['profile_a_id'] = profile_a_id
            features['profile_b_id'] = profile_b_id
            
            pairs.append(features)
            
            if len(pairs) >= max_pairs:
                break
        
        if len(pairs) >= max_pairs:
            break
    
    logger.info(f"Generated {len(pairs)} compatibility pairs")
    return pd.DataFrame(pairs)


def generate_conversation_starters_dataset(
    pairs_df: pd.DataFrame,
    profiles_df: pd.DataFrame,
    min_score: float = 60.0
) -> pd.DataFrame:
    """Generate conversation starters for high-value pairs."""
    logger.info("Generating conversation starters...")
    
    generator = ConversationStarterGenerator()
    starters_df = generator.batch_generate(pairs_df, profiles_df, min_compatibility_score=min_score)
    
    return starters_df


def generate_skills_network_analysis(profiles_df: pd.DataFrame) -> pd.DataFrame:
    """Generate skills supply/demand analysis."""
    logger.info("Generating skills network analysis...")
    
    from collections import Counter
    
    # Collect all skills with their demand/supply
    skills_offered = []
    skills_needed = []
    skill_by_seniority = {}
    skill_by_industry = {}
    
    for _, profile in profiles_df.iterrows():
        skills = profile.get('skills', [])
        needs = profile.get('needs', [])
        seniority = profile.get('seniority_level', 'mid')
        industry = profile.get('industry', 'Unknown')
        
        for skill in skills:
            skills_offered.append(skill)
            
            if skill not in skill_by_seniority:
                skill_by_seniority[skill] = []
            skill_by_seniority[skill].append(seniority)
            
            if skill not in skill_by_industry:
                skill_by_industry[skill] = []
            skill_by_industry[skill].append(industry)
        
        for need in needs:
            skills_needed.append(need)
    
    # Count frequencies
    supply_counts = Counter(skills_offered)
    demand_counts = Counter(skills_needed)
    
    # Build skills network
    all_skills = set(list(supply_counts.keys()) + list(demand_counts.keys()))
    
    if not all_skills:
        logger.warning("No skills found in profiles, creating empty skills network")
        return pd.DataFrame(columns=[
            'skill_name', 'supply_count', 'demand_count', 'supply_demand_ratio',
            'rarity_score', 'avg_seniority', 'top_industries', 'total_mentions'
        ])
    
    skills_data = []
    for skill in all_skills:
        supply = supply_counts.get(skill, 0)
        demand = demand_counts.get(skill, 0)
        
        # Calculate rarity score
        total_profiles = len(profiles_df)
        frequency = supply / total_profiles if total_profiles > 0 else 0
        
        if frequency < 0.05:
            rarity_score = 90
        elif frequency < 0.15:
            rarity_score = 70
        elif frequency < 0.30:
            rarity_score = 50
        else:
            rarity_score = 30
        
        # Get most common seniority and industry
        seniorities = skill_by_seniority.get(skill, [])
        industries = skill_by_industry.get(skill, [])
        
        avg_seniority = Counter(seniorities).most_common(1)[0][0] if seniorities else 'mid'
        top_industries = [ind for ind, _ in Counter(industries).most_common(3)]
        
        skills_data.append({
            'skill_name': skill,
            'supply_count': supply,
            'demand_count': demand,
            'supply_demand_ratio': supply / demand if demand > 0 else float('inf'),
            'rarity_score': rarity_score,
            'avg_seniority': avg_seniority,
            'top_industries': ', '.join(top_industries) if top_industries else 'Various',
            'total_mentions': supply + demand
        })
    
    if not skills_data:
        logger.warning("No skills data created, returning empty dataframe")
        return pd.DataFrame(columns=[
            'skill_name', 'supply_count', 'demand_count', 'supply_demand_ratio',
            'rarity_score', 'avg_seniority', 'top_industries', 'total_mentions'
        ])
    
    skills_df = pd.DataFrame(skills_data)
    skills_df = skills_df.sort_values('rarity_score', ascending=False)
    
    logger.info(f"Generated skills network analysis for {len(skills_df)} unique skills")
    return skills_df


def save_datasets(
    profiles_df: pd.DataFrame,
    pairs_df: pd.DataFrame,
    starters_df: pd.DataFrame,
    skills_df: pd.DataFrame
):
    """Save all datasets to processed directory."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Saving datasets...")
    
    # Save profiles (convert lists to JSON strings for CSV)
    profiles_export = profiles_df.copy()
    json_columns = ['skills', 'experience', 'education', 'goals', 'needs', 'can_offer']
    for col in json_columns:
        if col in profiles_export.columns:
            profiles_export[col] = profiles_export[col].apply(json.dumps)
    
    profiles_export.to_csv(output_dir / "profiles_enhanced.csv", index=False)
    logger.info(f"Saved {len(profiles_export)} profiles to profiles_enhanced.csv")
    
    # Save compatibility pairs
    pairs_df.to_csv(output_dir / "compatibility_pairs_enhanced.csv", index=False)
    logger.info(f"Saved {len(pairs_df)} pairs to compatibility_pairs_enhanced.csv")
    
    # Save conversation starters
    if len(starters_df) > 0:
        starters_df.to_csv(output_dir / "conversation_starters.csv", index=False)
        logger.info(f"Saved {len(starters_df)} conversation starters to conversation_starters.csv")
    
    # Save skills network
    skills_df.to_csv(output_dir / "skills_network.csv", index=False)
    logger.info(f"Saved {len(skills_df)} skills to skills_network.csv")
    
    # Generate top red flags and gems exports
    logger.info("Generating specialized exports...")
    
    # Top red flags
    red_flags = profiles_export[profiles_export['red_flag_score'] > 50].sort_values('red_flag_score', ascending=False)
    red_flags.to_csv(output_dir / "red_flags_top_profiles.csv", index=False)
    logger.info(f"Saved {len(red_flags)} red flag profiles")
    
    # Hidden gems
    gems = profiles_export[profiles_export['gem_score'] > 70].sort_values('gem_score', ascending=False)
    gems.to_csv(output_dir / "hidden_gems_top_profiles.csv", index=False)
    logger.info(f"Saved {len(gems)} hidden gem profiles")
    
    # Generate metadata
    metadata = {
        'generation_date': datetime.now().isoformat(),
        'total_profiles': len(profiles_df),
        'total_pairs': len(pairs_df),
        'total_conversation_starters': len(starters_df),
        'total_skills': len(skills_df),
        'red_flags_detected': int((profiles_df['red_flag_score'] > 50).sum()),
        'hidden_gems_found': int((profiles_df['gem_score'] > 70).sum()),
        'avg_compatibility_score': float(pairs_df['compatibility_score'].mean()),
        'high_value_pairs': int((pairs_df['compatibility_score'] >= 70).sum()),
        'seniority_distribution': profiles_df['seniority_level'].value_counts().to_dict(),
        'top_industries': profiles_df['industry'].value_counts().head(10).to_dict(),
    }
    
    with open(output_dir / "metadata_enhanced.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info("Saved metadata to metadata_enhanced.json")
    
    print("\n" + "="*80)
    print("✅ DATASET GENERATION COMPLETE!")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   • Profiles: {metadata['total_profiles']:,}")
    print(f"   • Compatibility Pairs: {metadata['total_pairs']:,}")
    print(f"   • Conversation Starters: {metadata['total_conversation_starters']:,}")
    print(f"   • Unique Skills: {metadata['total_skills']:,}")
    print(f"   • Red Flag Profiles: {metadata['red_flags_detected']:,}")
    print(f"   • Hidden Gems: {metadata['hidden_gems_found']:,}")
    print(f"   • Avg Compatibility: {metadata['avg_compatibility_score']:.1f}/100")
    print(f"   • High-Value Pairs (≥70): {metadata['high_value_pairs']:,}")
    print(f"\n📁 Files saved to: {output_dir.absolute()}")
    print("="*80 + "\n")


def main():
    """Main execution function."""
    logger.info("="*80)
    logger.info("Starting Enhanced LinkedIn Compatibility Dataset Generation")
    logger.info("="*80)
    
    # Step 1: Load or generate profiles
    profiles_df = load_or_generate_profiles(num_profiles=50000)
    
    # Step 2: Analyze for red flags and gems
    profiles_df = analyze_profiles_for_red_flags_and_gems(profiles_df)
    
    # Step 3: Generate compatibility pairs
    pairs_df = generate_compatibility_pairs(profiles_df, max_pairs=500000)
    
    # Step 4: Generate conversation starters
    starters_df = generate_conversation_starters_dataset(pairs_df, profiles_df, min_score=60.0)
    
    # Step 5: Generate skills network analysis
    skills_df = generate_skills_network_analysis(profiles_df)
    
    # Step 6: Save all datasets
    save_datasets(profiles_df, pairs_df, starters_df, skills_df)
    
    logger.info("All done! 🎉")


if __name__ == "__main__":
    main()
