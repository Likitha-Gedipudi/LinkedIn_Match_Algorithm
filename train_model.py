"""
LinkedIn Compatibility Model Training
=====================================
Train a model to predict compatibility scores between LinkedIn profiles.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

# Check for XGBoost
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️ XGBoost not installed. Run: pip install xgboost")

# Check for LightGBM
try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    print("⚠️ LightGBM not installed. Run: pip install lightgbm")

print("="*60)
print("🚀 LinkedIn Compatibility Model Training")
print("="*60)

# ============================================
# 1. LOAD DATA
# ============================================
print("\n📂 Loading dataset...")

DATA_PATH = "data/processed/compatibility_pairs.csv"
SAMPLE_SIZE = 500_000  # Use subset for faster iteration (set to None for full data)

# Load data
df = pd.read_csv(DATA_PATH)
print(f"   Total records: {len(df):,}")

# Sample for faster training (optional)
if SAMPLE_SIZE and len(df) > SAMPLE_SIZE:
    df = df.sample(n=SAMPLE_SIZE, random_state=42)
    print(f"   Sampled to: {len(df):,} records")

# ============================================
# 2. FEATURE ENGINEERING
# ============================================
print("\n🔧 Preparing features...")

# Define feature columns
FEATURE_COLS = [
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

TARGET_COL = 'compatibility_score'

# Check for missing features
missing_cols = [col for col in FEATURE_COLS if col not in df.columns]
if missing_cols:
    print(f"   ⚠️ Missing columns: {missing_cols}")
    FEATURE_COLS = [col for col in FEATURE_COLS if col in df.columns]

print(f"   Features: {len(FEATURE_COLS)}")
print(f"   Target: {TARGET_COL}")

# Prepare X and y
X = df[FEATURE_COLS].copy()
y = df[TARGET_COL].copy()

# Handle missing values
X = X.fillna(0)

# Feature statistics
print(f"\n📊 Feature Statistics:")
print(X.describe().round(2))

print(f"\n🎯 Target Statistics:")
print(f"   Min: {y.min():.2f}")
print(f"   Max: {y.max():.2f}")
print(f"   Mean: {y.mean():.2f}")
print(f"   Std: {y.std():.2f}")

# ============================================
# 3. TRAIN/TEST SPLIT
# ============================================
print("\n✂️ Splitting data...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"   Train: {len(X_train):,} samples")
print(f"   Test: {len(X_test):,} samples")

# ============================================
# 4. TRAIN MODELS
# ============================================
print("\n🏋️ Training models...")

results = {}

# --- XGBoost ---
if HAS_XGB:
    print("\n   [1/2] Training XGBoost...")
    
    xgb_model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    
    results['XGBoost'] = {
        'model': xgb_model,
        'predictions': y_pred_xgb,
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred_xgb)),
        'mae': mean_absolute_error(y_test, y_pred_xgb),
        'r2': r2_score(y_test, y_pred_xgb)
    }
    print(f"      ✅ XGBoost trained!")

# --- LightGBM ---
if HAS_LGB:
    print("\n   [2/2] Training LightGBM...")
    
    lgb_model = lgb.LGBMRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    
    lgb_model.fit(X_train, y_train)
    y_pred_lgb = lgb_model.predict(X_test)
    
    results['LightGBM'] = {
        'model': lgb_model,
        'predictions': y_pred_lgb,
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred_lgb)),
        'mae': mean_absolute_error(y_test, y_pred_lgb),
        'r2': r2_score(y_test, y_pred_lgb)
    }
    print(f"      ✅ LightGBM trained!")

# ============================================
# 5. EVALUATE MODELS
# ============================================
print("\n" + "="*60)
print("📈 MODEL EVALUATION RESULTS")
print("="*60)

print(f"\n{'Model':<15} {'RMSE':<10} {'MAE':<10} {'R² Score':<10}")
print("-"*45)

best_model_name = None
best_r2 = -float('inf')

for name, res in results.items():
    print(f"{name:<15} {res['rmse']:<10.4f} {res['mae']:<10.4f} {res['r2']:<10.4f}")
    
    if res['r2'] > best_r2:
        best_r2 = res['r2']
        best_model_name = name

print("-"*45)
print(f"\n🏆 Best Model: {best_model_name} (R² = {best_r2:.4f})")

# ============================================
# 6. FEATURE IMPORTANCE
# ============================================
print("\n📊 Feature Importance (Best Model):")
print("-"*40)

best_model = results[best_model_name]['model']

if hasattr(best_model, 'feature_importances_'):
    importance = pd.DataFrame({
        'feature': FEATURE_COLS,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for _, row in importance.iterrows():
        bar = '█' * int(row['importance'] * 50)
        print(f"   {row['feature']:<30} {row['importance']:.4f} {bar}")

# ============================================
# 7. SAVE MODEL
# ============================================
print("\n💾 Saving model...")

MODEL_DIR = "data/models"
os.makedirs(MODEL_DIR, exist_ok=True)

model_path = os.path.join(MODEL_DIR, f"compatibility_model_{best_model_name.lower()}.joblib")
joblib.dump(best_model, model_path)
print(f"   Saved: {model_path}")

# Save feature list
feature_path = os.path.join(MODEL_DIR, "feature_columns.txt")
with open(feature_path, 'w') as f:
    f.write('\n'.join(FEATURE_COLS))
print(f"   Saved: {feature_path}")

# Save training metadata
metadata = {
    'model_type': best_model_name,
    'features': FEATURE_COLS,
    'metrics': {
        'rmse': results[best_model_name]['rmse'],
        'mae': results[best_model_name]['mae'],
        'r2': results[best_model_name]['r2']
    },
    'train_samples': len(X_train),
    'test_samples': len(X_test),
    'trained_at': datetime.now().isoformat()
}

import json
metadata_path = os.path.join(MODEL_DIR, "model_metadata.json")
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"   Saved: {metadata_path}")

# ============================================
# 8. QUICK TEST
# ============================================
print("\n🧪 Quick Prediction Test:")
print("-"*40)

# Test with sample data
sample = X_test.iloc[0:3]
predictions = best_model.predict(sample)
actuals = y_test.iloc[0:3].values

for i, (pred, actual) in enumerate(zip(predictions, actuals)):
    diff = abs(pred - actual)
    print(f"   Sample {i+1}: Predicted={pred:.2f}, Actual={actual:.2f}, Diff={diff:.2f}")

# ============================================
# SUMMARY
# ============================================
print("\n" + "="*60)
print("✅ TRAINING COMPLETE!")
print("="*60)
print(f"""
📊 Results Summary:
   • Best Model: {best_model_name}
   • R² Score: {best_r2:.4f} ({best_r2*100:.1f}% variance explained)
   • RMSE: {results[best_model_name]['rmse']:.4f}
   • MAE: {results[best_model_name]['mae']:.4f}
   
💾 Files Saved:
   • {model_path}
   • {feature_path}
   • {metadata_path}

🚀 Next Steps:
   1. Tune hyperparameters for better accuracy
   2. Try with full dataset (remove SAMPLE_SIZE limit)
   3. Integrate model into Chrome extension API
""")
