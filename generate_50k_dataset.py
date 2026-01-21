"""
LinkedIn Match - 50K Synthetic Dataset Generator
=================================================
Generates realistic LinkedIn profile pairs with compatibility scores.

Features:
- 50,000 profile pairs
- Realistic job titles, skills, industries
- Domain-logic based compatibility scoring
- Ready for deep learning + XGBoost training

Author: Likitha Gedipudi
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import random
import json
from datetime import datetime

np.random.seed(42)
random.seed(42)

# ============================================================
# REALISTIC LINKEDIN DATA POOLS
# ============================================================

JOB_FAMILIES = {
    'DATA': {
        'titles': [
            'Data Scientist', 'Senior Data Scientist', 'Staff Data Scientist',
            'Data Analyst', 'Senior Data Analyst', 'Business Analyst',
            'ML Engineer', 'Senior ML Engineer', 'Machine Learning Engineer',
            'Data Engineer', 'Senior Data Engineer', 'Analytics Engineer',
            'AI Engineer', 'Research Scientist', 'Applied Scientist',
            'Quantitative Analyst', 'Statistician', 'BI Developer'
        ],
        'skills': [
            'Python', 'SQL', 'Machine Learning', 'Deep Learning', 'TensorFlow',
            'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Statistics',
            'Data Analysis', 'Data Visualization', 'Tableau', 'Power BI',
            'Spark', 'Hadoop', 'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes',
            'NLP', 'Computer Vision', 'Time Series', 'A/B Testing', 'R',
            'Databricks', 'Snowflake', 'dbt', 'Airflow', 'MLflow', 'LLMs'
        ],
        'adjacent': ['SOFTWARE', 'PRODUCT', 'FINANCE']
    },
    'SOFTWARE': {
        'titles': [
            'Software Engineer', 'Senior Software Engineer', 'Staff Engineer',
            'Backend Developer', 'Frontend Developer', 'Full Stack Developer',
            'DevOps Engineer', 'SRE', 'Platform Engineer',
            'Solutions Architect', 'Technical Lead', 'Engineering Manager',
            'iOS Developer', 'Android Developer', 'Mobile Engineer'
        ],
        'skills': [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI',
            'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes', 'CI/CD',
            'PostgreSQL', 'MongoDB', 'Redis', 'GraphQL', 'REST APIs',
            'Microservices', 'System Design', 'Git', 'Linux', 'Terraform'
        ],
        'adjacent': ['DATA', 'PRODUCT', 'DESIGN']
    },
    'PRODUCT': {
        'titles': [
            'Product Manager', 'Senior Product Manager', 'Group Product Manager',
            'Product Owner', 'Technical Product Manager', 'Product Lead',
            'Product Director', 'VP of Product', 'Chief Product Officer',
            'Product Analyst', 'Growth Product Manager'
        ],
        'skills': [
            'Product Strategy', 'Roadmapping', 'User Research', 'A/B Testing',
            'Agile', 'Scrum', 'JIRA', 'Confluence', 'Analytics', 'SQL',
            'Figma', 'PRDs', 'Go-to-Market', 'Stakeholder Management',
            'OKRs', 'KPIs', 'Market Research', 'Competitive Analysis'
        ],
        'adjacent': ['DATA', 'SOFTWARE', 'DESIGN']
    },
    'DESIGN': {
        'titles': [
            'UX Designer', 'Senior UX Designer', 'UI Designer',
            'Product Designer', 'UX Researcher', 'Interaction Designer',
            'Visual Designer', 'Design Lead', 'Head of Design'
        ],
        'skills': [
            'Figma', 'Sketch', 'Adobe XD', 'User Research', 'Prototyping',
            'Wireframing', 'Design Systems', 'Usability Testing',
            'Information Architecture', 'Visual Design', 'Typography',
            'Design Thinking', 'Accessibility', 'Motion Design'
        ],
        'adjacent': ['PRODUCT', 'SOFTWARE']
    },
    'FINANCE': {
        'titles': [
            'Financial Analyst', 'Senior Financial Analyst', 'Investment Analyst',
            'Quantitative Analyst', 'Risk Analyst', 'Portfolio Manager',
            'Investment Banker', 'Equity Research Analyst', 'FP&A Analyst',
            'CFO', 'Finance Manager', 'Controller'
        ],
        'skills': [
            'Financial Modeling', 'Excel', 'SQL', 'Python', 'Valuation',
            'DCF', 'M&A', 'Due Diligence', 'Bloomberg Terminal', 'VBA',
            'Financial Reporting', 'Budgeting', 'Forecasting', 'Risk Management'
        ],
        'adjacent': ['DATA', 'CONSULTING']
    },
    'CONSULTING': {
        'titles': [
            'Consultant', 'Senior Consultant', 'Manager', 'Senior Manager',
            'Principal', 'Partner', 'Strategy Consultant', 'Management Consultant'
        ],
        'skills': [
            'Strategy', 'Problem Solving', 'PowerPoint', 'Excel', 'Data Analysis',
            'Client Management', 'Project Management', 'Business Development',
            'Market Sizing', 'Competitive Analysis', 'Financial Analysis'
        ],
        'adjacent': ['FINANCE', 'PRODUCT']
    },
    'MARKETING': {
        'titles': [
            'Marketing Manager', 'Growth Manager', 'Product Marketing Manager',
            'Digital Marketing Manager', 'Content Marketing Manager',
            'Brand Manager', 'CMO', 'Marketing Director', 'SEO Specialist'
        ],
        'skills': [
            'Digital Marketing', 'SEO', 'SEM', 'Content Strategy', 'Social Media',
            'Google Analytics', 'Marketing Automation', 'Email Marketing',
            'Brand Strategy', 'Campaign Management', 'A/B Testing'
        ],
        'adjacent': ['PRODUCT', 'DATA']
    },
    'HR': {
        'titles': [
            'HR Manager', 'Recruiter', 'Technical Recruiter', 'Talent Acquisition',
            'HR Business Partner', 'People Operations', 'CHRO', 'HR Director'
        ],
        'skills': [
            'Recruiting', 'Talent Management', 'Employee Relations', 'HRIS',
            'Compensation', 'Benefits', 'Performance Management', 'Onboarding'
        ],
        'adjacent': ['CONSULTING']
    }
}

COMPANIES = {
    'FAANG': ['Google', 'Meta', 'Amazon', 'Apple', 'Netflix', 'Microsoft'],
    'TIER1_TECH': ['Uber', 'Airbnb', 'Stripe', 'Databricks', 'Snowflake', 'OpenAI', 'Anthropic'],
    'TIER2_TECH': ['Salesforce', 'Adobe', 'Intuit', 'Atlassian', 'Shopify', 'Square', 'Twilio'],
    'BIG_FINANCE': ['Goldman Sachs', 'JP Morgan', 'Morgan Stanley', 'Citadel', 'Two Sigma'],
    'CONSULTING': ['McKinsey', 'BCG', 'Bain', 'Deloitte', 'Accenture'],
    'STARTUPS': ['Series A Startup', 'Series B Startup', 'Early Stage Startup', 'Tech Startup'],
    'ENTERPRISE': ['IBM', 'Oracle', 'SAP', 'Cisco', 'Dell', 'HP'],
    'RETAIL': ['Walmart', 'Target', 'Costco', 'Home Depot', 'Best Buy'],
    'OTHER': ['Fortune 500 Company', 'Multinational Corp', 'Growing Company']
}

LOCATIONS = [
    'San Francisco Bay Area', 'New York City', 'Seattle', 'Austin',
    'Boston', 'Los Angeles', 'Chicago', 'Denver', 'Atlanta', 'Remote',
    'London', 'Toronto', 'Bangalore', 'Singapore'
]

EDUCATION = [
    'Stanford', 'MIT', 'Carnegie Mellon', 'UC Berkeley', 'Harvard',
    'Georgia Tech', 'University of Washington', 'University of Michigan',
    'Cornell', 'Columbia', 'UCLA', 'UT Austin', 'UIUC',
    'State University', 'Private University', 'International University'
]

SENIORITY_LEVELS = ['Entry', 'Mid', 'Senior', 'Lead', 'Director', 'VP', 'C-Level']

# ============================================================
# PROFILE GENERATION
# ============================================================

def generate_profile(family: str = None) -> Dict:
    """Generate a single realistic LinkedIn profile"""
    
    if family is None:
        family = random.choice(list(JOB_FAMILIES.keys()))
    
    job_data = JOB_FAMILIES[family]
    
    # Seniority and years of experience
    seniority_idx = np.random.choice(len(SENIORITY_LEVELS), p=[0.15, 0.25, 0.30, 0.15, 0.10, 0.04, 0.01])
    seniority = SENIORITY_LEVELS[seniority_idx]
    
    years_exp_ranges = {
        'Entry': (0, 2), 'Mid': (2, 5), 'Senior': (5, 10),
        'Lead': (8, 15), 'Director': (12, 20), 'VP': (15, 25), 'C-Level': (20, 35)
    }
    years_exp = random.randint(*years_exp_ranges[seniority])
    
    # Job title
    title = random.choice(job_data['titles'])
    if seniority in ['Lead', 'Director'] and 'Senior' not in title and 'Lead' not in title:
        title = f"Senior {title}" if random.random() > 0.5 else f"{title} Lead"
    
    # Company
    company_tier = np.random.choice(
        list(COMPANIES.keys()),
        p=[0.10, 0.10, 0.15, 0.08, 0.07, 0.20, 0.10, 0.10, 0.10]
    )
    company = random.choice(COMPANIES[company_tier])
    
    # Skills (pick 5-15 from family skills + some random)
    num_skills = random.randint(5, 15)
    skills = random.sample(job_data['skills'], min(num_skills, len(job_data['skills'])))
    
    # Add some cross-functional skills
    if random.random() > 0.5:
        adjacent_family = random.choice(job_data['adjacent'])
        extra_skills = random.sample(JOB_FAMILIES[adjacent_family]['skills'], min(3, len(JOB_FAMILIES[adjacent_family]['skills'])))
        skills.extend(extra_skills[:2])
    
    # Education
    education = random.choice(EDUCATION)
    has_grad_degree = random.random() > 0.6
    degree = random.choice(['MS', 'MBA', 'PhD']) if has_grad_degree else 'BS'
    
    # Location
    location = random.choice(LOCATIONS)
    
    # Connections
    connection_base = {'Entry': 200, 'Mid': 400, 'Senior': 600, 'Lead': 800, 'Director': 1000, 'VP': 1500, 'C-Level': 2000}
    connections = int(np.random.normal(connection_base[seniority], connection_base[seniority] * 0.3))
    connections = max(50, min(connections, 5000))
    
    # Generate headline
    headline = f"{title} at {company}"
    if random.random() > 0.5:
        headline += f" | {' | '.join(random.sample(skills, min(3, len(skills))))}"
    if has_grad_degree and random.random() > 0.7:
        headline += f" | {degree}"
    
    return {
        'family': family,
        'title': title,
        'company': company,
        'company_tier': company_tier,
        'headline': headline,
        'skills': skills,
        'seniority': seniority,
        'seniority_level': seniority_idx,
        'years_exp': years_exp,
        'education': education,
        'degree': degree,
        'has_grad_degree': has_grad_degree,
        'location': location,
        'connections': connections
    }

# ============================================================
# COMPATIBILITY SCORE CALCULATION
# ============================================================

def calculate_compatibility(user: Dict, target: Dict) -> Tuple[float, Dict]:
    """
    Calculate compatibility score based on domain logic.
    Returns score (0-100) and feature breakdown.
    """
    
    features = {}
    
    # 1. SKILL OVERLAP (0-100)
    user_skills = set(s.lower() for s in user['skills'])
    target_skills = set(s.lower() for s in target['skills'])
    
    if len(user_skills) > 0 and len(target_skills) > 0:
        intersection = len(user_skills & target_skills)
        union = len(user_skills | target_skills)
        skill_jaccard = intersection / union
        skill_overlap = min(intersection / min(len(user_skills), len(target_skills)), 1.0)
        features['skill_overlap'] = skill_overlap * 100
        features['skill_jaccard'] = skill_jaccard * 100
        features['common_skills_count'] = intersection
    else:
        features['skill_overlap'] = 0
        features['skill_jaccard'] = 0
        features['common_skills_count'] = 0
    
    # 2. ROLE FAMILY AFFINITY (0-100)
    if user['family'] == target['family']:
        features['role_family_match'] = 100
    elif target['family'] in JOB_FAMILIES[user['family']].get('adjacent', []):
        features['role_family_match'] = 70
    else:
        features['role_family_match'] = 20
    
    # 3. SENIORITY ALIGNMENT (0-100)
    seniority_diff = abs(user['seniority_level'] - target['seniority_level'])
    if seniority_diff == 0:
        features['seniority_match'] = 100  # Peer
    elif seniority_diff == 1:
        features['seniority_match'] = 90   # Close peer
    elif seniority_diff == 2:
        features['seniority_match'] = 70   # Potential mentor/mentee
    else:
        features['seniority_match'] = max(40 - seniority_diff * 10, 10)
    
    # Bonus if target is senior (mentor potential)
    features['target_is_senior'] = 1 if target['seniority_level'] > user['seniority_level'] else 0
    
    # 4. COMPANY TIER ALIGNMENT (0-100)
    tier_scores = {'FAANG': 100, 'TIER1_TECH': 90, 'TIER2_TECH': 80, 'BIG_FINANCE': 85, 
                   'CONSULTING': 80, 'STARTUPS': 70, 'ENTERPRISE': 60, 'RETAIL': 55, 'OTHER': 50}
    
    user_tier_score = tier_scores.get(user['company_tier'], 50)
    target_tier_score = tier_scores.get(target['company_tier'], 50)
    
    # Higher score if target is at same or better company
    if target_tier_score >= user_tier_score:
        features['company_tier_match'] = min(100, 70 + (target_tier_score - user_tier_score) / 2)
    else:
        features['company_tier_match'] = max(30, 70 - (user_tier_score - target_tier_score) / 2)
    
    # 5. LOCATION ALIGNMENT (0-100)
    features['same_location'] = 100 if user['location'] == target['location'] else 50
    features['remote_friendly'] = 80 if 'Remote' in [user['location'], target['location']] else 50
    
    # 6. EDUCATION ALIGNMENT (0-100)
    if user['education'] == target['education']:
        features['alumni_match'] = 100
    else:
        features['alumni_match'] = 40
    features['target_has_grad_degree'] = 100 if target['has_grad_degree'] else 50
    
    # 7. NETWORK SIZE (0-100)
    features['target_connections'] = min(target['connections'] / 20, 100)  # Normalize to 0-100
    
    # 8. EXPERIENCE ALIGNMENT
    exp_diff = abs(user['years_exp'] - target['years_exp'])
    features['experience_alignment'] = max(100 - exp_diff * 5, 20)
    
    # 9. RECRUITER BONUS
    features['is_recruiter'] = 100 if target['family'] == 'HR' else 0
    
    # ============================================================
    # WEIGHTED FINAL SCORE
    # ============================================================
    weights = {
        'skill_overlap': 0.20,
        'role_family_match': 0.20,
        'seniority_match': 0.12,
        'company_tier_match': 0.15,
        'same_location': 0.05,
        'target_has_grad_degree': 0.03,
        'target_connections': 0.08,
        'experience_alignment': 0.10,
        'alumni_match': 0.07
    }
    
    weighted_score = sum(features.get(k, 50) * v for k, v in weights.items())
    
    # Add noise (±5 points) for realism
    noise = np.random.normal(0, 3)
    final_score = np.clip(weighted_score + noise, 0, 100)
    
    features['compatibility_score'] = round(final_score, 1)
    
    return final_score, features

# ============================================================
# DATASET GENERATION
# ============================================================

def generate_dataset(n_samples: int = 50000, user_family: str = 'DATA') -> pd.DataFrame:
    """Generate dataset of profile pairs with compatibility scores"""
    
    print(f"🚀 Generating {n_samples:,} profile pairs...")
    print(f"   User family: {user_family}")
    
    data = []
    
    # Generate a pool of user profiles (variation)
    print("   Creating user profile pool...")
    user_profiles = [generate_profile(user_family) for _ in range(100)]
    
    for i in range(n_samples):
        if i % 10000 == 0 and i > 0:
            print(f"   Progress: {i:,}/{n_samples:,} ({i/n_samples*100:.0f}%)")
        
        # Pick a random user from pool
        user = random.choice(user_profiles)
        
        # Generate target profile (varied families)
        target_family_weights = [0.30, 0.25, 0.15, 0.05, 0.08, 0.05, 0.07, 0.05]
        target_family = np.random.choice(list(JOB_FAMILIES.keys()), p=target_family_weights)
        target = generate_profile(target_family)
        
        # Calculate compatibility
        score, features = calculate_compatibility(user, target)
        
        row = {
            # User features
            'user_headline': user['headline'],
            'user_title': user['title'],
            'user_family': user['family'],
            'user_seniority': user['seniority'],
            'user_seniority_level': user['seniority_level'],
            'user_years_exp': user['years_exp'],
            'user_company_tier': user['company_tier'],
            'user_location': user['location'],
            'user_skills': '|'.join(user['skills']),
            'user_connections': user['connections'],
            
            # Target features
            'target_headline': target['headline'],
            'target_title': target['title'],
            'target_family': target['family'],
            'target_seniority': target['seniority'],
            'target_seniority_level': target['seniority_level'],
            'target_years_exp': target['years_exp'],
            'target_company_tier': target['company_tier'],
            'target_location': target['location'],
            'target_skills': '|'.join(target['skills']),
            'target_connections': target['connections'],
            'target_has_grad_degree': target['has_grad_degree'],
            
            # Computed features
            **features,
            
            # Target
            'compatibility_score': score
        }
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    print(f"\n✅ Generated {len(df):,} samples")
    print(f"   Score distribution:")
    print(f"   - Mean: {df['compatibility_score'].mean():.1f}")
    print(f"   - Std:  {df['compatibility_score'].std():.1f}")
    print(f"   - Min:  {df['compatibility_score'].min():.1f}")
    print(f"   - Max:  {df['compatibility_score'].max():.1f}")
    
    return df

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("📊 LINKEDIN MATCH - SYNTHETIC DATASET GENERATOR")
    print("="*60)
    
    # Generate 50K samples
    df = generate_dataset(n_samples=50000, user_family='DATA')
    
    # Save dataset
    output_path = 'linkedin_match_50k_synthetic.csv'
    df.to_csv(output_path, index=False)
    print(f"\n💾 Saved to {output_path}")
    
    # Show sample
    print("\n📋 Sample rows:")
    print(df[['user_headline', 'target_headline', 'skill_overlap', 'role_family_match', 'compatibility_score']].head(10).to_string())
    
    # Feature stats
    print("\n📊 Feature correlations with compatibility_score:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlations = df[numeric_cols].corr()['compatibility_score'].sort_values(ascending=False)
    print(correlations.head(15))
