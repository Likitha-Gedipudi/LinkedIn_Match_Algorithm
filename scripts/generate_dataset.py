#!/usr/bin/env python3
"""
Script to process raw profile data and generate the final compatibility dataset.

This script:
1. Loads all raw profile data
2. Processes and normalizes profiles
3. Generates profile pairs
4. Calculates compatibility features
5. Exports final dataset files

Usage:
    python scripts/generate_dataset.py
    python scripts/generate_dataset.py --max-profiles 5000 --max-pairs 50000
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.processors import ProfileProcessor, CompatibilityPairGenerator
from src.features.compatibility_features import calculate_batch_features
from src.utils import get_logger, get_config

logger = get_logger()


def load_raw_profiles(raw_data_path: str) -> list:
    """Load all raw profile JSON files."""
    logger.info(f"Loading raw profiles from {raw_data_path}...")
    
    raw_path = Path(raw_data_path)
    if not raw_path.exists():
        logger.error(f"Raw data path does not exist: {raw_data_path}")
        return []
    
    all_profiles = []
    
    for json_file in raw_path.glob("*.json"):
        logger.info(f"Loading {json_file.name}...")
        with open(json_file, 'r') as f:
            profiles = json.load(f)
            all_profiles.extend(profiles)
    
    logger.info(f"Loaded {len(all_profiles)} total raw profiles")
    return all_profiles


def main():
    parser = argparse.ArgumentParser(description="Generate LinkedIn compatibility dataset")
    
    parser.add_argument(
        "--max-profiles",
        type=int,
        help="Maximum number of profiles to process"
    )
    
    parser.add_argument(
        "--max-pairs",
        type=int,
        help="Maximum number of profile pairs to generate"
    )
    
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Output directory for processed data"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    
    logger.info("=" * 80)
    logger.info("LinkedIn Professional Matching Dataset Generation")
    logger.info("=" * 80)
    
    # Step 1: Load raw profiles
    logger.info("\n[1/5] Loading raw profile data...")
    raw_profiles = load_raw_profiles(config.data.raw_data_path)
    
    if not raw_profiles:
        logger.error("No raw profiles found. Run scrapers first!")
        return
    
    if args.max_profiles:
        raw_profiles = raw_profiles[:args.max_profiles]
    
    # Step 2: Process profiles
    logger.info(f"\n[2/5] Processing {len(raw_profiles)} profiles...")
    processor = ProfileProcessor(
        min_fields_required=config.data.profiles.min_fields_required,
        require_skills=config.data.profiles.require_skills,
        deduplication=config.data.profiles.deduplication,
    )
    
    profiles_df = processor.process_profiles(raw_profiles)
    logger.info(f"Processed {len(profiles_df)} valid profiles")
    
    # Save processed profiles
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    profiles_file = output_dir / "profiles.csv"
    profiles_df.to_csv(profiles_file, index=False)
    logger.info(f"Saved profiles to {profiles_file}")
    
    # Step 3: Generate profile pairs
    logger.info("\n[3/5] Generating profile pairs...")
    pair_generator = CompatibilityPairGenerator(max_pairs_per_profile=100)
    pairs_df = pair_generator.generate_pairs(
        profiles_df,
        sample_size=args.max_pairs
    )
    logger.info(f"Generated {len(pairs_df)} profile pairs")
    
    # Step 4: Calculate compatibility features
    logger.info("\n[4/5] Calculating compatibility features...")
    features_config = {
        "skill_weight": config.features.skills.complementarity_weight,
        "network_weight": config.features.network.network_value_weight,
        "career_weight": config.features.career.alignment_weight,
        "geographic_weight": config.features.geographic.weight,
    }
    
    compatibility_df = calculate_batch_features(
        pairs_df,
        profiles_df,
        features_config
    )
    logger.info(f"Calculated features for {len(compatibility_df)} pairs")
    
    # Step 5: Export final datasets
    logger.info("\n[5/5] Exporting final datasets...")
    
    # Compatibility pairs dataset
    compatibility_file = output_dir / "compatibility_pairs.csv"
    compatibility_df.to_csv(compatibility_file, index=False)
    logger.info(f"Saved compatibility pairs to {compatibility_file}")
    
    # Generate metadata
    metadata = {
        "total_profiles": len(profiles_df),
        "total_pairs": len(compatibility_df),
        "avg_compatibility_score": float(compatibility_df["compatibility_score"].mean()),
        "sources": profiles_df["source"].value_counts().to_dict(),
        "seniority_distribution": profiles_df["seniority_level"].value_counts().to_dict(),
        "top_industries": profiles_df["industry"].value_counts().head(10).to_dict(),
        "generation_timestamp": pd.Timestamp.now().isoformat(),
    }
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_file}")
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("Dataset Generation Complete!")
    logger.info("=" * 80)
    logger.info(f"Total Profiles: {len(profiles_df):,}")
    logger.info(f"Total Compatibility Pairs: {len(compatibility_df):,}")
    logger.info(f"Average Compatibility Score: {metadata['avg_compatibility_score']:.2f}/100")
    logger.info(f"\nOutput files:")
    logger.info(f"  - {profiles_file}")
    logger.info(f"  - {compatibility_file}")
    logger.info(f"  - {metadata_file}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
