#!/usr/bin/env python3
"""
Local Model Testing Script
Tests the trained model's accuracy, performance, and edge cases locally.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import pandas as pd
import numpy as np
import time
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
MODEL_PATH = Path("data/models/compatibility_scorer.joblib")
DATA_PATH = Path("data/processed/compatibility_pairs_enhanced.csv")


def load_model():
    """Load the trained model."""
    print("="*80)
    print("Loading Model...")
    print("="*80)
    
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    
    model_data = joblib.load(MODEL_PATH)
    pipeline = model_data['pipeline']
    feature_names = model_data['feature_names']
    model_type = model_data['model_type']
    
    print(f"✅ Model loaded: {model_type}")
    print(f"Features: {len(feature_names)}")
    print(f"Model size: {MODEL_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    
    return pipeline, feature_names, model_type


def load_test_data(feature_names, n_samples=1000):
    """Load and prepare test data."""
    print("\n" + "="*80)
    print("Loading Test Data...")
    print("="*80)
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data not found at {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)
    
    # Sample test data
    test_df = df.sample(n=min(n_samples, len(df)), random_state=42)
    
    # Extract features
    X_test = test_df[feature_names]
    y_test = test_df['compatibility_score']
    
    print(f"✅ Loaded {len(test_df)} test samples")
    print(f"Score distribution: mean={y_test.mean():.1f}, std={y_test.std():.1f}")
    
    return X_test, y_test, test_df


def test_model_accuracy(pipeline, X_test, y_test):
    """Test model prediction accuracy."""
    print("\n" + "="*80)
    print("TEST 1: Model Accuracy")
    print("="*80)
    
    # Make predictions
    start_time = time.time()
    y_pred = pipeline.predict(X_test)
    prediction_time = time.time() - start_time
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Error distribution
    errors = np.abs(y_test - y_pred)
    
    print(f"\n📊 Accuracy Metrics:")
    print(f"  • R² Score: {r2:.4f}")
    print(f"  • Mean Absolute Error (MAE): {mae:.3f}")
    print(f"  • Root Mean Squared Error (RMSE): {rmse:.3f}")
    print(f"  • Max Error: {errors.max():.3f}")
    print(f"  • 95th Percentile Error: {np.percentile(errors, 95):.3f}")
    
    print(f"\n⚡ Performance:")
    print(f"  • Total Prediction Time: {prediction_time:.3f}s")
    print(f"  • Time per Prediction: {prediction_time/len(X_test)*1000:.3f}ms")
    print(f"  • Predictions/Second: {len(X_test)/prediction_time:.0f}")
    
    # Score distribution
    print(f"\n📈 Score Distribution:")
    print(f"  • Actual   - Mean: {y_test.mean():.1f}, Std: {y_test.std():.1f}")
    print(f"  • Predicted - Mean: {y_pred.mean():.1f}, Std: {y_pred.std():.1f}")
    
    # Prediction accuracy by score range
    print(f"\n🎯 Accuracy by Score Range:")
    for low, high in [(0, 40), (40, 60), (60, 80), (80, 100)]:
        mask = (y_test >= low) & (y_test < high)
        if mask.sum() > 0:
            range_mae = mean_absolute_error(y_test[mask], y_pred[mask])
            print(f"  • {low}-{high}: MAE={range_mae:.3f} (n={mask.sum()})")
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'predictions': y_pred,
        'actuals': y_test,
        'errors': errors
    }


def test_edge_cases(pipeline, feature_names):
    """Test model behavior on edge cases."""
    print("\n" + "="*80)
    print("TEST 2: Edge Cases")
    print("="*80)
    
    test_cases = [
        {
            'name': 'All Zeros',
            'data': {feat: 0.0 for feat in feature_names}
        },
        {
            'name': 'All Max (100s)',
            'data': {feat: 100.0 for feat in feature_names}
        },
        {
            'name': 'High Skills, Low Network',
            'data': {
                **{feat: 50.0 for feat in feature_names},
                'skill_complementarity_score': 95.0,
                'skill_match_score': 90.0,
                'network_value_avg': 10.0
            }
        },
        {
            'name': 'Low Skills, High Network',
            'data': {
                **{feat: 50.0 for feat in feature_names},
                'skill_complementarity_score': 15.0,
                'skill_match_score': 10.0,
                'network_value_avg': 95.0
            }
        }
    ]
    
    for test_case in test_cases:
        X = pd.DataFrame([test_case['data']])
        score = pipeline.predict(X)[0]
        print(f"\n{test_case['name']}:")
        print(f"  Score: {score:.1f}/100")
        
        if score < 0 or score > 100:
            print(f"  ⚠️  WARNING: Score out of bounds!")
        else:
            print(f"  ✅ Score within valid range")


def test_feature_importance(pipeline, feature_names):
    """Analyze feature importance."""
    print("\n" + "="*80)
    print("TEST 3: Feature Importance")
    print("="*80)
    
    try:
        # Extract model from pipeline
        regressor = pipeline.named_steps['regressor']
        
        if hasattr(regressor, 'feature_importances_'):
            importances = regressor.feature_importances_
            
            # Create importance DataFrame
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            print("\n📊 Top 10 Most Important Features:")
            for idx, row in importance_df.head(10).iterrows():
                print(f"  {row['feature']:35s}: {row['importance']:.4f} ({row['importance']*100:.1f}%)")
            
            # Check if any features are unused
            unused = importance_df[importance_df['importance'] < 0.001]
            if len(unused) > 0:
                print(f"\n⚠️  {len(unused)} features with very low importance (<0.1%):")
                for feat in unused['feature'].values:
                    print(f"    • {feat}")
            
            return importance_df
        else:
            print("⚠️  Model does not support feature importance")
            return None
            
    except Exception as e:
        print(f"❌ Error calculating feature importance: {e}")
        return None


def test_inference_speed(pipeline, feature_names, n_runs=100):
    """Test inference speed under different conditions."""
    print("\n" + "="*80)
    print("TEST 4: Inference Speed")
    print("="*80)
    
    # Generate random test data
    X_single = pd.DataFrame([{feat: np.random.rand() * 100 for feat in feature_names}])
    X_batch_10 = pd.DataFrame([{feat: np.random.rand() * 100 for feat in feature_names} for _ in range(10)])
    X_batch_100 = pd.DataFrame([{feat: np.random.rand() * 100 for feat in feature_names} for _ in range(100)])
    
    # Single prediction
    times_single = []
    for _ in range(n_runs):
        start = time.time()
        _ = pipeline.predict(X_single)
        times_single.append((time.time() - start) * 1000)
    
    # Batch of 10
    times_batch_10 = []
    for _ in range(n_runs):
        start = time.time()
        _ = pipeline.predict(X_batch_10)
        times_batch_10.append((time.time() - start) * 1000)
    
    # Batch of 100
    times_batch_100 = []
    for _ in range(n_runs):
        start = time.time()
        _ = pipeline.predict(X_batch_100)
        times_batch_100.append((time.time() - start) * 1000)
    
    print(f"\n⚡ Inference Latency (ms) over {n_runs} runs:")
    print(f"\nSingle Prediction:")
    print(f"  • Mean: {np.mean(times_single):.3f}ms")
    print(f"  • Median: {np.median(times_single):.3f}ms")
    print(f"  • P95: {np.percentile(times_single, 95):.3f}ms")
    print(f"  • P99: {np.percentile(times_single, 99):.3f}ms")
    
    print(f"\nBatch 10:")
    print(f"  • Mean: {np.mean(times_batch_10):.3f}ms")
    print(f"  • Per prediction: {np.mean(times_batch_10)/10:.3f}ms")
    
    print(f"\nBatch 100:")
    print(f"  • Mean: {np.mean(times_batch_100):.3f}ms")
    print(f"  • Per prediction: {np.mean(times_batch_100)/100:.3f}ms")
    
    throughput = 100 / (np.mean(times_batch_100) / 1000)
    print(f"\n🚀 Throughput: {throughput:.0f} predictions/second")


def test_prediction_consistency(pipeline, feature_names, n_runs=10):
    """Test if model produces consistent predictions."""
    print("\n" + "="*80)
    print("TEST 5: Prediction Consistency")
    print("="*80)
    
    # Same input, multiple predictions
    X_test = pd.DataFrame([{feat: 50.0 for feat in feature_names}])
    
    predictions = []
    for _ in range(n_runs):
        pred = pipeline.predict(X_test)[0]
        predictions.append(pred)
    
    std = np.std(predictions)
    
    print(f"\nSame input, {n_runs} predictions:")
    print(f"  • All predictions: {predictions}")
    print(f"  • Std Dev: {std:.6f}")
    
    if std < 1e-10:
        print("  ✅ Model is deterministic")
    else:
        print("  ⚠️  Model shows variability")


def generate_summary_report(results, model_type):
    """Generate summary report."""
    print("\n" + "="*80)
    print("📋 SUMMARY REPORT")
    print("="*80)
    
    print(f"\n🤖 Model: {model_type}")
    print(f"📁 Model File: {MODEL_PATH}")
    print(f"💾 Model Size: {MODEL_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    
    print(f"\n📊 Performance Metrics:")
    print(f"  • R² Score: {results['r2']:.4f}")
    print(f"  • MAE: {results['mae']:.3f}")
    print(f"  • RMSE: {results['rmse']:.3f}")
    
    print(f"\n✅ Model Status:")
    if results['r2'] > 0.95:
        print("  ✅ Excellent accuracy")
    elif results['r2'] > 0.85:
        print("  ✅ Good accuracy")
    elif results['r2'] > 0.70:
        print("  ⚠️  Acceptable accuracy")
    else:
        print("  ❌ Low accuracy - needs improvement")
    
    if results['mae'] < 5:
        print("  ✅ Low prediction error")
    elif results['mae'] < 10:
        print("  ⚠️  Moderate prediction error")
    else:
        print("  ❌ High prediction error")
    
    print("\n" + "="*80)


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*80)
    print("🧪 MODEL TESTING SUITE")
    print("="*80)
    
    try:
        # Load model
        pipeline, feature_names, model_type = load_model()
        
        # Load test data
        X_test, y_test, test_df = load_test_data(feature_names, n_samples=1000)
        
        # Run tests
        accuracy_results = test_model_accuracy(pipeline, X_test, y_test)
        test_edge_cases(pipeline, feature_names)
        test_feature_importance(pipeline, feature_names)
        test_inference_speed(pipeline, feature_names)
        test_prediction_consistency(pipeline, feature_names)
        
        # Generate summary
        generate_summary_report(accuracy_results, model_type)
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        
        return accuracy_results
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    run_all_tests()
