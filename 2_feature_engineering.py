"""
LinkedIn Compatibility Model - Part 2: Feature Engineering
============================================================
Create features for "How much will I benefit from connecting with this person?"

Key Scoring Criteria:
1. About section - mutual benefit from similar positions
2. Current company/role - can they help me?
3. Keyword matching - skills, experience, job-related terms
4. Profile strength gap - what can they offer me?
"""

import pandas as pd
import numpy as np
import json
import ast
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("🔧 LINKEDIN COMPATIBILITY MODEL - FEATURE ENGINEERING")
print("="*70)

# ============================================
# 1. LOAD DATA
# ============================================
print("\n" + "─"*70)
print("📂 LOADING DATA")
print("─"*70)

profiles_df = pd.read_csv("data/processed/profiles_cleaned.csv")
print(f"✅ Profiles loaded: {len(profiles_df):,}")

# Parse JSON columns if needed
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
profiles_df['experience_list'] = profiles_df['experience_list'].apply(safe_parse)

# ============================================
# 2. PROFILE STRENGTH SCORE
# ============================================
print("\n" + "─"*70)
print("💪 CALCULATING PROFILE STRENGTH SCORES")
print("─"*70)

"""
Profile Strength = How valuable is this profile overall?

Components (0-100 each, weighted):
- Experience: 20%
- Seniority: 20%
- Skills: 15%
- Connections: 15%
- Company Prestige: 15%
- Education: 15%
"""

# Seniority mapping
SENIORITY_SCORES = {
    'entry': 20,
    'mid': 45,
    'senior': 70,
    'executive': 95
}

# Prestigious companies
PRESTIGIOUS = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 
               'netflix', 'tesla', 'uber', 'airbnb', 'stripe', 'linkedin',
               'nvidia', 'adobe', 'salesforce', 'oracle', 'ibm', 'intel']

def calculate_profile_strength(row):
    """Calculate overall profile strength score (0-100)"""
    
    # 1. Experience Score (0-100)
    years = row.get('years_experience', 0)
    exp_score = min(years * 5, 100)  # 20 years = max
    
    # 2. Seniority Score (0-100)
    seniority = row.get('seniority_level', 'entry')
    seniority_score = SENIORITY_SCORES.get(seniority, 20)
    
    # 3. Skills Score (0-100)
    skills = row.get('skills_list', [])
    if isinstance(skills, str):
        skills = safe_parse(skills)
    skills_count = len(skills) if skills else 0
    skills_score = min(skills_count * 5, 100)  # 20 skills = max
    
    # 4. Connections Score (0-100)
    connections = row.get('connections', 0)
    if connections >= 5000:
        conn_score = 100
    elif connections >= 1000:
        conn_score = 80
    elif connections >= 500:
        conn_score = 60
    elif connections >= 200:
        conn_score = 40
    else:
        conn_score = 20
    
    # 5. Company Prestige Score (0-100)
    company = str(row.get('current_company', '')).lower()
    prestige_score = 80 if any(p in company for p in PRESTIGIOUS) else 40
    
    # 6. Education Score (placeholder - assume 50)
    edu_score = 50
    
    # Weighted average
    strength = (
        0.20 * exp_score +
        0.20 * seniority_score +
        0.15 * skills_score +
        0.15 * conn_score +
        0.15 * prestige_score +
        0.15 * edu_score
    )
    
    return round(strength, 2)

profiles_df['profile_strength'] = profiles_df.apply(calculate_profile_strength, axis=1)

print(f"📊 Profile Strength Distribution:")
print(f"   Min: {profiles_df['profile_strength'].min():.1f}")
print(f"   Mean: {profiles_df['profile_strength'].mean():.1f}")
print(f"   Max: {profiles_df['profile_strength'].max():.1f}")

# ============================================
# 3. ROLE/POSITION CATEGORIZATION
# ============================================
print("\n" + "─"*70)
print("💼 CATEGORIZING ROLES")
print("─"*70)

# Job categories with related terms
JOB_CATEGORIES = {
    'data_science': ['data scientist', 'machine learning', 'ml engineer', 'ai', 
                     'deep learning', 'nlp', 'computer vision', 'data science'],
    'data_analytics': ['data analyst', 'analytics', 'business intelligence', 'bi',
                       'tableau', 'power bi', 'sql analyst'],
    'data_engineering': ['data engineer', 'etl', 'pipeline', 'spark', 'airflow',
                         'data platform', 'big data'],
    'software_dev': ['software engineer', 'developer', 'sde', 'programmer',
                     'backend', 'frontend', 'full stack', 'web developer'],
    'product': ['product manager', 'product owner', 'pm', 'product lead'],
    'design': ['designer', 'ux', 'ui', 'user experience', 'creative'],
    'executive': ['ceo', 'cto', 'cfo', 'coo', 'director', 'vp', 'head of', 'chief'],
    'student': ['student', 'intern', 'graduate', 'fresher', 'entry level', 'junior']
}

def get_job_category(text):
    """Extract job category from headline/about/role"""
    if pd.isna(text):
        return 'other'
    text_lower = text.lower()
    for category, keywords in JOB_CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return 'other'

# Combine headline and about for better categorization
profiles_df['combined_text'] = (
    profiles_df['headline'].fillna('') + ' ' + 
    profiles_df['about'].fillna('') + ' ' +
    profiles_df['current_role'].fillna('')
)
profiles_df['job_category'] = profiles_df['combined_text'].apply(get_job_category)

print("📊 Job Categories:")
print(profiles_df['job_category'].value_counts().to_string())

# ============================================
# 4. KEYWORD EXTRACTION
# ============================================
print("\n" + "─"*70)
print("🔑 EXTRACTING KEYWORDS")
print("─"*70)

# Important keywords for matching
SKILL_KEYWORDS = {
    'programming': ['python', 'java', 'javascript', 'c++', 'go', 'rust', 'scala'],
    'data_tools': ['sql', 'spark', 'hadoop', 'airflow', 'kafka', 'pandas', 'numpy'],
    'ml_tools': ['tensorflow', 'pytorch', 'scikit', 'keras', 'xgboost'],
    'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'cloud'],
    'web': ['react', 'angular', 'vue', 'node', 'django', 'flask'],
    'design_tools': ['figma', 'sketch', 'photoshop', 'illustrator']
}

def extract_keywords(text):
    """Extract relevant keywords from text"""
    if pd.isna(text):
        return set()
    text_lower = text.lower()
    found = set()
    for category, keywords in SKILL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found.add(kw)
    return found

profiles_df['keywords'] = profiles_df['combined_text'].apply(extract_keywords)
profiles_df['keyword_count'] = profiles_df['keywords'].apply(len)

print(f"📊 Keywords extracted - Avg per profile: {profiles_df['keyword_count'].mean():.1f}")

# ============================================
# 5. COMPATIBILITY FEATURE CALCULATOR
# ============================================
print("\n" + "─"*70)
print("🎯 CREATING COMPATIBILITY FEATURES")
print("─"*70)

class CompatibilityCalculator:
    """
    Calculate how much User U benefits from connecting with Target T.
    
    Score = weighted sum of:
    1. Mentorship Potential (can T mentor U?) - 22%
    2. Network Value (T's connections useful?) - 18%
    3. Skill Learning (can U learn from T?) - 18%
    4. Role Synergy (same/related field?) - 14%
    5. Alumni Connection (same university?) - 10%  # NEW!
    6. Career Advancement (can T help U's career?) - 10%
    7. Industry Match (same industry?) - 8%
    """
    
    # Weight distribution (updated with alumni)
    WEIGHTS = {
        'mentorship_potential': 0.22,
        'network_value': 0.18,
        'skill_learning': 0.18,
        'role_synergy': 0.14,
        'alumni_connection': 0.10,  # NEW!
        'career_advancement': 0.10,
        'industry_match': 0.08
    }
    
    # Related job categories (for role synergy)
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
    
    def calculate(self, user_profile, target_profile):
        """Calculate compatibility score (0-100)"""
        
        scores = {}
        
        # 1. Mentorship Potential (22%)
        # Higher if target is more experienced and in same/related field
        scores['mentorship_potential'] = self._mentorship_score(user_profile, target_profile)
        
        # 2. Network Value (18%)
        # Based on target's connections and company prestige
        scores['network_value'] = self._network_score(target_profile)
        
        # 3. Skill Learning (18%)
        # Skills target has that user doesn't
        scores['skill_learning'] = self._skill_learning_score(user_profile, target_profile)
        
        # 4. Role Synergy (14%)
        # Same or related job category
        scores['role_synergy'] = self._role_synergy_score(user_profile, target_profile)
        
        # 5. Alumni Connection (10%) - NEW!
        scores['alumni_connection'] = self._alumni_score(user_profile, target_profile)
        
        # 6. Career Advancement (10%)
        # Can target help with career (referrals, advice)?
        scores['career_advancement'] = self._career_score(user_profile, target_profile)
        
        # 7. Industry Match (8%)
        scores['industry_match'] = self._industry_score(user_profile, target_profile)
        
        # Calculate weighted total
        total = sum(self.WEIGHTS[k] * scores[k] for k in scores)
        
        return {
            'total_score': round(total, 2),
            'breakdown': scores
        }
    
    def _mentorship_score(self, user, target):
        """Can target mentor user?"""
        user_exp = user.get('years_experience', 0)
        target_exp = target.get('years_experience', 0)
        
        exp_gap = target_exp - user_exp
        
        # Best mentorship: 3-10 years gap
        if 3 <= exp_gap <= 10:
            base_score = 100
        elif exp_gap > 10:
            base_score = 70  # Too senior, less accessible
        elif exp_gap > 0:
            base_score = 60  # Slight gap, some mentorship
        else:
            base_score = 20  # Same or less experience
        
        # Bonus for related field
        user_role = user.get('job_category', 'other')
        target_role = target.get('job_category', 'other')
        
        if user_role == target_role:
            base_score = min(base_score + 20, 100)
        elif target_role in self.RELATED_ROLES.get(user_role, []):
            base_score = min(base_score + 10, 100)
        
        return base_score
    
    def _network_score(self, target):
        """How valuable is target's network?"""
        connections = target.get('connections', 0)
        
        if connections >= 5000:
            score = 100
        elif connections >= 2000:
            score = 85
        elif connections >= 1000:
            score = 70
        elif connections >= 500:
            score = 55
        elif connections >= 200:
            score = 40
        else:
            score = 25
        
        # Bonus for prestigious company
        company = str(target.get('current_company', '')).lower()
        if any(p in company for p in PRESTIGIOUS):
            score = min(score + 15, 100)
        
        return score
    
    def _skill_learning_score(self, user, target):
        """Can user learn skills from target?"""
        user_skills = set(user.get('skills_list', []) if isinstance(user.get('skills_list'), list) else [])
        target_skills = set(target.get('skills_list', []) if isinstance(target.get('skills_list'), list) else [])
        
        # Skills target has that user doesn't
        new_skills = target_skills - user_skills
        shared_skills = user_skills & target_skills
        
        # More unique skills = higher score
        unique_count = len(new_skills)
        shared_count = len(shared_skills)
        
        if unique_count >= 10:
            score = 90
        elif unique_count >= 5:
            score = 70
        elif unique_count >= 3:
            score = 50
        else:
            score = 30
        
        # Bonus for shared skills (shows common ground)
        if shared_count >= 3:
            score = min(score + 10, 100)
        
        return score
    
    def _role_synergy_score(self, user, target):
        """Are they in same/related field?"""
        user_role = user.get('job_category', 'other')
        target_role = target.get('job_category', 'other')
        
        if user_role == target_role:
            return 100  # Same field
        elif target_role in self.RELATED_ROLES.get(user_role, []):
            return 70   # Related field
        elif user_role == 'other' or target_role == 'other':
            return 40   # Unknown
        else:
            return 20   # Different field
    
    def _career_score(self, user, target):
        """Can target help user's career?"""
        # Based on target's seniority and company
        target_seniority = target.get('seniority_level', 'entry')
        
        seniority_scores = {'entry': 30, 'mid': 50, 'senior': 75, 'executive': 95}
        score = seniority_scores.get(target_seniority, 30)
        
        # Bonus for prestigious company (can refer)
        company = str(target.get('current_company', '')).lower()
        if any(p in company for p in PRESTIGIOUS):
            score = min(score + 15, 100)
        
        return score
    
    def _industry_score(self, user, target):
        """Same industry?"""
        user_ind = user.get('industry', '').lower()
        target_ind = target.get('industry', '').lower()
        
        if user_ind == target_ind:
            return 100
        
        # Related industries
        related = {
            'technology': ['software', 'ai', 'data'],
            'finance': ['fintech', 'banking', 'consulting'],
            'healthcare': ['biotech', 'pharma'],
            'media': ['entertainment', 'advertising']
        }
        
        for ind, related_inds in related.items():
            if (user_ind == ind and target_ind in related_inds) or \
               (target_ind == ind and user_ind in related_inds):
                return 70
        
        return 30
    
    def _alumni_score(self, user, target):
        """Same university? Alumni connections are valuable!"""
        # Try to extract education/university info
        user_edu = user.get('education_list', [])
        target_edu = target.get('education_list', [])
        
        # Extract school names
        user_schools = set()
        target_schools = set()
        
        if isinstance(user_edu, list):
            for edu in user_edu:
                if isinstance(edu, dict) and 'school' in edu:
                    user_schools.add(edu['school'].lower().strip())
        
        if isinstance(target_edu, list):
            for edu in target_edu:
                if isinstance(edu, dict) and 'school' in edu:
                    target_schools.add(edu['school'].lower().strip())
        
        # Check for matching schools
        if user_schools and target_schools:
            # Exact match
            common = user_schools & target_schools
            if common:
                return 100  # Same university!
            
            # Partial match (e.g., "MIT" in "MIT Sloan")
            for u_school in user_schools:
                for t_school in target_schools:
                    if u_school in t_school or t_school in u_school:
                        return 80
        
        return 0  # No alumni connection

# Create calculator instance
calc = CompatibilityCalculator()

# ============================================
# 6. GENERATE TRAINING DATA
# ============================================
print("\n" + "─"*70)
print("📊 GENERATING TRAINING DATA")
print("─"*70)

# Sample profile pairs and calculate compatibility
print("Creating profile pairs with features...")

# Sample profiles for training data
sample_size = 50000  # Create 50k training pairs
np.random.seed(42)

# Create pairs
pairs_data = []
profile_indices = np.random.choice(len(profiles_df), size=sample_size * 2, replace=True)

for i in range(0, len(profile_indices), 2):
    user_idx = profile_indices[i]
    target_idx = profile_indices[i+1]
    
    if user_idx == target_idx:
        continue
    
    user = profiles_df.iloc[user_idx].to_dict()
    target = profiles_df.iloc[target_idx].to_dict()
    
    # Calculate compatibility
    result = calc.calculate(user, target)
    
    pairs_data.append({
        'user_id': user['profile_id'],
        'target_id': target['profile_id'],
        'user_exp': user.get('years_experience', 0),
        'target_exp': target.get('years_experience', 0),
        'user_seniority': user.get('seniority_level', 'entry'),
        'target_seniority': target.get('seniority_level', 'entry'),
        'user_connections': user.get('connections', 0),
        'target_connections': target.get('connections', 0),
        'user_role': user.get('job_category', 'other'),
        'target_role': target.get('job_category', 'other'),
        'user_industry': user.get('industry', ''),
        'target_industry': target.get('industry', ''),
        'user_strength': user.get('profile_strength', 50),
        'target_strength': target.get('profile_strength', 50),
        'mentorship_score': result['breakdown']['mentorship_potential'],
        'network_score': result['breakdown']['network_value'],
        'skill_learning_score': result['breakdown']['skill_learning'],
        'role_synergy_score': result['breakdown']['role_synergy'],
        'alumni_score': result['breakdown']['alumni_connection'],
        'career_score': result['breakdown']['career_advancement'],
        'industry_score': result['breakdown']['industry_match'],
        'compatibility_score': result['total_score']
    })

pairs_df = pd.DataFrame(pairs_data)
print(f"✅ Generated {len(pairs_df):,} training pairs")

# ============================================
# 7. SAVE FEATURE DATA
# ============================================
print("\n" + "─"*70)
print("💾 SAVING DATA")
print("─"*70)

# Save profiles with features
profiles_df.to_csv("data/processed/profiles_with_features.csv", index=False)
print("✅ Saved: profiles_with_features.csv")

# Save training pairs
pairs_df.to_csv("data/processed/training_pairs.csv", index=False)
print("✅ Saved: training_pairs.csv")

# ============================================
# 8. FEATURE SUMMARY
# ============================================
print("\n" + "="*70)
print("📋 FEATURE ENGINEERING SUMMARY")
print("="*70)

print("""
📊 Features Created:

1. PROFILE FEATURES:
   • profile_strength (0-100): Overall value of profile
   • job_category: Role classification
   • keywords: Extracted skill keywords
   
2. COMPATIBILITY FEATURES (with weights):
   
   ┌────────────────────────┬────────┬───────────────────────────────────────┐
   │ Feature                │ Weight │ Description                           │
   ├────────────────────────┼────────┼───────────────────────────────────────┤
   │ mentorship_potential   │  25%   │ Can target mentor you?                │
   │ network_value          │  20%   │ How valuable is their network?        │
   │ skill_learning         │  20%   │ Can you learn skills from them?       │
   │ role_synergy           │  15%   │ Same or related job field?            │
   │ career_advancement     │  10%   │ Can they help your career?            │
   │ industry_match         │  10%   │ Same industry?                        │
   └────────────────────────┴────────┴───────────────────────────────────────┘

3. SCORING SCENARIOS:
   
   Student → Professional:
   • High mentorship (senior can guide)
   • High network value (connections help)
   • High skill learning (lots to learn)
   • Career advancement if at good company
   
   Professional → Professional (same level):
   • Moderate mentorship (peers)
   • Network value based on connections
   • Skill learning if different expertise
   • Role synergy if same field

   Senior → Junior:
   • Lower mentorship (they can't mentor you)
   • Network value still counts
   • Skill learning if they have new tech skills
   • Role synergy matters

4. TRAINING DATA:
   • {len(pairs_df):,} profile pairs
   • Score range: {pairs_df['compatibility_score'].min():.1f} - {pairs_df['compatibility_score'].max():.1f}
   • Mean score: {pairs_df['compatibility_score'].mean():.1f}

🚀 Next Step: Train the model (run train_model_v2.py)
""".format(**{'len(pairs_df)': len(pairs_df), 
              'pairs_df': pairs_df}))

print(f"\n📊 Score Distribution:")
print(pairs_df['compatibility_score'].describe().round(2))
