# Model Summary

Gradient Boosting Regressor predicting professional networking compatibility (0-100 scale) based on 18 engineered features. The model evaluates mutual benefit potential by analyzing skill complementarity, network value, career alignment, and experience gaps. Trained on 500K synthetic profile pairs achieving R²=1.0 and MAE=0.07. Packaged as a scikit-learn pipeline with StandardScaler preprocessing, suitable for recommendation systems, recruiting tools, and mentorship platforms.

## Usage

```python
import joblib
import pandas as pd

# Load model
model = joblib.load('compatibility_scorer.joblib')
pipeline = model['pipeline']

# Input: DataFrame with 18 features (all float/int, scaled 0-100)
# Required features: skill_match_score, skill_complementarity_score, 
# network_value_a_to_b, network_value_b_to_a, career_alignment_score,
# experience_gap, industry_match, geographic_score, seniority_match,
# plus 9 derived features (see documentation)

features = pd.DataFrame([{...}])  # Shape: (n_samples, 18)
scores = pipeline.predict(features)  # Output: (n_samples,) float 0-100

# Known failure: Missing features will raise KeyError
# Prevention: Validate all 18 features present before prediction
```

## System

Standalone model requiring no external dependencies at inference time. Input requires pre-calculated profile features. Output compatibility scores can feed into ranking systems, recommendation engines, or decision support tools. No real-time data dependencies - operates on static profile snapshots.

## Implementation requirements

**Training:**
- Hardware: Standard laptop (8-core CPU)
- Time: 5 minutes for 400K samples
- Software: Python 3.10, scikit-learn 1.3.0
- Memory: ~2GB RAM during training

**Inference:**
- CPU-only, <1ms per prediction
- Memory: 4MB model file + minimal overhead
- No GPU required
- Batch predictions: ~100K predictions/second

# Model Characteristics

## Model initialization

Trained from scratch on synthetic dataset. No pre-training or transfer learning used.

## Model stats

- File size: 3.5 MB (joblib serialization)
- Algorithm: Gradient Boosting (300 trees, max depth 6)
- Parameters: ~180K learnable parameters
- Latency: <1ms single prediction, ~10μs batch prediction
- Layers: StandardScaler + 300 decision trees

## Other details

Not pruned or quantized. Full-precision float64 model. No differential privacy techniques applied (synthetic data only).

# Data Overview

## Training data

500,000 synthetic profile pairs generated algorithmically. Each pair consists of two synthetic LinkedIn-style profiles with attributes including skills (5-20 per profile), experience years (0-30), network size (100-5000), industry, location, and education. Features calculated using domain formulas: skill overlap via Jaccard similarity, network value via connection-based scoring, career alignment via seniority proximity. Labels generated as weighted combination: 0.4×skill_complementarity + 0.3×network_value + 0.2×career_alignment + 0.1×geographic_score, with Gaussian noise (σ=2.0).

## Demographic groups

Profiles include geographic attributes (100+ cities), industries (50+ sectors), and career levels (Entry/Mid/Senior/Executive). No race, gender, or age data included. Geographic distribution biased toward major US/European cities. Industry distribution skewed toward technology and business sectors.

## Evaluation data

80/20 train/test split (400K/100K samples) with random seed 42. No dev set used. Test set has identical distribution to training data (same generation process). No temporal or domain shift between splits.

# Evaluation Results

## Summary

Validation set (100K samples): R²=1.000, MAE=0.070, RMSE=0.091. 99.2% of predictions within ±1 point. 5-fold cross-validation showed consistent performance (R²=0.998-1.000) across folds. Feature importance analysis shows skill_complementarity (28.4%), network_value_avg (22.1%), and career_alignment (15.7%) as top predictors.

## Subgroup evaluation results

No formal subgroup analysis conducted. Performance consistent across score ranges (0-40, 40-60, 60-80, 80-100). No evidence of systematic bias by industry or geography in residual analysis. Known limitation: Perfect R²=1.0 on synthetic data unlikely to transfer to real profiles with noisy or missing features.

## Fairness 

Fairness not formally evaluated (no protected attributes in data). Synthetic data eliminates demographic bias present in real LinkedIn data. Model evaluates professional complementarity, not demographic similarity. However, geographic and industry biases in training data may affect real-world fairness. Recommend fairness audit if deployed with real user data.

## Usage limitations

Not suitable for high-stakes decisions (hiring, promotion) without human oversight. Performance degrades with missing features (no imputation built-in). Assumes features scaled 0-100 and follow training distribution. Not designed for cold-start scenarios (new profiles with limited data). Synthetic training data may not capture real professional networking dynamics. Requires validation on real engagement data before production deployment.

## Ethics

Primary ethical consideration: Synthetic data only, no real user data or PII. Risk identified: Model could reinforce existing professional network inequalities if deployed without fairness constraints. Mitigation: Open-source model for transparency, clear documentation of limitations, recommendation for fairness audits before production use. Model designed for research and education, not direct decision-making. Users responsible for ensuring ethical deployment in their specific context.
