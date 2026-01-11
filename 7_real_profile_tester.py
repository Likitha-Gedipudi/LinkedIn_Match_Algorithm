"""
Real LinkedIn Profile Tester - v3 Model
========================================
Manually test the enhanced model with real LinkedIn profiles.

USAGE:
1. Go to a LinkedIn profile
2. Copy the profile data (manually or save as JSON)
3. Paste into this script
4. Get instant compatibility prediction!

Note: This script doesn't scrape - it analyzes data you provide.
"""

import pandas as pd
import joblib
import json
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("🔬 REAL LINKEDIN PROFILE TESTER - Enhanced Model v3")
print("="*70)

# Load v3 model
model = joblib.load("data/models/compatibility_model_v3.joblib")
encoders = joblib.load("data/models/encoders.joblib")
print("\n✅ Enhanced model v3 loaded")

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

# ============================================
# YOUR PROFILE (UPDATE THIS!)
# ============================================
YOUR_PROFILE = {
    'name': 'Likitha',
    'years_experience': 1,
    'seniority_level': 'entry',
    'connections': 600,
    'industry': 'Technology',
    'job_category': 'data_science',
    'skills': ['Python', 'SQL', 'Machine Learning', 'Data Analysis'],
    'university': 'university at buffalo',
    'location': 'Buffalo, NY',
    'needs': ['mentorship', 'job referral', 'career guidance'],
    'can_offer': ['coding help', 'data analysis', 'python tutoring']
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def parse_years_experience(text):
    """Extract years of experience from text"""
    # Look for patterns like "5 years", "5+ years", "5-7 years"
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\s*-\s*\d+\s*(?:years?|yrs?)'
    ]
    for pattern in patterns:
        match = re.search(pattern, str(text).lower())
        if match:
            return int(match.group(1))
    return 1  # Default

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

def infer_job_category(headline, about=''):
    """Infer job category from headline/about"""
    text = f"{headline} {about}".lower()
    
    categories = {
        'data_science': ['data scientist', 'machine learning', 'ml engineer', 'ai', 'data science'],
        'data_analytics': ['data analyst', 'business intelligence', 'bi', 'analytics'],
        'data_engineering': ['data engineer', 'etl', 'pipeline', 'spark'],
        'software_dev': ['software engineer', 'developer', 'sde', 'programmer', 'full stack'],
        'product': ['product manager', 'pm', 'product owner'],
        'design': ['designer', 'ux', 'ui'],
        'executive': ['ceo', 'cto', 'director', 'vp']
    }
    
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
    return 'other'

def estimate_engagement(has_posts=True, has_recent_activity=True):
    """Estimate engagement quality (0-100)"""
    score = 50  # Baseline
    if has_posts: score += 20
    if has_recent_activity: score += 15
    return min(score, 100)

def estimate_red_flags(profile_data):
    """Estimate red flag score based on profile"""
    score = 0
    
    # Job hopping (many short stints)
    if 'experience_count' in profile_data and profile_data['experience_count'] > 8:
        score += 25
    
    # Sparse profile
    if not profile_data.get('about') or len(str(profile_data.get('about', ''))) < 50:
        score += 15
    
    # Few connections (ghost profile)
    if profile_data.get('connections', 0) < 100:
        score += 20
    
    return min(score, 100)

def create_profile_from_manual_input(data):
    """Create a structured profile from manual input"""
    profile = {}
    
    # Required fields
    profile['name'] = data.get('name', 'Unknown')
    profile['headline'] = data.get('headline', '')
    profile['about'] = data.get('about', '')
    profile['location'] = data.get('location', '')
    profile['company'] = data.get('company', data.get('current_company', ''))
    
    # Experience
    if 'years_experience' in data:
        profile['years_experience'] = data['years_experience']
    else:
        profile['years_experience'] = parse_years_experience(data.get('headline', ''))
    
    # Seniority
    if 'seniority_level' in data:
        profile['seniority_level'] = data['seniority_level']
    else:
        profile['seniority_level'] = infer_seniority(
            data.get('headline', ''), 
            profile['years_experience']
        )
    
    # Connections
    profile['connections'] = data.get('connections', 500)
    
    # Industry
    profile['industry'] = data.get('industry', 'Technology')
    
    # Job category
    if 'job_category' in data:
        profile['job_category'] = data['job_category']
    else:
        profile['job_category'] = infer_job_category(
            data.get('headline', ''), 
            data.get('about', '')
        )
    
    # Skills
    profile['skills'] = data.get('skills', [])
    if isinstance(profile['skills'], str):
        profile['skills'] = [s.strip() for s in profile['skills'].split(',')]
    
    # Education
    profile['education_list'] = data.get('education_list', data.get('education', []))
    profile['university'] = ''
    if profile['education_list']:
        if isinstance(profile['education_list'], list) and len(profile['education_list']) > 0:
            if isinstance(profile['education_list'][0], dict):
                profile['university'] = profile['education_list'][0].get('school', '').lower()
    
    # v3 specific fields
    profile['needs'] = data.get('needs', [])
    profile['can_offer'] = data.get('can_offer', [])
    profile['goals'] = data.get('goals', [])
    
    # Estimated scores
    profile['engagement_quality_score'] = data.get('engagement_quality_score', 
                                                    estimate_engagement())
    profile['red_flag_score'] = data.get('red_flag_score', 
                                         estimate_red_flags(data))
    profile['rising_star_score'] = data.get('rising_star_score', 30.0)
    profile['undervalued_score'] = data.get('undervalued_score', 30.0)
    
    return profile

def calculate_all_scores(user, target):
    """Calculate all 12 component scores for v3"""
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
    user_skills = set([s.lower() for s in user.get('skills', [])])
    target_skills = set([s.lower() for s in target.get('skills', [])])
    new = len(target_skills - user_skills)
    if new >= 5: scores['skill_learning_score'] = 70
    elif new >= 3: scores['skill_learning_score'] = 50
    else: scores['skill_learning_score'] = 40
    
    # 4. Role Synergy
    ur = user.get('job_category', 'other')
    tr = target.get('job_category', 'other')
    if ur == tr: scores['role_synergy_score'] = 100
    elif tr in RELATED_ROLES.get(ur, []): scores['role_synergy_score'] = 70
    else: scores['role_synergy_score'] = 40
    
    # 5. Goal Alignment (v3)
    user_needs = set([str(n).lower() for n in user.get('needs', [])])
    target_offers = set([str(o).lower() for o in target.get('can_offer', [])])
    if user_needs and target_offers:
        overlap = user_needs & target_offers
        scores['goal_alignment_score'] = int((len(overlap) / len(user_needs)) * 100) if user_needs else 50
    else:
        scores['goal_alignment_score'] = 50
    
    # 6. Alumni
    user_uni = user.get('university', '').lower()
    target_uni = target.get('university', '').lower()
    scores['alumni_score'] = 100 if (user_uni and target_uni and user_uni in target_uni) else 0
    
    # 7. Career
    sen_scores = {'entry': 30, 'mid': 50, 'senior': 75, 'executive': 95}
    scores['career_score'] = sen_scores.get(target.get('seniority_level', 'entry'), 30)
    
    # 8. Industry
    scores['industry_score'] = 100 if user.get('industry', '').lower() == target.get('industry', '').lower() else 30
    
    # 9. Geographic Proximity (v3)
    user_loc = user.get('location', '').split(',')
    target_loc = target.get('location', '').split(',')
    if len(user_loc) >= 2 and len(target_loc) >= 2:
        if user_loc[0].strip().lower() == target_loc[0].strip().lower():
            scores['geographic_score'] = 100
        elif user_loc[-1].strip().lower() == target_loc[-1].strip().lower():
            scores['geographic_score'] = 70
        else:
            scores['geographic_score'] = 40
    else:
        scores['geographic_score'] = 50
    
    # 10. Engagement Quality (v3)
    scores['engagement_score'] = float(target.get('engagement_quality_score', 50))
    
    # 11. Rising Star (v3)
    rising = float(target.get('rising_star_score', 0))
    hidden = float(target.get('undervalued_score', 0))
    scores['rising_star_score_calc'] = (rising + hidden) / 2
    
    return scores

def predict_compatibility(user, target):
    """Predict using v3 model"""
    scores = calculate_all_scores(user, target)
    
    user_strength = 50
    target_strength = 60
    
    def safe_transform(encoder, value):
        if value in encoder.classes_:
            return encoder.transform([value])[0]
        return 0
    
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
    score = model.predict(X)[0]
    
    # Apply red flag penalty
    red_flag = float(target.get('red_flag_score', 0))
    if red_flag > 75: score *= 0.80
    elif red_flag > 50: score *= 0.90
    elif red_flag > 25: score *= 0.95
    
    return score, scores

# ============================================
# TEST PROFILES
# ============================================

# Example: Add real profiles here (manually copied from LinkedIn)
TEST_PROFILES = [
    {
        'name': 'Test Person 1',
        'headline': 'Senior Data Scientist at Amazon',
        'about': 'Passionate about ML and AI. 8 years experience.',
        'location': 'Seattle, WA',
        'company': 'Amazon',
        'connections': 2500,
        'years_experience': 8,
        'skills': ['Python', 'Machine Learning', 'AWS', 'Spark', 'TensorFlow'],
        'education_list': [{'school': 'Stanford University'}],
        'can_offer': ['mentorship', 'job referral', 'career advice'],
        'needs': ['collaboration', 'research ideas']
    },
    # Add more profiles here...
]

# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("📋 TESTING WITH SAMPLE PROFILES")
    print("="*70)
    
    for raw_profile in TEST_PROFILES:
        # Parse profile
        target = create_profile_from_manual_input(raw_profile)
        
        # Predict
        score, breakdown = predict_compatibility(YOUR_PROFILE, target)
        
        print(f"\n{'='*70}")
        print(f"🎯 Target: {target['name']}")
        print(f"   {target['headline']}")
        print(f"{'='*70}")
        
        print(f"\n📊 COMPATIBILITY SCORE: {score:.1f}/100")
        
        if score >= 80:
            verdict = "EXCELLENT MATCH 🌟"
        elif score >= 70:
            verdict = "GREAT MATCH 💎"
        elif score >= 60:
            verdict = "GOOD MATCH 👍"
        elif score >= 50:
            verdict = "MODERATE MATCH 📊"
        else:
            verdict = "LOW MATCH 📉"
        
        print(f"   Verdict: {verdict}")
        
        print(f"\n📋 SCORE BREAKDOWN (v3 - 12 factors):")
        print(f"   1. Mentorship:        {breakdown['mentorship_score']:3.0f}/100")
        print(f"   2. Network:           {breakdown['network_score']:3.0f}/100")
        print(f"   3. Skill Learning:    {breakdown['skill_learning_score']:3.0f}/100")
        print(f"   4. Role Synergy:      {breakdown['role_synergy_score']:3.0f}/100")
        print(f"   5. Goal Alignment:    {breakdown['goal_alignment_score']:3.0f}/100 (v3)")
        print(f"   6. Alumni:            {breakdown['alumni_score']:3.0f}/100")
        print(f"   7. Career:            {breakdown['career_score']:3.0f}/100")
        print(f"   8. Industry:          {breakdown['industry_score']:3.0f}/100")
        print(f"   9. Geographic:        {breakdown['geographic_score']:3.0f}/100 (v3)")
        print(f"  10. Engagement:        {breakdown['engagement_score']:3.0f}/100 (v3)")
        print(f"  11. Rising Star:       {breakdown['rising_star_score_calc']:3.0f}/100 (v3)")
        
        print(f"\n💡 Profile Details:")
        print(f"   Location: {target['location']}")
        print(f"   Experience: {target['years_experience']} years ({target['seniority_level']})")
        print(f"   Company: {target['company']}")
        print(f"   Connections: {target['connections']:,}")
        print(f"   Job Category: {target['job_category']}")
    
    print("\n" + "="*70)
    print("✅ Testing Complete!")
    print("="*70)
    print("\n💡 TO TEST WITH REAL PROFILES:")
    print("   1. Find a LinkedIn profile")
    print("   2. Copy the data manually")
    print("   3. Add to TEST_PROFILES list in this script")
    print("   4. Run again!")
    print(f"\n📝 Edit this file to add more profiles: 7_real_profile_tester.py")
