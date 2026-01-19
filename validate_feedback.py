"""
LinkedIn Match Feedback Validator
Analyzes user feedback to calculate real accuracy metrics for resume
"""

import pandas as pd
import os
from datetime import datetime

def validate_feedback(csv_path=None):
    """
    Validate feedback data and calculate resume-worthy metrics
    """
    
    # Auto-find CSV if not provided
    if csv_path is None:
        # Check common locations
        locations = [
            os.path.expanduser('~/Downloads'),
            os.path.expanduser('~/Desktop'),
            '.'
        ]
        
        for loc in locations:
            if os.path.exists(loc):
                for f in os.listdir(loc):
                    if 'linkedin_match_feedback' in f and f.endswith('.csv'):
                        csv_path = os.path.join(loc, f)
                        break
        
        if csv_path is None:
            print("❌ No feedback CSV found!")
            print("\nTo export your feedback:")
            print("1. Click the extension icon in Chrome")
            print("2. Find 'Feedback Data' section")
            print("3. Click 'Export CSV' button")
            print("\nThen run: python validate_feedback.py path/to/your/file.csv")
            return
    
    print(f"📂 Loading: {csv_path}")
    
    # Load data
    df = pd.read_csv(csv_path)
    
    print(f"\n{'='*60}")
    print("📊 LINKEDIN MATCH FEEDBACK VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data file: {os.path.basename(csv_path)}")
    
    # ==================== BASIC STATS ====================
    total = len(df)
    useful = df['wasUseful'].sum()
    not_useful = total - useful
    
    print(f"\n📈 BASIC STATISTICS")
    print(f"   Total feedback collected: {total}")
    print(f"   Marked useful (👍): {useful} ({useful/total*100:.1f}%)")
    print(f"   Marked not useful (👎): {not_useful} ({not_useful/total*100:.1f}%)")
    
    # ==================== ACCURACY BY SCORE BUCKET ====================
    print(f"\n🎯 ACCURACY BY SCORE BUCKET")
    
    # Define buckets
    df['bucket'] = pd.cut(
        df['score'], 
        bins=[0, 50, 70, 100], 
        labels=['Low (<50)', 'Medium (50-70)', 'High (70+)'],
        include_lowest=True
    )
    
    for bucket in ['High (70+)', 'Medium (50-70)', 'Low (<50)']:
        bucket_df = df[df['bucket'] == bucket]
        if len(bucket_df) > 0:
            if 'High' in bucket or 'Medium' in bucket:
                # For high/medium scores, "useful" is correct
                accuracy = bucket_df['wasUseful'].mean() * 100
                print(f"   {bucket}: {len(bucket_df)} samples, {accuracy:.1f}% marked useful")
            else:
                # For low scores, "not useful" is correct (we predicted skip, user agreed)
                accuracy = (1 - bucket_df['wasUseful'].mean()) * 100
                print(f"   {bucket}: {len(bucket_df)} samples, {accuracy:.1f}% correctly identified as skip")
    
    # ==================== KEY METRICS FOR RESUME ====================
    print(f"\n✅ RESUME-READY METRICS")
    
    # Overall accuracy (treating model's intent)
    # High score + useful = correct, Low score + not useful = correct
    df['correct'] = ((df['score'] >= 50) & (df['wasUseful'])) | ((df['score'] < 50) & (~df['wasUseful']))
    overall_accuracy = df['correct'].mean() * 100
    
    # Precision for recommended connections (score >= 70)
    high_score = df[df['score'] >= 70]
    if len(high_score) > 0:
        high_precision = high_score['wasUseful'].mean() * 100
    else:
        high_precision = 0
    
    # Recall: Of all useful connections, how many did we score high?
    useful_connections = df[df['wasUseful'] == True]
    if len(useful_connections) > 0:
        high_score_recall = (useful_connections['score'] >= 70).mean() * 100
    else:
        high_score_recall = 0
    
    print(f"   → Overall accuracy: {overall_accuracy:.1f}%")
    print(f"   → Precision (high score = useful): {high_precision:.1f}%")
    print(f"   → Recall (useful → high score): {high_score_recall:.1f}%")
    
    # ==================== RESUME BULLET POINTS ====================
    print(f"\n📝 SUGGESTED RESUME BULLET POINTS")
    print(f"{'='*60}")
    
    if total >= 50:
        print(f"""
Point 1 (with real metrics):
"Developed LinkedIn compatibility scoring system with 29 engineered features; 
validated through user feedback collection achieving {overall_accuracy:.0f}% accuracy 
in predicting user-accepted connection recommendations across {total} samples."

Point 2 (precision focused):
"Built Chrome extension for professional networking with {high_precision:.0f}% precision 
for high-value connection recommendations; implemented Jaccard similarity, 
weighted scoring, and LLM-powered analysis via Groq API."
""")
    else:
        print(f"""
⚠️  You have {total} samples. Collect at least 50-100 for credible metrics.

Current tentative metrics:
- Accuracy: {overall_accuracy:.0f}%
- High-score precision: {high_precision:.0f}%

Keep collecting feedback, then re-run this script!
""")
    
    # ==================== DETAILED BREAKDOWN ====================
    print(f"\n📋 DETAILED BREAKDOWN BY PROFILE")
    print(f"{'='*60}")
    print(df[['profileName', 'score', 'wasUseful']].to_string())
    
    return {
        'total': total,
        'overall_accuracy': overall_accuracy,
        'high_precision': high_precision,
        'high_recall': high_score_recall
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        validate_feedback(sys.argv[1])
    else:
        validate_feedback()
