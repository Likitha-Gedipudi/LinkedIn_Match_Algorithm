"""
LinkedIn Compatibility Predictor
=================================
Enter YOUR profile details and find compatible connections!
"""

import pandas as pd
import numpy as np
import joblib
import json
import ast
import warnings
warnings.filterwarnings('ignore')

# ============================================
# LOAD MODEL AND DATA
# ============================================
print("="*70)
print("🎯 LINKEDIN COMPATIBILITY PREDICTOR")
print("="*70)
print("\nLoading model and data...")

# Load model
model = joblib.load("data/models/compatibility_model_v2.joblib")
encoders = joblib.load("data/models/encoders.joblib")
profiles_df = pd.read_csv("data/processed/profiles_with_features.csv")

# Parse skills list
def safe_parse(x):
    if pd.isna(x):
        return []
    if isinstance(x, list):
        return x
    try:
        return ast.literal_eval(x)
    except:
        return []

profiles_df['skills_list'] = profiles_df['skills_list'].apply(safe_parse)

print(f"✅ Model loaded")
print(f"✅ {len(profiles_df):,} profiles available")

# ============================================
# SCORING FUNCTIONS
# ============================================

# Prestigious companies
PRESTIGIOUS = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 
               'netflix', 'tesla', 'uber', 'airbnb', 'stripe', 'linkedin',
               'nvidia', 'adobe', 'salesforce', 'oracle', 'ibm', 'intel']

SENIORITY_MAP = {'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3}

# Related roles
RELATED_ROLES = {
    'data_science': ['data_analytics', 'data_engineering', 'software_dev', 'product'],
    'data_analytics': ['data_science', 'data_engineering', 'product'],
    'data_engineering': ['data_science', 'data_analytics', 'software_dev'],
    'software_dev': ['data_engineering', 'data_science', 'product'],
    'product': ['data_analytics', 'software_dev', 'design', 'data_science'],
    'design': ['product', 'software_dev'],
    'executive': ['product', 'data_science', 'software_dev'],
    'student': ['data_science', 'software_dev', 'data_analytics', 'data_engineering'],
    'other': []
}

# NEW WEIGHTS with Alumni factor
WEIGHTS = {
    'mentorship': 0.22,
    'network': 0.18,
    'skill_learning': 0.18,
    'role_synergy': 0.14,
    'alumni': 0.10,
    'career': 0.10,
    'industry': 0.08
}

def calculate_profile_strength(profile):
    """Calculate profile strength score"""
    exp_score = min(profile['years_experience'] * 5, 100)
    seniority_scores = {'entry': 20, 'mid': 45, 'senior': 70, 'executive': 95}
    seniority_score = seniority_scores.get(profile['seniority_level'], 20)
    skills_count = len(profile.get('skills', []))
    skills_score = min(skills_count * 5, 100)
    connections = profile.get('connections', 0)
    if connections >= 5000: conn_score = 100
    elif connections >= 1000: conn_score = 80
    elif connections >= 500: conn_score = 60
    elif connections >= 200: conn_score = 40
    else: conn_score = 20
    company = str(profile.get('company', '')).lower()
    prestige_score = 80 if any(p in company for p in PRESTIGIOUS) else 40
    
    return (0.20 * exp_score + 0.20 * seniority_score + 0.15 * skills_score +
            0.15 * conn_score + 0.15 * prestige_score + 0.15 * 50)

def calculate_component_scores(user, target):
    """Calculate the 7 component scores (with alumni)"""
    
    # 1. Mentorship Potential (22%)
    exp_gap = target.get('years_experience', 0) - user.get('years_experience', 0)
    if 3 <= exp_gap <= 10: mentorship = 100
    elif exp_gap > 10: mentorship = 70
    elif exp_gap > 0: mentorship = 60
    else: mentorship = 20
    
    user_role = user.get('job_category', 'other')
    target_role = target.get('job_category', 'other')
    if user_role == target_role: mentorship = min(mentorship + 20, 100)
    elif target_role in RELATED_ROLES.get(user_role, []): mentorship = min(mentorship + 10, 100)
    
    # 2. Network Value (18%)
    connections = target.get('connections', 0)
    if connections >= 5000: network = 100
    elif connections >= 2000: network = 85
    elif connections >= 1000: network = 70
    elif connections >= 500: network = 55
    elif connections >= 200: network = 40
    else: network = 25
    company = str(target.get('company', target.get('current_company', ''))).lower()
    if any(p in company for p in PRESTIGIOUS): network = min(network + 15, 100)
    
    # 3. Skill Learning (18%)
    user_skills = set(user.get('skills', []))
    target_skills = set(target.get('skills_list', target.get('skills', [])))
    if isinstance(target_skills, str): target_skills = set()
    new_skills = len(target_skills - user_skills)
    shared = len(user_skills & target_skills)
    if new_skills >= 10: skill_learning = 90
    elif new_skills >= 5: skill_learning = 70
    elif new_skills >= 3: skill_learning = 50
    else: skill_learning = 30
    if shared >= 3: skill_learning = min(skill_learning + 10, 100)
    
    # 4. Role Synergy (14%)
    if user_role == target_role: role_synergy = 100
    elif target_role in RELATED_ROLES.get(user_role, []): role_synergy = 70
    elif user_role == 'other' or target_role == 'other': role_synergy = 40
    else: role_synergy = 20
    
    # 5. Alumni Connection (10%) - NEW!
    user_uni = user.get('university', '').lower().strip()
    target_edu = target.get('education_list', [])
    target_schools = set()
    if isinstance(target_edu, list):
        for edu in target_edu:
            if isinstance(edu, dict) and 'school' in edu:
                target_schools.add(edu['school'].lower().strip())
    
    alumni = 0
    if user_uni and target_schools:
        if user_uni in target_schools:
            alumni = 100
        else:
            for school in target_schools:
                if user_uni in school or school in user_uni:
                    alumni = 80
                    break
    
    # 6. Career Advancement (10%)
    target_seniority = target.get('seniority_level', 'entry')
    career_scores = {'entry': 30, 'mid': 50, 'senior': 75, 'executive': 95}
    career = career_scores.get(target_seniority, 30)
    if any(p in company for p in PRESTIGIOUS): career = min(career + 15, 100)
    
    # 7. Industry Match (8%)
    user_ind = user.get('industry', '').lower()
    target_ind = str(target.get('industry', '')).lower()
    if user_ind == target_ind: industry = 100
    else: industry = 30
    
    return {
        'mentorship_score': mentorship,
        'network_score': network,
        'skill_learning_score': skill_learning,
        'role_synergy_score': role_synergy,
        'alumni_score': alumni,
        'career_score': career,
        'industry_score': industry
    }

def predict_compatibility(user_profile, target_profile, model, encoders):
    """Predict compatibility score between user and target"""
    
    # Calculate component scores
    scores = calculate_component_scores(user_profile, target_profile)
    
    # Calculate profile strengths
    user_strength = calculate_profile_strength(user_profile)
    target_strength = calculate_profile_strength(target_profile)
    
    # Encode categorical variables
    le_seniority = encoders['seniority']
    le_role = encoders['role']
    le_industry = encoders['industry']
    
    user_seniority = user_profile.get('seniority_level', 'entry')
    target_seniority = target_profile.get('seniority_level', 'entry')
    user_role = user_profile.get('job_category', 'other')
    target_role = target_profile.get('job_category', 'other')
    user_industry = str(user_profile.get('industry', ''))
    target_industry = str(target_profile.get('industry', ''))
    
    # Handle unknown categories
    if user_seniority not in le_seniority.classes_: user_seniority = 'entry'
    if target_seniority not in le_seniority.classes_: target_seniority = 'entry'
    if user_role not in le_role.classes_: user_role = 'other'
    if target_role not in le_role.classes_: target_role = 'other'
    if user_industry not in le_industry.classes_: user_industry = ''
    if target_industry not in le_industry.classes_: target_industry = ''
    
    # Handle unknown categories - use first known class as fallback
    def safe_transform(encoder, value, default_idx=0):
        if value in encoder.classes_:
            return encoder.transform([value])[0]
        return default_idx
    
    # Create feature vector
    features = {
        'user_exp': user_profile.get('years_experience', 0),
        'user_seniority_enc': safe_transform(le_seniority, user_seniority),
        'user_connections': user_profile.get('connections', 0),
        'user_role_enc': safe_transform(le_role, user_role),
        'user_industry_enc': safe_transform(le_industry, user_industry),
        'user_strength': user_strength,
        'target_exp': target_profile.get('years_experience', 0),
        'target_seniority_enc': safe_transform(le_seniority, target_seniority),
        'target_connections': target_profile.get('connections', 0),
        'target_role_enc': safe_transform(le_role, target_role),
        'target_industry_enc': safe_transform(le_industry, target_industry),
        'target_strength': target_strength,
        'exp_gap': target_profile.get('years_experience', 0) - user_profile.get('years_experience', 0),
        'seniority_gap': SENIORITY_MAP.get(target_seniority, 0) - SENIORITY_MAP.get(user_seniority, 0),
        'connection_gap': target_profile.get('connections', 0) - user_profile.get('connections', 0),
        'strength_gap': target_strength - user_strength,
        'same_role': 1 if user_role == target_role else 0,
        'same_industry': 1 if user_industry.lower() == target_industry.lower() else 0,
        **scores
    }
    
    # Predict
    X = pd.DataFrame([features])
    prediction = model.predict(X)[0]
    
    return {
        'score': round(prediction, 1),
        'breakdown': scores,
        'user_strength': round(user_strength, 1),
        'target_strength': round(target_strength, 1)
    }

# ============================================
# YOUR PROFILE
# ============================================
print("\n" + "─"*70)
print("📝 ENTER YOUR PROFILE")
print("─"*70)

# MODIFY THIS WITH YOUR DETAILS!
YOUR_PROFILE = {
    'name': 'Likitha',
    'years_experience': 1,  # Years of experience
    'seniority_level': 'entry',  # entry, mid, senior, executive
    'connections': 600,  # LinkedIn connections
    'industry': 'Technology',  # Your industry
    'company': 'null',  # Current company
    'job_category': 'data_science, data analyst',  # data_science, data_analytics, software_dev, product, design, etc.
    'skills': ['Python', 'SQL', 'Machine Learning', 'Data Analysis', 'Tableau'],  # Your skills
    'university': 'University at Buffalo'  # Your university for alumni matching!
}

print(f"\n👤 Your Profile:")
print(f"   Experience: {YOUR_PROFILE['years_experience']} years ({YOUR_PROFILE['seniority_level']})")
print(f"   Industry: {YOUR_PROFILE['industry']}")
print(f"   Role: {YOUR_PROFILE['job_category']}")
print(f"   Skills: {', '.join(YOUR_PROFILE['skills'][:5])}")
print(f"   Connections: {YOUR_PROFILE['connections']}")

# ============================================
# FIND TOP MATCHES
# ============================================
print("\n" + "─"*70)
print("🔍 FINDING TOP MATCHES...")
print("─"*70)

# Calculate compatibility with all profiles
results = []
sample_profiles = profiles_df.sample(n=min(5000, len(profiles_df)), random_state=42)

for idx, target in sample_profiles.iterrows():
    target_dict = target.to_dict()
    target_dict['skills_list'] = target['skills_list'] if isinstance(target['skills_list'], list) else []
    
    result = predict_compatibility(YOUR_PROFILE, target_dict, model, encoders)
    
    results.append({
        'name': target['name'],
        'headline': target.get('headline', '')[:50],
        'company': target.get('current_company', ''),
        'experience': target.get('years_experience', 0),
        'seniority': target.get('seniority_level', ''),
        'connections': target.get('connections', 0),
        'score': result['score'],
        'mentorship': result['breakdown']['mentorship_score'],
        'network': result['breakdown']['network_score'],
        'skills': result['breakdown']['skill_learning_score'],
        'role_match': result['breakdown']['role_synergy_score']
    })

results_df = pd.DataFrame(results).sort_values('score', ascending=False)

# ============================================
# DISPLAY TOP MATCHES
# ============================================
print("\n" + "="*70)
print("🏆 TOP 20 MATCHES FOR YOU")
print("="*70)

print(f"\n{'#':<3} {'Name':<20} {'Company':<15} {'Exp':<5} {'Score':<8} {'Why Great?'}")
print("-"*80)

for i, row in results_df.head(20).iterrows():
    # Determine why they're a good match
    reasons = []
    if row['mentorship'] >= 80: reasons.append("Mentor 👨‍🏫")
    if row['network'] >= 80: reasons.append("Network 🌐")
    if row['skills'] >= 70: reasons.append("Skills 🛠️")
    if row['role_match'] >= 80: reasons.append("Same Field 🎯")
    
    reason_str = ", ".join(reasons[:2]) if reasons else "Good Overall"
    
    rank = results_df.index.get_loc(i) + 1
    print(f"{rank:<3} {row['name'][:19]:<20} {str(row['company'])[:14]:<15} {row['experience']:<5} {row['score']:<8.1f} {reason_str}")

# ============================================
# SCORE DISTRIBUTION
# ============================================
print("\n" + "─"*70)
print("📊 SCORE DISTRIBUTION")
print("─"*70)

print(f"\nYour matches across {len(results_df)} profiles:")
print(f"   90-100 (Excellent): {len(results_df[results_df['score'] >= 90])}")
print(f"   75-89 (Great):      {len(results_df[(results_df['score'] >= 75) & (results_df['score'] < 90)])}")
print(f"   60-74 (Good):       {len(results_df[(results_df['score'] >= 60) & (results_df['score'] < 75)])}")
print(f"   40-59 (Moderate):   {len(results_df[(results_df['score'] >= 40) & (results_df['score'] < 60)])}")
print(f"   Below 40 (Low):     {len(results_df[results_df['score'] < 40])}")

# ============================================
# EXAMPLE SCENARIOS
# ============================================
print("\n" + "─"*70)
print("📋 SCORE INTERPRETATION")
print("─"*70)

print("""
WHAT THE SCORES MEAN:

90-100 (Excellent Match):
  → Strong mentorship potential from senior in your field
  → Great network value (FAANG, 5000+ connections)
  → Same role category, can directly help your career

75-89 (Great Match):
  → Good mentorship (3-5 years more experience)
  → Decent network at good company
  → Related field, useful for career guidance

60-74 (Good Match):
  → Some experience advantage
  → Standard networking value
  → Related industry or skills

40-59 (Moderate Match):
  → Similar experience level (peer)
  → Average networking value
  → Different field but some overlap

Below 40 (Lower Match):
  → Less experience than you
  → Small network
  → Different industry/field

WEIGHT DISTRIBUTION:
  • Mentorship Potential: 22%
  • Network Value: 18%
  • Skill Learning: 18%
  • Role Synergy: 14%
  • 🎓 Alumni Connection: 10%
  • Career Advancement: 10%
  • Industry Match: 8%
""")

print("\n✅ Done! Modify YOUR_PROFILE in predict.py to test with your actual details.")
