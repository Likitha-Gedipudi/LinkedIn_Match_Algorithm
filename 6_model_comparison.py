"""
Model Comparison - v2 vs v3
Compare basic model (7 factors) with enhanced model (12 factors)
"""

import pandas as pd
import joblib
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("🔬 MODEL COMPARISON: v2 (7 factors) vs v3 (12 factors)")
print("="*70)

# Load both models
print("\nLoading models...")
model_v2 = joblib.load("data/models/compatibility_model_v2.joblib")
model_v3 = joblib.load("data/models/compatibility_model_v3.joblib")
encoders = joblib.load("data/models/encoders.joblib")

print("✅ Both models loaded")

# Test profiles
YOUR_PROFILE = {
    'name': 'Likitha',
    'years_experience': 1,
    'seniority_level': 'entry',
    'connections': 600,
    'industry': 'Technology',
    'job_category': 'data_science',
    'skills': ['Python', 'SQL', 'Machine Learning'],
    'university': 'university at buffalo',
    'location': 'Buffalo, NY',
    'needs': ['mentorship', 'job referral'],
    'goals': ['Get promoted', 'Build network'],
    'can_offer': ['coding help', 'data analysis']
}

TEST_PROFILES = [
    {
        'name': 'Jayashree (Amazon BI)',
        'years_experience': 5,
        'seniority_level': 'mid',
        'connections': 700,
        'industry': 'Technology',
        'company': 'Amazon',
        'job_category': 'data_analytics',
        'skills': ['Python', 'SQL', 'AWS', 'Tableau'],
        'education_list': [{'school': 'university at buffalo'}],
        'location': 'Seattle, WA',
        'can_offer': ['mentorship', 'career advice', 'job referral'],
        'needs': ['leadership', 'project ideas'],
        'engagement_quality_score': 85.0,
        'red_flag_score': 5.0,
        'rising_star_score': 60.0,
        'undervalued_score': 40.0
    },
    {
        'name': 'Vani (Biomedical)',
        'years_experience': 2,
        'seniority_level': 'mid',
        'connections': 400,
        'industry': 'Healthcare',
        'company': 'HCLTech',
        'job_category': 'other',
        'skills': ['SAS', 'Research'],
        'education_list': [{'school': 'university at buffalo'}],
        'location': 'Buffalo, NY',
        'can_offer': ['research help'],
        'needs': ['collaboration'],
        'engagement_quality_score': 45.0,
        'red_flag_score': 10.0,
        'rising_star_score': 20.0,
        'undervalued_score': 30.0
    },
    {
        'name': 'Colin (Student)',
        'years_experience': 0,
        'seniority_level': 'entry',
        'connections': 300,
        'industry': 'Technology',
        'company': 'Student',
        'job_category': 'software_dev',
        'skills': ['Java', 'Python'],
        'education_list': [{'school': 'same btech clg'}],
        'location': 'Buffalo, NY',
        'can_offer': ['coding help'],
        'needs': ['mentorship', 'job search'],
        'engagement_quality_score': 65.0,
        'red_flag_score': 8.0,
        'rising_star_score': 75.0,  # High potential!
        'undervalued_score': 80.0
    }
]

# Scoring logic for both versions
PRESTIGIOUS = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 
               'netflix', 'tesla', 'uber', 'airbnb', 'stripe', 'linkedin']
SENIORITY_MAP = {'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3}
RELATED_ROLES = {
    'data_science': ['data_analytics', 'data_engineering', 'software_dev', 'product'],
    'data_analytics': ['data_science', 'data_engineering', 'product'],
    'software_dev': ['data_engineering', 'data_science', 'product'],
    'other': []
}

def calculate_scores_v2(user, target):
    """Calculate 7 component scores for v2 model"""
    scores = {}
    
    # 1. Mentorship
    exp_gap = target['years_experience'] - user['years_experience']
    if 3 <= exp_gap <= 10: scores['mentorship_score'] = 100
    elif exp_gap > 10: scores['mentorship_score'] = 70
    elif exp_gap > 0: scores['mentorship_score'] = 60
    else: scores['mentorship_score'] = 20
    
    # 2. Network
    conn = target['connections']
    if conn >= 5000: scores['network_score'] = 100
    elif conn >= 2000: scores['network_score'] = 85
    elif conn >= 1000: scores['network_score'] = 70
    elif conn >= 500: scores['network_score'] = 55
    else: scores['network_score'] = 40
    if any(p in str(target.get('company', '')).lower() for p in PRESTIGIOUS):
        scores['network_score'] = min(scores['network_score'] + 15, 100)
    
    # 3. Skill Learning
    user_skills = set([s.lower() for s in user['skills']])
    target_skills =set([s.lower() for s in target['skills']])
    new = len(target_skills - user_skills)
    if new >= 5: scores['skill_learning_score'] = 70
    else: scores['skill_learning_score'] = 40
    
    # 4. Role Synergy
    ur = user['job_category']
    tr = target['job_category']
    if ur == tr: scores['role_synergy_score'] = 100
    elif tr in RELATED_ROLES.get(ur, []): scores['role_synergy_score'] = 70
    else: scores['role_synergy_score'] = 40
    
    # 5. Alumni
    user_uni = user.get('university', '').lower()
    target_schools = [edu['school'].lower() for edu in target.get('education_list', []) if 'school' in edu]
    scores['alumni_score'] = 100 if user_uni in target_schools else 0
    
    # 6. Career
    sen_scores = {'entry': 30, 'mid': 50, 'senior': 75, 'executive': 95}
    scores['career_score'] = sen_scores.get(target['seniority_level'], 30)
    
    # 7. Industry
    scores['industry_score'] = 100 if user['industry'].lower() == target['industry'].lower() else 30
    
    return scores

def calculate_scores_v3(user, target):
    """Calculate 12 component scores for v3 model"""
    scores = calculate_scores_v2(user, target)  # Start with v2 scores
    
    # 8. Goal Alignment (NEW!)
    user_needs = set([str(n).lower() for n in user.get('needs', [])])
    target_offers = set([str(o).lower() for o in target.get('can_offer', [])])
    if user_needs and target_offers:
        overlap = user_needs & target_offers
        scores['goal_alignment_score'] = int((len(overlap) / len(user_needs)) * 100) if user_needs else 50
    else:
        scores['goal_alignment_score'] = 50
    
    # 9. Geographic Proximity (NEW!)
    user_loc = user.get('location', '').split(',')
    target_loc = target.get('location', '').split(',')
    if len(user_loc) == 2 and len(target_loc) == 2:
        if user_loc[0].strip().lower() == target_loc[0].strip().lower():
            scores['geographic_score'] = 100  # Same city!
        elif user_loc[1].strip().lower() == target_loc[1].strip().lower():
            scores['geographic_score'] = 70   # Same state
        else:
            scores['geographic_score'] = 40
    else:
        scores['geographic_score'] = 50
    
    # 10. Engagement Quality (NEW!)
    scores['engagement_score'] = float(target.get('engagement_quality_score', 50))
    
    # 11. Rising Star (NEW!)
    rising = float(target.get('rising_star_score', 0))
    hidden = float(target.get('undervalued_score', 0))
    scores['rising_star_score_calc'] = (rising + hidden) / 2
    
    return scores

def safe_transform(encoder, value):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    return 0

def predict_v2(user, target):
    """Predict using v2 model"""
    scores = calculate_scores_v2(user, target)
    
    # Calculate strengths
    user_strength = 50  # Simplified
    target_strength = 60
    
    features = {
        'user_exp': user['years_experience'],
        'user_seniority_enc': safe_transform(encoders['seniority'], user['seniority_level']),
        'user_connections': user['connections'],
        'user_role_enc': safe_transform(encoders['role'], user['job_category']),
        'user_industry_enc': safe_transform(encoders['industry'], user['industry']),
        'user_strength': user_strength,
        'target_exp': target['years_experience'],
        'target_seniority_enc': safe_transform(encoders['seniority'], target['seniority_level']),
        'target_connections': target['connections'],
        'target_role_enc': safe_transform(encoders['role'], target['job_category']),
        'target_industry_enc': safe_transform(encoders['industry'], target['industry']),
        'target_strength': target_strength,
        'exp_gap': target['years_experience'] - user['years_experience'],
        'seniority_gap': SENIORITY_MAP[target['seniority_level']] - SENIORITY_MAP[user['seniority_level']],
        'connection_gap': target['connections'] - user['connections'],
        'strength_gap': target_strength - user_strength,
        'same_role': 1 if user['job_category'] == target['job_category'] else 0,
        'same_industry': 1 if user['industry'].lower() == target['industry'].lower() else 0,
        **scores
    }
    
    X = pd.DataFrame([features])
    return model_v2.predict(X)[0], scores

def predict_v3(user, target):
    """Predict using v3 model"""
    scores = calculate_scores_v3(user, target)
    
    user_strength = 50
    target_strength = 60
    
    features = {
        'user_exp': user['years_experience'],
        'user_seniority_enc': safe_transform(encoders['seniority'], user['seniority_level']),
        'user_connections': user['connections'],
        'user_role_enc': safe_transform(encoders['role'], user['job_category']),
        'user_industry_enc': safe_transform(encoders['industry'], user['industry']),
        'user_strength': user_strength,
        'target_exp': target['years_experience'],
        'target_seniority_enc': safe_transform(encoders['seniority'], target['seniority_level']),
        'target_connections': target['connections'],
        'target_role_enc': safe_transform(encoders['role'], target['job_category']),
        'target_industry_enc': safe_transform(encoders['industry'], target['industry']),
        'target_strength': target_strength,
        'exp_gap': target['years_experience'] - user['years_experience'],
        'seniority_gap': SENIORITY_MAP[target['seniority_level']] - SENIORITY_MAP[user['seniority_level']],
        'connection_gap': target['connections'] - user['connections'],
        'strength_gap': target_strength - user_strength,
        'same_role': 1 if user['job_category'] == target['job_category'] else 0,
        'same_industry': 1 if user['industry'].lower() == target['industry'].lower() else 0,
        **scores
    }
    
    X = pd.DataFrame([features])
    score = model_v3.predict(X)[0]
    
    # Apply red flag penalty
    red_flag = float(target.get('red_flag_score', 0))
    if red_flag > 75: score *= 0.80
    elif red_flag > 50: score *= 0.90
    elif red_flag > 25: score *= 0.95
    
    return score, scores

# Run comparisons
print("\n" + "="*70)
print("📊 COMPARISON RESULTS")
print("="*70)

for target in TEST_PROFILES:
    print(f"\n{'='*70}")
    print(f"🎯 Target: {target['name']}")
    print(f"{'='*70}")
    
    v2_score, v2_scores = predict_v2(YOUR_PROFILE, target)
    v3_score, v3_scores = predict_v3(YOUR_PROFILE, target)
    
    print(f"\n📊 SCORES:")
    print(f"   v2 (7 factors):  {v2_score:.1f}/100")
    print(f"   v3 (12 factors): {v3_score:.1f}/100")
    print(f"   Difference:      {v3_score - v2_score:+.1f} points")
    
    print(f"\n🆕 NEW v3 FACTORS:")
    print(f"   Goal Alignment:      {v3_scores['goal_alignment_score']:.0f}/100")
    print(f"   Geographic Proximity: {v3_scores['geographic_score']:.0f}/100")
    print(f"   Engagement Quality:   {v3_scores['engagement_score']:.0f}/100")
    print(f"   Rising Star:         {v3_scores['rising_star_score_calc']:.0f}/100")
    
    # Determine why score changed
    if v3_score > v2_score + 2:
        print(f"   ✅ v3 scores HIGHER - benefits from new factors!")
    elif v3_score < v2_score - 2:
        print(f"   ⚠️  v3 scores LOWER - red flags or poor engagement")
    else:
        print(f"   ➡️  Similar scores - new factors balanced")

print("\n" + "="*70)
print("✅ Comparison Complete!")
print("="*70)
