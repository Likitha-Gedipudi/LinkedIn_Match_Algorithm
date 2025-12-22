#!/usr/bin/env python3
"""
Master training script for all production models.
Trains and saves all models for deployment.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.red_flag_classifier import train_red_flag_classifier
from src.models.compatibility_scorer import train_compatibility_scorer

import json
from datetime import datetime


def train_all_models():
    """Train all production models."""
    print("="*80)
    print("🚀 TRAINING ALL PRODUCTION MODELS")
    print("="*80)
    
    models_dir = Path("data/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'training_date': datetime.now().isoformat(),
        'models': {}
    }
    
    # 1. Train Red Flag Classifier
    print("\n" + "="*80)
    print("1️⃣  RED FLAG CLASSIFIER")
    print("="*80)
    
    try:
        red_flag_classifier = train_red_flag_classifier(
            profiles_path='data/processed/profiles_enhanced.csv',
            model_save_path='data/models/red_flag_classifier.joblib',
            model_type='random_forest'
        )
        results['models']['red_flag_classifier'] = {
            'status': 'success',
            'path': 'data/models/red_flag_classifier.joblib',
            'model_type': 'random_forest'
        }
        print("\n✅ Red Flag Classifier trained and saved!")
    except Exception as e:
        print(f"\n❌ Error training Red Flag Classifier: {e}")
        results['models']['red_flag_classifier'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # 2. Train Compatibility Scorer
    print("\n" + "="*80)
    print("2️⃣  COMPATIBILITY SCORER")
    print("="*80)
    
    try:
        compatibility_scorer = train_compatibility_scorer(
            pairs_path='data/processed/compatibility_pairs_enhanced.csv',
            model_save_path='data/models/compatibility_scorer.joblib',
            model_type='gradient_boosting'  # Use gradient_boosting as fallback
        )
        results['models']['compatibility_scorer'] = {
            'status': 'success',
            'path': 'data/models/compatibility_scorer.joblib',
            'model_type': 'gradient_boosting'
        }
        print("\n✅ Compatibility Scorer trained and saved!")
    except Exception as e:
        print(f"\n❌ Error training Compatibility Scorer: {e}")
        results['models']['compatibility_scorer'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # 3. Recommender System (no training needed, uses pre-computed scores)
    print("\n" + "="*80)
    print("3️⃣  CONNECTION RECOMMENDER")
    print("="*80)
    print("✅ Recommender system ready (uses pre-computed compatibility scores)")
    results['models']['connection_recommender'] = {
        'status': 'ready',
        'note': 'No training needed - uses pre-computed scores'
    }
    
    # Save training results
    results_path = models_dir / 'training_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print("📊 TRAINING SUMMARY")
    print("="*80)
    
    for model_name, model_info in results['models'].items():
        status_emoji = "✅" if model_info['status'] in ['success', 'ready'] else "❌"
        print(f"{status_emoji} {model_name}: {model_info['status']}")
    
    print(f"\n📁 Training results saved to: {results_path}")
    print("="*80)
    
    # Check if all critical models trained successfully
    critical_models = ['red_flag_classifier', 'compatibility_scorer']
    all_success = all(
        results['models'].get(m, {}).get('status') == 'success'
        for m in critical_models
    )
    
    if all_success:
        print("\n🎉 ALL MODELS TRAINED SUCCESSFULLY!")
        print("\nDeployment-ready models:")
        print("  • data/models/red_flag_classifier.joblib")
        print("  • data/models/compatibility_scorer.joblib")
        print("\n🚀 Ready for production deployment!")
    else:
        print("\n⚠️  Some models failed to train. Check errors above.")
    
    print("="*80)
    
    return results


if __name__ == "__main__":
    train_all_models()
