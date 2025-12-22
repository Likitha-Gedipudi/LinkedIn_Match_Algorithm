"""
Production-grade Red Flag Classifier.
Binary classification model to detect problematic LinkedIn profiles.
"""

import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    roc_auc_score,
    precision_recall_fscore_support
)

import warnings
warnings.filterwarnings('ignore')


class RedFlagClassifier:
    """
    Production-ready classifier for detecting red flag profiles.
    
    Features:
    - Sklearn pipeline with preprocessing
    - Model serialization (save/load)
    - Cross-validation
    - Production inference API
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize classifier.
        
        Args:
            model_type: 'random_forest' or 'gradient_boosting'
        """
        self.model_type = model_type
        self.pipeline = None
        self.feature_names = None
        self.is_trained = False
        
    def _create_pipeline(self) -> Pipeline:
        """Create sklearn pipeline with preprocessing and model."""
        if self.model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        else:  # gradient_boosting
            model = GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=10,
                subsample=0.8,
                random_state=42
            )
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', model)
        ])
        
        return pipeline
    
    def prepare_features(self, profiles_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extract features for red flag classification.
        
        Args:
            profiles_df: DataFrame with profile data
            
        Returns:
            X: Feature matrix
            y: Target labels (1 = red flag, 0 = clean)
        """
        # Feature engineering
        features = pd.DataFrame()
        
        # Connection features
        features['connections'] = profiles_df['connections']
        features['connections_log'] = np.log1p(profiles_df['connections'])
        features['is_high_connections'] = (profiles_df['connections'] > 5000).astype(int)
        
        # Experience features
        features['years_experience'] = profiles_df['years_experience']
        features['connections_per_year'] = profiles_df['connections'] / (profiles_df['years_experience'] + 1)
        
        # Seniority encoding
        seniority_map = {'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3}
        features['seniority_encoded'] = profiles_df['seniority_level'].map(seniority_map).fillna(1)
        
        # Skills count (parse JSON if needed)
        if profiles_df['skills'].dtype == object:
            features['skills_count'] = profiles_df['skills'].apply(
                lambda x: len(eval(x)) if isinstance(x, str) else len(x) if isinstance(x, list) else 0
            )
        else:
            features['skills_count'] = 0
        
        # Experience count
        if 'experience' in profiles_df.columns:
            features['experience_count'] = profiles_df['experience'].apply(
                lambda x: len(eval(x)) if isinstance(x, str) else len(x) if isinstance(x, list) else 0
            )
        else:
            features['experience_count'] = 0
        
        # Education count
        if 'education' in profiles_df.columns:
            features['education_count'] = profiles_df['education'].apply(
                lambda x: len(eval(x)) if isinstance(x, str) else len(x) if isinstance(x, list) else 1
            )
        else:
            features['education_count'] = 1
        
        # Engagement signals
        if 'engagement_quality_score' in profiles_df.columns:
            features['engagement_quality'] = profiles_df['engagement_quality_score']
        else:
            features['engagement_quality'] = 50
        
        # Spam likelihood
        if 'spam_likelihood' in profiles_df.columns:
            features['spam_likelihood'] = profiles_df['spam_likelihood']
        else:
            features['spam_likelihood'] = 0
        
        # Profile completeness score
        features['profile_completeness'] = (
            (features['skills_count'] > 5).astype(int) * 25 +
            (features['experience_count'] > 2).astype(int) * 25 +
            (features['education_count'] > 0).astype(int) * 25 +
            (features['connections'] > 100).astype(int) * 25
        )
        
        # Red flag indicators
        features['collector_signal'] = ((features['connections'] > 5000) & 
                                       (features['profile_completeness'] < 50)).astype(int)
        features['ghost_signal'] = ((features['skills_count'] < 3) & 
                                   (features['experience_count'] < 2)).astype(int)
        
        # Target: red flag score > 50
        if 'red_flag_score' in profiles_df.columns:
            y = (profiles_df['red_flag_score'] > 50).astype(int)
        else:
            # Fallback: use heuristic
            y = ((features['collector_signal'] == 1) | 
                 (features['ghost_signal'] == 1) | 
                 (features['spam_likelihood'] > 30)).astype(int)
        
        self.feature_names = features.columns.tolist()
        
        return features, y
    
    def train(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        test_size: float = 0.2,
        validate: bool = True
    ) -> Dict[str, float]:
        """
        Train the red flag classifier.
        
        Args:
            X: Feature matrix
            y: Target labels
            test_size: Proportion for test set
            validate: Whether to run cross-validation
            
        Returns:
            Dictionary with metrics
        """
        print(f"Training {self.model_type} red flag classifier...")
        print(f"Dataset: {len(X)} samples, {X.shape[1]} features")
        print(f"Class distribution: {y.value_counts().to_dict()}")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Create and train pipeline
        self.pipeline = self._create_pipeline()
        self.pipeline.fit(X_train, y_train)
        
        # Predictions
        y_pred = self.pipeline.predict(X_test)
        y_proba = self.pipeline.predict_proba(X_test)[:, 1]
        
        # Metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='binary'
        )
        roc_auc = roc_auc_score(y_test, y_proba)
        
        metrics = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'test_size': len(X_test),
            'train_size': len(X_train)
        }
        
        print(f"\n✅ Training Complete!")
        print(f"  • Precision: {precision:.3f}")
        print(f"  • Recall: {recall:.3f}")
        print(f"  • F1 Score: {f1:.3f}")
        print(f"  • ROC-AUC: {roc_auc:.3f}")
        
        # Cross-validation
        if validate:
            print(f"\n🔄 Running 5-fold cross-validation...")
            cv_scores = cross_val_score(
                self.pipeline, X, y, cv=5, scoring='f1', n_jobs=-1
            )
            metrics['cv_f1_mean'] = cv_scores.mean()
            metrics['cv_f1_std'] = cv_scores.std()
            print(f"  • CV F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        
        # Feature importance
        if hasattr(self.pipeline.named_steps['classifier'], 'feature_importances_'):
            importances = self.pipeline.named_steps['classifier'].feature_importances_
            feature_importance = sorted(
                zip(self.feature_names, importances),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            print(f"\n📊 Top 10 Important Features:")
            for feat, imp in feature_importance:
                print(f"  • {feat}: {imp:.4f}")
        
        self.is_trained = True
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict red flags for profiles.
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of predictions (0 = clean, 1 = red flag)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.pipeline.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict red flag probabilities.
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of probabilities [prob_clean, prob_red_flag]
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.pipeline.predict_proba(X)
    
    def predict_single(self, profile: pd.Series) -> Dict[str, any]:
        """
        Predict red flag for a single profile (production API).
        
        Args:
            profile: Single profile data
            
        Returns:
            Dictionary with prediction and probability
        """
        # Prepare features
        X, _ = self.prepare_features(pd.DataFrame([profile]))
        
        # Predict
        pred = self.predict(X)[0]
        proba = self.predict_proba(X)[0]
        
        return {
            'is_red_flag': bool(pred),
            'red_flag_probability': float(proba[1]),
            'confidence': float(max(proba)),
            'risk_level': 'HIGH' if proba[1] > 0.7 else 'MEDIUM' if proba[1] > 0.4 else 'LOW'
        }
    
    def save(self, path: str):
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model not trained. Nothing to save.")
        
        model_data = {
            'pipeline': self.pipeline,
            'feature_names': self.feature_names,
            'model_type': self.model_type
        }
        
        joblib.dump(model_data, path)
        print(f"✅ Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'RedFlagClassifier':
        """Load trained model from disk."""
        model_data = joblib.load(path)
        
        classifier = cls(model_type=model_data['model_type'])
        classifier.pipeline = model_data['pipeline']
        classifier.feature_names = model_data['feature_names']
        classifier.is_trained = True
        
        print(f"✅ Model loaded from {path}")
        return classifier


def train_red_flag_classifier(
    profiles_path: str,
    model_save_path: str = 'data/models/red_flag_classifier.joblib',
    model_type: str = 'random_forest'
) -> RedFlagClassifier:
    """
    Convenience function to train red flag classifier from CSV.
    
    Args:
        profiles_path: Path to profiles CSV
        model_save_path: Where to save trained model
        model_type: Type of classifier
        
    Returns:
        Trained classifier
    """
    # Load data
    print(f"Loading profiles from {profiles_path}...")
    profiles = pd.read_csv(profiles_path)
    
    # Train classifier
    classifier = RedFlagClassifier(model_type=model_type)
    X, y = classifier.prepare_features(profiles)
    metrics = classifier.train(X, y)
    
    # Save model
    Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
    classifier.save(model_save_path)
    
    return classifier
