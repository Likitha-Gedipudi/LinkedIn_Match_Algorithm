"""
LinkedIn Compatibility - Detailed Single Prediction
====================================================
Get a comprehensive analysis of why someone is/isn't a good match
"""

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

# ============================================
# LOAD MODEL
# ============================================
print("="*70)
print("🎯 LINKEDIN COMPATIBILITY - DETAILED ANALYSIS")
print("="*70)
print("\nLoading model...")

model = joblib.load("data/models/compatibility_model_v2.joblib")
encoders = joblib.load("data/models/encoders.joblib")

print("✅ Model loaded")

# ============================================
# CONSTANTS
# ============================================
PRESTIGIOUS = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 
               'netflix', 'tesla', 'uber', 'airbnb', 'stripe', 'linkedin',
               'nvidia', 'adobe', 'salesforce', 'oracle', 'ibm', 'intel',
               'twitter', 'snap', 'spotify', 'zillow', 'doordash']

SENIORITY_MAP = {'entry': 0, 'mid': 1, 'senior': 2, 'executive': 3}

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

# ============================================
# SCORING FUNCTIONS
# ============================================

def calculate_profile_strength(profile):
    """Calculate profile strength score"""
    exp_score = min(profile.get('years_experience', 0) * 5, 100)
    seniority_scores = {'entry': 20, 'mid': 45, 'senior': 70, 'executive': 95}
    seniority_score = seniority_scores.get(profile.get('seniority_level', 'entry'), 20)
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
    """Calculate all 7 component scores"""
    
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
    company = str(target.get('company', '')).lower()
    if any(p in company for p in PRESTIGIOUS): network = min(network + 15, 100)
    
    # 3. Skill Learning (18%)
    user_skills = set([s.lower() for s in user.get('skills', [])])
    target_skills = set([s.lower() for s in target.get('skills', [])])
    new_skills = target_skills - user_skills
    shared_skills = user_skills & target_skills
    if len(new_skills) >= 10: skill_learning = 90
    elif len(new_skills) >= 5: skill_learning = 70
    elif len(new_skills) >= 3: skill_learning = 50
    else: skill_learning = 30
    if len(shared_skills) >= 3: skill_learning = min(skill_learning + 10, 100)
    
    # 4. Role Synergy (14%)
    if user_role == target_role: role_synergy = 100
    elif target_role in RELATED_ROLES.get(user_role, []): role_synergy = 70
    elif user_role == 'other' or target_role == 'other': role_synergy = 40
    else: role_synergy = 20
    
    # 5. Alumni Connection (10%)
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
    target_ind = target.get('industry', '').lower()
    if user_ind == target_ind: industry = 100
    else: industry = 30
    
    return {
        'mentorship_score': mentorship,
        'network_score': network,
        'skill_learning_score': skill_learning,
        'role_synergy_score': role_synergy,
        'alumni_score': alumni,
        'career_score': career,
        'industry_score': industry,
        'exp_gap': exp_gap,
        'new_skills': new_skills,
        'shared_skills': shared_skills
    }

def generate_insights(user, target, scores, prediction):
    """Generate comprehensive scenario-based insights"""
    
    insights = {
        'strengths': [],
        'weaknesses': [],
        'opportunities': [],
        'recommendations': []
    }
    
    exp_gap = scores['exp_gap']
    user_role = user.get('job_category', 'other')
    target_role = target.get('job_category', 'other')
    company = str(target.get('company', '')).lower()
    is_prestigious = any(p in company for p in PRESTIGIOUS)
    
    # === STRENGTHS ===
    
    # Alumni connection
    if scores['alumni_score'] == 100:
        insights['strengths'].append(f"🎓 **SAME UNIVERSITY** - Strong alumni bond! Instant conversation starter.")
    elif scores['alumni_score'] == 80:
        insights['strengths'].append(f"🎓 **Related universities** - Some alumni connection.")
    
    # Mentorship potential
    if 3 <= exp_gap <= 10:
        if user_role == target_role:
            insights['strengths'].append(f"👨‍🏫 **PERFECT MENTOR** - {exp_gap} years more experience in the SAME field!")
        elif target_role in RELATED_ROLES.get(user_role, []):
            insights['strengths'].append(f"👨‍🏫 **GREAT MENTOR** - {exp_gap} years more experience in a related field!")
        else:
            insights['strengths'].append(f"✅ **Experienced** - {exp_gap} years more experience (though different field)")
    elif exp_gap > 10:
        insights['strengths'].append(f"🎯 **Very senior** - {exp_gap} years more experience (may be less accessible)")
    
    # Prestigious company
    if is_prestigious:
        company_name = target.get('company', 'prestigious company')
        insights['strengths'].append(f"🏢 **{company_name.upper()}** - Can refer you to jobs! Valuable network access.")
    
    # Same/related field
    if user_role == target_role:
        insights['strengths'].append(f"🎯 **SAME FIELD** - Direct career relevance! Can share specific advice.")
    elif target_role in RELATED_ROLES.get(user_role, []):
        insights['strengths'].append(f"🔗 **RELATED FIELD** - Cross-functional insights valuable.")
    
    # Skills
    if len(scores['new_skills']) >= 5:
        sample_skills = list(scores['new_skills'])[:5]
        insights['strengths'].append(f"📚 **MANY NEW SKILLS** - Can learn: {', '.join(sample_skills)}...")
    elif len(scores['new_skills']) >= 3:
        insights['strengths'].append(f"📖 **New skills to learn** - {len(scores['new_skills'])} skills you don't have")
    
    # Good network size
    if target.get('connections', 0) >= 2000:
        insights['strengths'].append(f"🌐 **LARGE NETWORK** - {target.get('connections', 0):,}+ connections for intro opportunities")
    elif target.get('connections', 0) >= 500:
        insights['strengths'].append(f"👥 **Good network** - {target.get('connections', 0):,} connections")
    
    # Same industry
    if scores['industry_score'] == 100:
        insights['strengths'].append(f"🏭 **Same industry** - Directly relevant experience")
    
    # === WEAKNESSES ===
    
    # No mentorship (less experienced)
    if exp_gap <= 0:
        insights['weaknesses'].append(f"⚠️ **No mentorship potential** - You have {abs(exp_gap)} more years experience")
    elif exp_gap < 3:
        insights['weaknesses'].append(f"⚠️ **Limited mentorship** - Only {exp_gap} year(s) gap")
    
    # Different field
    if user_role != target_role and target_role not in RELATED_ROLES.get(user_role, []):
        insights['weaknesses'].append(f"⚠️ **Different field** - {target_role.replace('_', ' ').title()} vs {user_role.replace('_', ' ').title()}")
    
    # Different industry
    if scores['industry_score'] != 100:
        user_ind = user.get('industry', 'your industry')
        target_ind = target.get('industry', 'their industry')
        insights['weaknesses'].append(f"⚠️ **Different industry** - {target_ind} vs {user_ind}")
    
    # Small network
    if target.get('connections', 0) < 200:
        insights['weaknesses'].append(f"📉 **Small network** - Limited networking opportunities")
    
    # No alumni connection
    if scores['alumni_score'] == 0:
        insights['weaknesses'].append(f"❌ **No alumni connection** - Different universities")
    
    # Few new skills
    if len(scores['new_skills']) < 3:
        insights['weaknesses'].append(f"📖 **Limited new skills** - Mostly skills you already have")
    
    # === OPPORTUNITIES ===
    
    # Scenario: Student/Junior looking at Senior
    if exp_gap >= 5 and user.get('seniority_level') == 'entry':
        insights['opportunities'].append("💼 **Career guidance** - Can help with career trajectory decisions")
        if is_prestigious:
            insights['opportunities'].append("🚀 **Job referrals** - May refer you to their company")
    
    # Scenario: Same level peers
    if -1 <= exp_gap <= 1:
        insights['opportunities'].append("🤝 **Peer collaboration** - Build projects together, grow together")
        insights['opportunities'].append("💬 **Mutual support** - Share job hunts, interview prep")
    
    # Scenario: Cross-functional learning
    if user_role != target_role and target_role in RELATED_ROLES.get(user_role, []):
        insights['opportunities'].append(f"🔄 **Cross-functional insights** - Learn {target_role.replace('_', ' ')} perspective")
    
    # Alumni networking
    if scores['alumni_score'] >= 80:
        insights['opportunities'].append("🎓 **Alumni events** - Connect at university networking events")
    
    # Industry connections
    if scores['industry_score'] == 100 and is_prestigious:
        insights['opportunities'].append("🌟 **Industry insider access** - Learn about company culture, hiring")
    
    # === RECOMMENDATIONS ===
    
    # Overall score-based recommendations
    if prediction >= 85:
        insights['recommendations'].append("✅ **HIGHLY RECOMMEND** - This is an excellent match! Reach out ASAP.")
        insights['recommendations'].append("💬 Message tip: Mention your common university/field and ask for a brief informational chat")
    elif prediction >= 70:
        insights['recommendations'].append("✅ **RECOMMENDED** - Strong potential benefit. Worth connecting.")
        insights['recommendations'].append("💬 Message tip: Reference specific shared interests or alumni connection")
    elif prediction >= 55:
        insights['recommendations'].append("👍 **WORTH CONNECTING** - Moderate benefit. Good for expanding network diversity.")
        insights['recommendations'].append("💬 Message tip: Be specific about what you'd like to learn from them")
    elif prediction >= 40:
        insights['recommendations'].append("🤔 **OPTIONAL** - Limited direct benefit, but could expand network diversity")
    else:
        insights['recommendations'].append("⏭️ **LOW PRIORITY** - Focus on higher-value connections first")
    
    # Specific action recommendations
    if scores['alumni_score'] >= 80:
        insights['recommendations'].append("🎓 Action: Mention your shared university in your connection request!")
    
    if is_prestigious and exp_gap >= 3:
        insights['recommendations'].append(f"💼 Action: Ask about their experience at {target.get('company', 'the company')}")
    
    if len(scores['new_skills']) >= 5:
        skills_list = ', '.join(list(scores['new_skills'])[:3])
        insights['recommendations'].append(f"📚 Action: Ask for resources to learn {skills_list}")
    
    if user_role == target_role and exp_gap >= 3:
        insights['recommendations'].append("👨‍🏫 Action: Request a 15-min informational interview about their career path")
    
    return insights

def predict_with_explanation(user_profile, target_profile):
    """Full prediction with comprehensive explanation"""
    
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
    
    def safe_transform(encoder, value):
        if value in encoder.classes_:
            return encoder.transform([value])[0]
        return 0
    
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
        'exp_gap': scores['exp_gap'],
        'seniority_gap': SENIORITY_MAP.get(target_seniority, 0) - SENIORITY_MAP.get(user_seniority, 0),
        'connection_gap': target_profile.get('connections', 0) - user_profile.get('connections', 0),
        'strength_gap': target_strength - user_strength,
        'same_role': 1 if user_role == target_role else 0,
        'same_industry': 1 if user_industry.lower() == target_industry.lower() else 0,
        'mentorship_score': scores['mentorship_score'],
        'network_score': scores['network_score'],
        'skill_learning_score': scores['skill_learning_score'],
        'role_synergy_score': scores['role_synergy_score'],
        'alumni_score': scores['alumni_score'],
        'career_score': scores['career_score'],
        'industry_score': scores['industry_score']
    }
    
    # Predict
    X = pd.DataFrame([features])
    prediction = model.predict(X)[0]
    
    # Generate insights
    insights = generate_insights(user_profile, target_profile, scores, prediction)
    
    return {
        'score': round(prediction, 1),
        'scores': scores,
        'insights': insights
    }

# ============================================
# DISPLAY FUNCTIONS
# ============================================

def display_result(user, target, result):
    """Display comprehensive analysis"""
    
    print("\n" + "="*70)
    print(f"🎯 COMPATIBILITY ANALYSIS: {user['name']} → {target['name']}")
    print("="*70)
    
    score = result['score']
    scores = result['scores']
    insights = result['insights']
    
    # Score with visual indicator
    print(f"\n📊 PREDICTED SCORE: {score}/100", end="")
    if score >= 85:
        print(" 🌟🌟🌟 EXCELLENT")
    elif score >= 70:
        print(" 💎 GREAT")
    elif score >= 55:
        print(" 👍 GOOD")
    elif score >= 40:
        print(" 📊 MODERATE")
    else:
        print(" 📉 LOW")
    
    # Score breakdown
    print(f"\n📋 SCORE BREAKDOWN:")
    print(f"   ┌────────────────────────────┬────────┬──────────┐")
    print(f"   │ Factor                     │ Score  │ Contrib  │")
    print(f"   ├────────────────────────────┼────────┼──────────┤")
    breakdown = [
        ('Mentorship Potential', 0.22, scores['mentorship_score']),
        ('Network Value', 0.18, scores['network_score']),
        ('Skill Learning', 0.18, scores['skill_learning_score']),
        ('Role Synergy', 0.14, scores['role_synergy_score']),
        ('🎓 Alumni Connection', 0.10, scores['alumni_score']),
        ('Career Advancement', 0.10, scores['career_score']),
        ('Industry Match', 0.08, scores['industry_score'])
    ]
    for factor, weight, score_val in breakdown:
        print(f"   │ {factor:<26} │ {score_val:3.0f}/100 │ +{weight*score_val:5.1f}   │")
    print(f"   └────────────────────────────┴────────┴──────────┘")
    
    # Strengths
    if insights['strengths']:
        print(f"\n✅ **STRENGTHS** (Why connect):")
        for strength in insights['strengths']:
            print(f"   {strength}")
    
    # Weaknesses
    if insights['weaknesses']:
        print(f"\n⚠️  **LIMITATIONS** (What to be aware of):")
        for weakness in insights['weaknesses']:
            print(f"   {weakness}")
    
    # Opportunities
    if insights['opportunities']:
        print(f"\n💡 **OPPORTUNITIES** (What you can gain):")
        for opp in insights['opportunities']:
            print(f"   {opp}")
    
    # Recommendations
    if insights['recommendations']:
        print(f"\n🎯 **RECOMMENDATIONS**:")
        for rec in insights['recommendations']:
            print(f"   {rec}")
    
    print("\n" + "="*70)

# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    
    # Example: Your profile
    YOUR_PROFILE = {
        'name': 'Likitha',
        'years_experience': 1,
        'seniority_level': 'entry',
        'connections': 600,
        'industry': 'Technology',
        'company': 'Student',
        'job_category': 'data_science',
        'skills': ['Python', 'SQL', 'Machine Learning', 'Data Analysis', 'Tableau'],
        'university': 'university at buffalo'
    }
    
    # Example: Target person (Jayashree)
    TARGET_PROFILE = {
        'name': 'Jayashree',
        'years_experience': 5,
        'seniority_level': 'mid',
        'connections': 700,
        'industry': 'Technology',
        'company': 'Amazon',
        'job_category': 'data_analytics',
        'skills': ['Python', 'SQL', 'AWS', 'QuickSight', 'NLP', 'Machine Learning', 
                   'Tableau', 'Spark', 'Snowflake', 'Airflow', 'ETL'],
        'education_list': [{'school': 'university at buffalo'}],
        'university': 'university at buffalo'
    }
    
    # Run prediction
    result = predict_with_explanation(YOUR_PROFILE, TARGET_PROFILE)
    display_result(YOUR_PROFILE, TARGET_PROFILE, result)
    
    print("\n" + "─"*70)
    print("💡 TO USE WITH YOUR OWN PROFILES:")
    print("   1. Modify YOUR_PROFILE with your details")
    print("   2. Modify TARGET_PROFILE with the person you want to analyze")
    print("   3. Run: python 5_detailed_prediction.py")
    print("─"*70)
