"""
XGBoost Model API for LinkedIn Compatibility Scoring
=====================================================
Flask API that serves the trained XGBoost model for real-time predictions.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Load model and encoders
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'compatibility_model_v3.joblib')
ENCODERS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'encoders.joblib')

print("Loading XGBoost model...")
model = joblib.load(MODEL_PATH)
encoders = joblib.load(ENCODERS_PATH)
print("✅ Model loaded successfully!")

# Constants
PRESTIGIOUS = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 
               'netflix', 'tesla', 'uber', 'airbnb', 'stripe', 'linkedin',
               'nvidia', 'adobe', 'salesforce', 'oracle', 'ibm']
SENIORITY_MAP = {'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3}
RELATED_ROLES = {
    'data_science': ['data_analytics', 'data_engineering', 'software_dev', 'product'],
    'data_analytics': ['data_science', 'data_engineering', 'product'],
    'software_dev': ['data_engineering', 'data_science', 'product'],
    'other': []
}


def safe_transform(encoder, value, default=0):
    """Safely transform a value using the encoder"""
    try:
        if value in encoder.classes_:
            return encoder.transform([value])[0]
        return default
    except:
        return default


def infer_job_category(headline, about=''):
    """Infer job category from headline/about"""
    text = f"{headline} {about}".lower()
    
    categories = {
        'data_science': ['data scientist', 'machine learning', 'ml engineer', 'ai', 'data science'],
        'data_analytics': ['data analyst', 'business intelligence', 'bi analyst', 'analytics'],
        'data_engineering': ['data engineer', 'etl', 'pipeline', 'spark engineer'],
        'software_dev': ['software engineer', 'developer', 'sde', 'programmer', 'full stack'],
        'product': ['product manager', 'pm', 'product owner'],
        'design': ['designer', 'ux', 'ui'],
        'executive': ['ceo', 'cto', 'director', 'vp']
    }
    
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
    return 'other'


def infer_seniority(title, years_exp):
    """Infer seniority from job title and experience"""
    title_lower = str(title).lower()
    if any(word in title_lower for word in ['ceo', 'cto', 'cfo', 'vp', 'director', 'head of']):
        return 'executive'
    elif any(word in title_lower for word in ['senior', 'lead', 'principal', 'staff']):
        return 'senior'
    elif any(word in title_lower for word in ['junior', 'associate', 'intern']) or years_exp < 2:
        return 'entry'
    else:
        return 'mid'


def calculate_scores(user, target):
    """Calculate all 12 component scores for v3 model"""
    scores = {}
    
    # 1. Mentorship (20%)
    exp_gap = target.get('years_experience', 0) - user.get('years_experience', 0)
    if 3 <= exp_gap <= 10: scores['mentorship_score'] = 100
    elif exp_gap > 10: scores['mentorship_score'] = 70
    elif exp_gap > 0: scores['mentorship_score'] = 60
    else: scores['mentorship_score'] = 20
    
    # 2. Network (16%)
    conn = target.get('connections', 0)
    if conn >= 5000: scores['network_score'] = 100
    elif conn >= 2000: scores['network_score'] = 85
    elif conn >= 1000: scores['network_score'] = 70
    elif conn >= 500: scores['network_score'] = 55
    else: scores['network_score'] = 40
    
    company = str(target.get('company', '')).lower()
    if any(p in company for p in PRESTIGIOUS):
        scores['network_score'] = min(scores['network_score'] + 15, 100)
    
    # 3. Skill Learning (16%)
    user_skills = set([s.lower() for s in user.get('skills', [])])
    target_skills = set([s.lower() for s in target.get('skills', [])])
    new_skills = len(target_skills - user_skills)
    if new_skills >= 5: scores['skill_learning_score'] = 70
    elif new_skills >= 3: scores['skill_learning_score'] = 50
    else: scores['skill_learning_score'] = 40
    
    # 4. Role Synergy (12%)
    ur = user.get('job_category', 'other')
    tr = target.get('job_category', 'other')
    if ur == tr: scores['role_synergy_score'] = 100
    elif tr in RELATED_ROLES.get(ur, []): scores['role_synergy_score'] = 70
    else: scores['role_synergy_score'] = 40
    
    # 5. Goal Alignment (5%)
    user_needs = set([str(n).lower() for n in user.get('needs', [])])
    target_offers = set([str(o).lower() for o in target.get('can_offer', [])])
    if user_needs and target_offers:
        overlap = user_needs & target_offers
        scores['goal_alignment_score'] = int((len(overlap) / len(user_needs)) * 100) if user_needs else 50
    else:
        scores['goal_alignment_score'] = 50
    
    # 6. Alumni (9%)
    user_uni = str(user.get('university', '')).lower()
    target_uni = str(target.get('university', '')).lower()
    scores['alumni_score'] = 100 if (user_uni and target_uni and (user_uni in target_uni or target_uni in user_uni)) else 0
    
    # 7. Career (9%)
    sen_scores = {'entry': 30, 'mid': 50, 'senior': 75, 'executive': 95}
    scores['career_score'] = sen_scores.get(target.get('seniority_level', 'entry'), 30)
    
    # 8. Industry (7%)
    scores['industry_score'] = 100 if user.get('industry', '').lower() == target.get('industry', '').lower() else 30
    
    # 9. Geographic (3%)
    user_loc = user.get('location', '').split(',')
    target_loc = target.get('location', '').split(',')
    if len(user_loc) >= 1 and len(target_loc) >= 1:
        if user_loc[0].strip().lower() == target_loc[0].strip().lower():
            scores['geographic_score'] = 100
        elif len(user_loc) > 1 and len(target_loc) > 1 and user_loc[-1].strip().lower() == target_loc[-1].strip().lower():
            scores['geographic_score'] = 70
        else:
            scores['geographic_score'] = 40
    else:
        scores['geographic_score'] = 50
    
    # 10. Engagement (2%)
    scores['engagement_score'] = float(target.get('engagement_quality_score', 50))
    
    # 11. Rising Star (1%)
    rising = float(target.get('rising_star_score', 30))
    hidden = float(target.get('undervalued_score', 30))
    scores['rising_star_score_calc'] = (rising + hidden) / 2
    
    return scores


def predict_compatibility(user_profile, target_profile):
    """Run XGBoost prediction"""
    
    # Infer missing fields
    if 'job_category' not in user_profile:
        user_profile['job_category'] = infer_job_category(
            user_profile.get('headline', ''), 
            user_profile.get('about', '')
        )
    
    if 'job_category' not in target_profile:
        target_profile['job_category'] = infer_job_category(
            target_profile.get('headline', ''), 
            target_profile.get('about', '')
        )
    
    if 'seniority_level' not in target_profile:
        target_profile['seniority_level'] = infer_seniority(
            target_profile.get('headline', ''),
            target_profile.get('years_experience', 0)
        )
    
    # Calculate component scores
    scores = calculate_scores(user_profile, target_profile)
    
    # Build feature vector
    user_strength = 50
    target_strength = 60
    
    features = {
        'user_exp': user_profile.get('years_experience', 0),
        'user_seniority_enc': safe_transform(encoders['seniority'], user_profile.get('seniority_level', 'entry')),
        'user_connections': user_profile.get('connections', 0),
        'user_role_enc': safe_transform(encoders['role'], user_profile.get('job_category', 'other')),
        'user_industry_enc': safe_transform(encoders['industry'], user_profile.get('industry', 'Technology')),
        'user_strength': user_strength,
        'target_exp': target_profile.get('years_experience', 0),
        'target_seniority_enc': safe_transform(encoders['seniority'], target_profile.get('seniority_level', 'entry')),
        'target_connections': target_profile.get('connections', 0),
        'target_role_enc': safe_transform(encoders['role'], target_profile.get('job_category', 'other')),
        'target_industry_enc': safe_transform(encoders['industry'], target_profile.get('industry', 'Technology')),
        'target_strength': target_strength,
        'exp_gap': target_profile.get('years_experience', 0) - user_profile.get('years_experience', 0),
        'seniority_gap': SENIORITY_MAP.get(target_profile.get('seniority_level', 'entry'), 0) - SENIORITY_MAP.get(user_profile.get('seniority_level', 'entry'), 0),
        'connection_gap': target_profile.get('connections', 0) - user_profile.get('connections', 0),
        'strength_gap': target_strength - user_strength,
        'same_role': 1 if user_profile.get('job_category') == target_profile.get('job_category') else 0,
        'same_industry': 1 if user_profile.get('industry', '').lower() == target_profile.get('industry', '').lower() else 0,
        **scores
    }
    
    # Create DataFrame and predict
    X = pd.DataFrame([features])
    
    # Ensure columns are in correct order
    expected_cols = model.feature_names_in_
    X = X[expected_cols]
    
    # Predict
    score = float(model.predict(X)[0])
    
    # Apply red flag penalty
    red_flag = float(target_profile.get('red_flag_score', 0))
    multiplier = 1.0
    if red_flag > 75: multiplier = 0.80
    elif red_flag > 50: multiplier = 0.90
    elif red_flag > 25: multiplier = 0.95
    
    final_score = score * multiplier
    
    return {
        'score': round(final_score, 1),
        'raw_score': round(score, 1),
        'red_flag_multiplier': multiplier,
        'breakdown': scores,
        'model': 'xgboost_v3'
    }


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'xgboost_v3',
        'features': len(model.feature_names_in_)
    })


@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction endpoint"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_profile = data.get('userProfile')
        target_profile = data.get('targetProfile')
        
        if not user_profile or not target_profile:
            return jsonify({'error': 'Missing userProfile or targetProfile'}), 400
        
        result = predict_compatibility(user_profile, target_profile)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in prediction: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
