"""
Production-grade Compatibility Scorer.
Predicts compatibility scores between professional pairs.
"""

import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not available, using GradientBoosting instead")

import warnings
warnings.filterwarnings('ignore')


class CompatibilityScorer:
    """
    Production-ready regressor for predicting compatibility scores.
    
    Features:
    - XGBoost/GradientBoosting pipeline
    - Feature engineering from profile pairs
    - Model serialization
    - Production inference API
    """
    
    def __init__(self, model_type: str = 'xgboost'):
        """
        Initialize scorer.
        
        Args:
            model_type: 'xgboost', 'gradient_boosting', or 'random_forest'
        """
        if model_type == 'xgboost' and not XGBOOST_AVAILABLE:
            model_type = 'gradient_boosting'
            
        self.model_type = model_type
        self.pipeline = None
        self.feature_names = None
        self.is_trained = False
        
    def _create_pipeline(self) -> Pipeline:
        """Create sklearn pipeline with preprocessing and model."""
        if self.model_type == 'xgboost':
            model = XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                min_samples_split=10,
                subsample=0.8,
                random_state=42
            )
        else:  # random_forest
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                random_state=42,
                n_jobs=-1
            )
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', model)
        ])
        
        return pipeline
    
    def prepare_features(self, pairs_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extract features for compatibility prediction.
        
        Args:
            pairs_df: DataFrame with compatibility pairs
            
        Returns:
            X: Feature matrix
            y: Target scores
        """
        features = pd.DataFrame()
        
        # Use existing compatibility features
        feature_cols = [
            'skill_match_score',
            'skill_complementarity_score',
            'network_value_a_to_b',
            'network_value_b_to_a',
            'career_alignment_score',
            'experience_gap',
            'industry_match',
            'geographic_score',
            'seniority_match'
        ]
        
        for col in feature_cols:
            if col in pairs_df.columns:
                features[col] = pairs_df[col]
            else:
                features[col] = 0
        
        # Engineered features
        features['network_value_avg'] = (features['network_value_a_to_b'] + 
                                         features['network_value_b_to_a']) / 2
        features['network_value_diff'] = abs(features['network_value_a_to_b'] - 
                                             features['network_value_b_to_a'])
        
        features['skill_total'] = features['skill_match_score'] + features['skill_complementarity_score']
        features['skill_balance'] = features['skill_match_score'] * features['skill_complementarity_score'] / 100
        
        features['exp_gap_squared'] = features['experience_gap'] ** 2
        features['is_mentorship_gap'] = ((features['experience_gap'] >= 3) & 
                                        (features['experience_gap'] <= 7)).astype(int)
        features['is_peer'] = (features['experience_gap'] <= 2).astype(int)
        
        # Interaction terms
        features['skill_x_network'] = features['skill_complementarity_score'] * features['network_value_avg'] / 100
        features['career_x_industry'] = features['career_alignment_score'] * features['industry_match'] / 100
        
        # Target
        if 'compatibility_score' in pairs_df.columns:
            y = pairs_df['compatibility_score']
        else:
            # Fallback: compute weighted average
            y = (
                features['skill_complementarity_score'] * 0.4 +
                features['network_value_avg'] * 0.3 +
                features['career_alignment_score'] * 0.2 +
                features['geographic_score'] * 0.1
            )
        
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
        Train the compatibility scorer.
        
        Args:
            X: Feature matrix
            y: Target scores
            test_size: Proportion for test set
            validate: Whether to run cross-validation
            
        Returns:
            Dictionary with metrics
        """
        print(f"Training {self.model_type} compatibility scorer...")
        print(f"Dataset: {len(X)} samples, {X.shape[1]} features")
        print(f"Target range: {y.min():.1f} - {y.max():.1f}, mean: {y.mean():.1f}")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Create and train pipeline
        self.pipeline = self._create_pipeline()
        self.pipeline.fit(X_train, y_train)
        
        # Predictions
        y_pred = self.pipeline.predict(X_test)
        
        # Metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2_score': r2,
            'test_size': len(X_test),
            'train_size': len(X_train)
        }
        
        print(f"\n✅ Training Complete!")
        print(f"  • R² Score: {r2:.3f}")
        print(f"  • RMSE: {rmse:.3f}")
        print(f"  • MAE: {mae:.3f}")
        
        # Cross-validation
        if validate:
            print(f"\n🔄 Running 5-fold cross-validation...")
            cv_scores = cross_val_score(
                self.pipeline, X, y, cv=5, scoring='r2', n_jobs=-1
            )
            metrics['cv_r2_mean'] = cv_scores.mean()
            metrics['cv_r2_std'] = cv_scores.std()
            print(f"  • CV R²: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        
        # Feature importance
        if hasattr(self.pipeline.named_steps['regressor'], 'feature_importances_'):
            importances = self.pipeline.named_steps['regressor'].feature_importances_
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
        Predict compatibility scores.
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of predicted scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = self.pipeline.predict(X)
        # Clip to valid range [0, 100]
        return np.clip(predictions, 0, 100)
    
    def predict_single(self, pair_features: pd.Series) -> Dict[str, any]:
        """
        Predict compatibility for a single pair (production API).
        
        Args:
            pair_features: Features for one pair
            
        Returns:
            Dictionary with prediction and metadata
        """
        X, _ = self.prepare_features(pd.DataFrame([pair_features]))
        
        score = float(self.predict(X)[0])
        
        return {
            'compatibility_score': score,
            'tier': 'EXCELLENT' if score >= 80 else 'GOOD' if score >= 60 else 'MODERATE' if score >= 40 else 'LOW',
            'recommendation': 'Connect immediately' if score >= 80 else 
                            'Worth considering' if score >= 60 else
                            'Evaluate carefully' if score >= 40 else
                            'Low priority'
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
    def load(cls, path: str) -> 'CompatibilityScorer':
        """Load trained model from disk."""
        model_data = joblib.load(path)
        
        scorer = cls(model_type=model_data['model_type'])
        scorer.pipeline = model_data['pipeline']
        scorer.feature_names = model_data['feature_names']
        scorer.is_trained = True
        
        print(f"✅ Model loaded from {path}")
        return scorer


def train_compatibility_scorer(
    pairs_path: str,
    model_save_path: str = 'data/models/compatibility_scorer.joblib',
    model_type: str = 'xgboost'
) -> CompatibilityScorer:
    """
    Convenience function to train compatibility scorer from CSV.
    
    Args:
        pairs_path: Path to pairs CSV
        model_save_path: Where to save trained model
        model_type: Type of regressor
        
    Returns:
        Trained scorer
    """
    # Load data
    print(f"Loading pairs from {pairs_path}...")
    pairs = pd.read_csv(pairs_path)
    
    # Train scorer
    scorer = CompatibilityScorer(model_type=model_type)
    X, y = scorer.prepare_features(pairs)
    metrics = scorer.train(X, y)
    
    # Save model
    Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
    scorer.save(model_save_path)
    
    return scorer
