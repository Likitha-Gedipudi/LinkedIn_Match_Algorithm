"""
LinkedIn Compatibility Model - Part 1: EDA & Data Cleaning
===========================================================
Explore the data and prepare it for feature engineering.
"""

import pandas as pd
import numpy as np
import json
import ast
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("📊 LINKEDIN COMPATIBILITY MODEL - EDA & DATA CLEANING")
print("="*70)

# ============================================
# 1. LOAD DATA
# ============================================
print("\n" + "─"*70)
print("📂 LOADING DATA")
print("─"*70)

# Load profiles
profiles_df = pd.read_csv("data/processed/profiles_enhanced.csv")
print(f"✅ Profiles loaded: {len(profiles_df):,} records")

# Load compatibility pairs (sample for EDA)
pairs_df = pd.read_csv("data/processed/compatibility_pairs.csv", nrows=100000)
print(f"✅ Pairs loaded: {len(pairs_df):,} records (sampled)")

# ============================================
# 2. DATA CLEANING
# ============================================
print("\n" + "─"*70)
print("🧹 DATA CLEANING")
print("─"*70)

# Check for missing values
print("\n📋 Missing Values in Profiles:")
missing = profiles_df.isnull().sum()
missing_pct = (missing / len(profiles_df) * 100).round(2)
for col in profiles_df.columns:
    if missing[col] > 0:
        print(f"   {col}: {missing[col]} ({missing_pct[col]}%)")

if missing.sum() == 0:
    print("   ✅ No missing values!")

# Parse JSON columns
print("\n🔧 Parsing JSON columns...")

def safe_parse_json(x):
    """Safely parse JSON string or return empty list"""
    if pd.isna(x):
        return []
    if isinstance(x, list):
        return x
    try:
        return json.loads(x.replace("'", '"'))
    except:
        try:
            return ast.literal_eval(x)
        except:
            return []

# Parse skills
profiles_df['skills_list'] = profiles_df['skills'].apply(safe_parse_json)
profiles_df['skills_count'] = profiles_df['skills_list'].apply(len)

# Parse experience
profiles_df['experience_list'] = profiles_df['experience'].apply(safe_parse_json)
profiles_df['experience_count'] = profiles_df['experience_list'].apply(len)

# Parse education
profiles_df['education_list'] = profiles_df['education'].apply(safe_parse_json)
profiles_df['education_count'] = profiles_df['education_list'].apply(len)

print("   ✅ JSON columns parsed!")

# ============================================
# 3. EXPLORATORY DATA ANALYSIS
# ============================================
print("\n" + "─"*70)
print("📈 EXPLORATORY DATA ANALYSIS")
print("─"*70)

# 3.1 Experience Distribution
print("\n📊 Experience Distribution:")
exp_bins = [0, 2, 5, 10, 15, 100]
exp_labels = ['0-2 (Entry)', '3-5 (Junior)', '6-10 (Mid)', '11-15 (Senior)', '15+ (Executive)']
profiles_df['exp_category'] = pd.cut(profiles_df['years_experience'], bins=exp_bins, labels=exp_labels)
print(profiles_df['exp_category'].value_counts().to_string())

# 3.2 Seniority Distribution
print("\n📊 Seniority Distribution:")
print(profiles_df['seniority_level'].value_counts().to_string())

# 3.3 Industry Distribution
print("\n📊 Top 10 Industries:")
print(profiles_df['industry'].value_counts().head(10).to_string())

# 3.4 Connection Distribution
print("\n📊 Connection Distribution:")
conn_stats = profiles_df['connections'].describe()
print(f"   Min: {conn_stats['min']:.0f}")
print(f"   25%: {conn_stats['25%']:.0f}")
print(f"   50%: {conn_stats['50%']:.0f}")
print(f"   75%: {conn_stats['75%']:.0f}")
print(f"   Max: {conn_stats['max']:.0f}")

# 3.5 Skills Analysis
print("\n📊 Skills Analysis:")
all_skills = []
for skills in profiles_df['skills_list']:
    all_skills.extend(skills)
skill_counts = pd.Series(all_skills).value_counts()
print(f"   Total unique skills: {len(skill_counts)}")
print(f"\n   Top 15 Skills:")
for skill, count in skill_counts.head(15).items():
    pct = count / len(profiles_df) * 100
    print(f"      {skill}: {count} ({pct:.1f}%)")

# 3.6 Compatibility Score Distribution
print("\n📊 Compatibility Score Distribution:")
score_stats = pairs_df['compatibility_score'].describe()
print(f"   Min: {score_stats['min']:.2f}")
print(f"   25%: {score_stats['25%']:.2f}")
print(f"   50%: {score_stats['50%']:.2f}")
print(f"   75%: {score_stats['75%']:.2f}")
print(f"   Max: {score_stats['max']:.2f}")

# 3.7 Feature Correlations
print("\n📊 Feature Correlations with Compatibility Score:")
numeric_cols = ['skill_match_score', 'network_value_a_to_b', 'network_value_b_to_a',
                'career_alignment_score', 'experience_gap', 'industry_match',
                'geographic_score', 'seniority_match']
correlations = pairs_df[numeric_cols + ['compatibility_score']].corr()['compatibility_score'].drop('compatibility_score')
correlations = correlations.sort_values(ascending=False)
for feat, corr in correlations.items():
    bar = '█' * int(abs(corr) * 30)
    sign = '+' if corr > 0 else '-'
    print(f"   {feat:<30} {sign}{abs(corr):.3f} {bar}")

# ============================================
# 4. ROLE/POSITION ANALYSIS
# ============================================
print("\n" + "─"*70)
print("💼 ROLE & POSITION ANALYSIS")
print("─"*70)

# Extract job keywords from headlines
job_keywords = {
    'data': ['data', 'analytics', 'analyst', 'scientist', 'ml', 'machine learning', 'ai'],
    'software': ['software', 'developer', 'engineer', 'sde', 'programmer', 'backend', 'frontend', 'full stack'],
    'product': ['product', 'pm', 'manager', 'owner'],
    'design': ['design', 'ui', 'ux', 'creative', 'graphic'],
    'business': ['business', 'consultant', 'strategy', 'operations', 'sales'],
    'executive': ['ceo', 'cto', 'cfo', 'coo', 'director', 'vp', 'head', 'chief'],
    'student': ['student', 'intern', 'graduate', 'fresher', 'junior']
}

def categorize_role(headline):
    """Categorize a headline into job categories"""
    if pd.isna(headline):
        return 'other'
    headline_lower = headline.lower()
    for category, keywords in job_keywords.items():
        for kw in keywords:
            if kw in headline_lower:
                return category
    return 'other'

profiles_df['role_category'] = profiles_df['headline'].apply(categorize_role)

print("\n📊 Role Categories:")
print(profiles_df['role_category'].value_counts().to_string())

# ============================================
# 5. COMPANY ANALYSIS
# ============================================
print("\n" + "─"*70)
print("🏢 COMPANY ANALYSIS")
print("─"*70)

print("\n📊 Top 15 Companies:")
print(profiles_df['current_company'].value_counts().head(15).to_string())

# Identify prestigious companies
PRESTIGIOUS_COMPANIES = [
    'google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 'netflix',
    'tesla', 'uber', 'airbnb', 'stripe', 'linkedin', 'twitter', 'salesforce',
    'oracle', 'ibm', 'intel', 'nvidia', 'adobe', 'spotify'
]

def is_prestigious(company):
    if pd.isna(company):
        return False
    return any(p in company.lower() for p in PRESTIGIOUS_COMPANIES)

profiles_df['prestigious_company'] = profiles_df['current_company'].apply(is_prestigious)
print(f"\n📊 Prestigious Company: {profiles_df['prestigious_company'].sum()} profiles ({profiles_df['prestigious_company'].mean()*100:.1f}%)")

# ============================================
# 6. SAVE CLEANED DATA
# ============================================
print("\n" + "─"*70)
print("💾 SAVING CLEANED DATA")
print("─"*70)

# Save enhanced profiles
output_path = "data/processed/profiles_cleaned.csv"
profiles_df.to_csv(output_path, index=False)
print(f"✅ Saved: {output_path}")

# ============================================
# SUMMARY
# ============================================
print("\n" + "="*70)
print("📋 EDA SUMMARY")
print("="*70)

print(f"""
📊 Dataset Overview:
   • Total Profiles: {len(profiles_df):,}
   • Total Pairs: 4,999,890+
   • Unique Skills: {len(skill_counts)}
   • Industries: {profiles_df['industry'].nunique()}

🔍 Key Insights:
   1. Seniority levels are well distributed
   2. Skills are diverse with {len(skill_counts)} unique skills
   3. Top correlating features with compatibility:
      - {correlations.index[0]}: {correlations.iloc[0]:.3f}
      - {correlations.index[1]}: {correlations.iloc[1]:.3f}
      - {correlations.index[2]}: {correlations.iloc[2]:.3f}

⚠️ Observations:
   - skill_complementarity_score is always 0 (not useful)
   - Compatibility scores range only 19-63 (not 0-100)
   - Features seem to directly compute target (possible data leakage)

🚀 Next Step: Feature Engineering (run feature_engineering.py)
""")
