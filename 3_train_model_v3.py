"""
LinkedIn Compatibility Model - Part 3: Model Training
======================================================
Train a model to predict compatibility scores based on engineered features.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

# Import models
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

print("="*70)
print("🚀 LINKEDIN COMPATIBILITY MODEL - TRAINING")
print("="*70)

# ============================================
# 1. LOAD DATA
# ============================================
print("\n" + "─"*70)
print("📂 LOADING TRAINING DATA")
print("─"*70)

df = pd.read_csv("data/processed/training_pairs.csv")
print(f"✅ Loaded {len(df):,} training pairs")

# ============================================
# 2. PREPARE FEATURES
# ============================================
print("\n" + "─"*70)
print("🔧 PREPARING FEATURES")
print("─"*70)

# Encode categorical variables
le_seniority = LabelEncoder()
le_role = LabelEncoder()
le_industry = LabelEncoder()

# Combine all seniority values for consistent encoding
all_seniority = pd.concat([df['user_seniority'], df['target_seniority']])
le_seniority.fit(all_seniority)

# Combine all roles
all_roles = pd.concat([df['user_role'], df['target_role']])
le_role.fit(all_roles)

# Combine all industries
all_industries = pd.concat([df['user_industry'], df['target_industry']])
le_industry.fit(all_industries.astype(str))

# Apply encoding
df['user_seniority_enc'] = le_seniority.transform(df['user_seniority'])
df['target_seniority_enc'] = le_seniority.transform(df['target_seniority'])
df['user_role_enc'] = le_role.transform(df['user_role'])
df['target_role_enc'] = le_role.transform(df['target_role'])
df['user_industry_enc'] = le_industry.transform(df['user_industry'].astype(str))
df['target_industry_enc'] = le_industry.transform(df['target_industry'].astype(str))

# Create derived features
df['exp_gap'] = df['target_exp'] - df['user_exp']
df['seniority_gap'] = df['target_seniority_enc'] - df['user_seniority_enc']
df['connection_gap'] = df['target_connections'] - df['user_connections']
df['strength_gap'] = df['target_strength'] - df['user_strength']
df['same_role'] = (df['user_role'] == df['target_role']).astype(int)
df['same_industry'] = (df['user_industry'] == df['target_industry']).astype(int)

# Feature columns (ENHANCED v3 - includes new factors)
FEATURE_COLS = [
    # User features
    'user_exp', 'user_seniority_enc', 'user_connections', 'user_role_enc',
    'user_industry_enc', 'user_strength',
    # Target features
    'target_exp', 'target_seniority_enc', 'target_connections', 'target_role_enc',
    'target_industry_enc', 'target_strength',
    # Gap/interaction features
    'exp_gap', 'seniority_gap', 'connection_gap', 'strength_gap',
    'same_role', 'same_industry',
    # Pre-computed score components (v3 - 12 factors total)
    'mentorship_score', 'network_score', 'skill_learning_score',
    'role_synergy_score', 'goal_alignment_score', 'alumni_score', 
    'career_score', 'industry_score', 'geographic_score',
    'engagement_score', 'rising_star_score_calc'
    # Note: red_flag_multiplier applied to final score, not as feature
]

TARGET_COL = 'compatibility_score'

X = df[FEATURE_COLS].copy()
y = df[TARGET_COL].copy()

print(f"✅ Features: {len(FEATURE_COLS)}")
print(f"✅ Target: {TARGET_COL}")

# ============================================
# 3. TRAIN/TEST SPLIT
# ============================================
print("\n" + "─"*70)
print("✂️ SPLITTING DATA")
print("─"*70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"✅ Train: {len(X_train):,} samples")
print(f"✅ Test: {len(X_test):,} samples")

# ============================================
# 4. TRAIN MODELS
# ============================================
print("\n" + "─"*70)
print("🏋️ TRAINING MODELS")
print("─"*70)

results = {}

# --- XGBoost ---
if HAS_XGB:
    print("\n[1] Training XGBoost...")
    
    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    
    # Cross-validation
    cv_scores = cross_val_score(xgb_model, X_train, y_train, cv=5, scoring='r2')
    
    results['XGBoost'] = {
        'model': xgb_model,
        'predictions': y_pred_xgb,
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred_xgb)),
        'mae': mean_absolute_error(y_test, y_pred_xgb),
        'r2': r2_score(y_test, y_pred_xgb),
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }
    print(f"   ✅ XGBoost: R²={results['XGBoost']['r2']:.4f}, CV={results['XGBoost']['cv_mean']:.4f}±{results['XGBoost']['cv_std']:.4f}")

# --- LightGBM ---
if HAS_LGB:
    print("\n[2] Training LightGBM...")
    
    lgb_model = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    
    lgb_model.fit(X_train, y_train)
    y_pred_lgb = lgb_model.predict(X_test)
    
    # Cross-validation
    cv_scores = cross_val_score(lgb_model, X_train, y_train, cv=5, scoring='r2')
    
    results['LightGBM'] = {
        'model': lgb_model,
        'predictions': y_pred_lgb,
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred_lgb)),
        'mae': mean_absolute_error(y_test, y_pred_lgb),
        'r2': r2_score(y_test, y_pred_lgb),
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }
    print(f"   ✅ LightGBM: R²={results['LightGBM']['r2']:.4f}, CV={results['LightGBM']['cv_mean']:.4f}±{results['LightGBM']['cv_std']:.4f}")

# ============================================
# 5. EVALUATION
# ============================================
print("\n" + "="*70)
print("📈 MODEL EVALUATION")
print("="*70)

print(f"\n{'Model':<12} {'RMSE':<10} {'MAE':<10} {'R²':<10} {'CV R² (5-fold)':<15}")
print("-"*60)

best_model_name = None
best_r2 = -float('inf')

for name, res in results.items():
    cv_str = f"{res['cv_mean']:.4f} ± {res['cv_std']:.4f}"
    print(f"{name:<12} {res['rmse']:<10.4f} {res['mae']:<10.4f} {res['r2']:<10.4f} {cv_str:<15}")
    
    if res['r2'] > best_r2:
        best_r2 = res['r2']
        best_model_name = name

print("-"*60)
print(f"\n🏆 Best Model: {best_model_name}")

# ============================================
# 6. FEATURE IMPORTANCE
# ============================================
print("\n" + "─"*70)
print("📊 FEATURE IMPORTANCE")
print("─"*70)

best_model = results[best_model_name]['model']

importance = pd.DataFrame({
    'feature': FEATURE_COLS,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 15 Features:")
for i, row in importance.head(15).iterrows():
    bar = '█' * int(row['importance'] / importance['importance'].max() * 30)
    print(f"   {row['feature']:<25} {row['importance']:.4f} {bar}")

# ============================================
# 7. ERROR ANALYSIS
# ============================================
print("\n" + "─"*70)
print("🔍 ERROR ANALYSIS")
print("─"*70)

y_pred = results[best_model_name]['predictions']
errors = np.abs(y_test - y_pred)

print(f"\nPrediction Error Distribution:")
print(f"   Mean Error: {errors.mean():.2f}")
print(f"   Median Error: {np.median(errors):.2f}")
print(f"   90th Percentile: {np.percentile(errors, 90):.2f}")
print(f"   Max Error: {errors.max():.2f}")

# Percentage within thresholds
for threshold in [5, 10, 15]:
    pct = (errors <= threshold).mean() * 100
    print(f"   Within ±{threshold} points: {pct:.1f}%")

# ============================================
# 8. SAVE MODEL
# ============================================
print("\n" + "─"*70)
print("💾 SAVING MODEL")
print("─"*70)

import os
os.makedirs("data/models", exist_ok=True)

# Save model
model_path =  f"data/models/compatibility_model_v3.joblib"
joblib.dump(best_model, model_path)
print(f"✅ Model: {model_path}")

# Save encoders
encoders = {
    'seniority': le_seniority,
    'role': le_role,
    'industry': le_industry
}
joblib.dump(encoders, "data/models/encoders.joblib")
print("✅ Encoders: data/models/encoders.joblib")

# Save feature columns
with open("data/models/feature_columns_v3.txt", 'w') as f:
    f.write('\n'.join(FEATURE_COLS))
print("✅ Features: data/models/feature_columns_v2.txt")

# Save metadata
metadata = {
    'model_type': best_model_name,
    'features': FEATURE_COLS,
    'metrics': {
        'rmse': float(results[best_model_name]['rmse']),
        'mae': float(results[best_model_name]['mae']),
        'r2': float(results[best_model_name]['r2']),
        'cv_mean': float(results[best_model_name]['cv_mean']),
        'cv_std': float(results[best_model_name]['cv_std'])
    },
    'weight_distribution': {
        'mentorship_potential': 0.20,
        'network_value': 0.16,
        'skill_learning': 0.16,
        'role_synergy': 0.12,
        'goal_alignment': 0.05,
        'alumni_connection': 0.09,
        'career_advancement': 0.09,
        'industry_match': 0.07,
        'geographic_proximity': 0.03,
        'engagement_quality': 0.02,
        'rising_star': 0.01
    },
    'train_samples': len(X_train),
    'test_samples': len(X_test)
}

with open("data/models/model_metadata_v3.json", 'w') as f:
    json.dump(metadata, f, indent=2)
print("✅ Metadata: data/models/model_metadata_v2.json")

# ============================================
# SUMMARY
# ============================================
print("\n" + "="*70)
print("✅ TRAINING COMPLETE!")
print("="*70)

print(f"""
📊 Model Performance:
   • Model: {best_model_name}
   • R² Score: {best_r2:.4f} ({best_r2*100:.1f}% variance explained)
   • RMSE: {results[best_model_name]['rmse']:.2f} points
   • MAE: {results[best_model_name]['mae']:.2f} points
   • Cross-Val R²: {results[best_model_name]['cv_mean']:.4f} ± {results[best_model_name]['cv_std']:.4f}

📋 Weight Distribution (in scoring):
   • Mentorship Potential: 25%
   • Network Value: 20%
   • Skill Learning: 20%
   • Role Synergy: 15%
   • Career Advancement: 10%
   • Industry Match: 10%

🎯 Prediction Accuracy:
   • {((errors <= 5).mean()*100):.1f}% predictions within ±5 points
   • {((errors <= 10).mean()*100):.1f}% predictions within ±10 points

💾 Files Saved:
   • data/models/compatibility_model_v2.joblib
   • data/models/encoders.joblib
   • data/models/feature_columns_v2.txt
   • data/models/model_metadata_v2.json

🚀 Next: Run predict.py to test with your profile!
""")
