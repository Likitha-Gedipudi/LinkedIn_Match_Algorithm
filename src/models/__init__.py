"""
Production ML Models for LinkedIn Professional Matching.

This package contains deployment-ready machine learning models:
- Red Flag Classifier: Detect problematic profiles
- Compatibility Scorer: Predict connection value
- Connection Recommender: Recommend best connections
"""

from .red_flag_classifier import RedFlagClassifier, train_red_flag_classifier
from .compatibility_scorer import CompatibilityScorer, train_compatibility_scorer
from .connection_recommender import ConnectionRecommender, create_recommender

__all__ = [
    'RedFlagClassifier',
    'train_red_flag_classifier',
    'CompatibilityScorer',
    'train_compatibility_scorer',
    'ConnectionRecommender',
    'create_recommender',
]
