# LinkedIn Professional Match Dataset

## 📊 Dataset Overview

This dataset contains **50,000+ synthetic professional profiles** and **500,000+ compatibility pairs** for building and training professional networking recommendation systems. Perfect for machine learning research, recommendation systems, and network analysis.

### What's Included

| File | Size | Records | Description |
|------|------|---------|-------------|
| `profiles_enhanced.csv` | 68 MB | 50,000+ | Professional profiles with 30+ features |
| `compatibility_pairs_enhanced.csv` | 181 MB | 500,000+ | Profile pairs with compatibility scores |
| `skills_network.csv` | 5 KB | 1,000+ | Skill supply/demand analysis |
| `conversation_starters.csv` | 62 KB | 10,000+ | AI-generated icebreakers |
| `hidden_gems_top_profiles.csv` | 470 B | 50 | Rising stars and super connectors |
| `red_flags_top_profiles.csv` | 470 B | 50 | Profiles with potential issues |
| `compatibility_scorer.joblib` | 3.5 MB | 1 model | Pre-trained Gradient Boosting model |
| `training_results.json` | 483 B | - | Model training metrics |

**Total Dataset Size:** ~253 MB

---

## 🎯 Use Cases

### Machine Learning
- Train compatibility prediction models
- Develop recommendation systems
- Test feature engineering techniques
- Benchmark ML algorithms
- Explainable AI research

### Data Science
- Professional network analysis
- Skill gap analysis
- Career trajectory modeling
- Geographic clustering
- Industry insights

### Research
- Social network analysis
- Professional networking patterns
- Skill market dynamics
- Career development research

---

## 📋 Dataset Schema

### 1. Profiles Dataset (`profiles_enhanced.csv`)

**50,000+ professional profiles with:**

| Column | Type | Description |
|--------|------|-------------|
| `profile_id` | string | Unique identifier |
| `name` | string | Professional name |
| `headline` | string | Professional headline |
| `location` | string | Geographic location |
| `industry` | string | Industry category |
| `connections` | int | Number of connections (100-5000) |
| `skills` | string | Comma-separated skills |
| `experience_years` | int | Total years of experience |
| `education` | string | Educational background |
| `certifications` | string | Professional certifications |
| `languages` | string | Languages spoken |
| `volunteer_work` | string | Volunteer experiences |
| `honors_awards` | string | Awards and recognition |
| `current_position` | string | Current job title |
| `current_company` | string | Current employer |
| `seniority_level` | string | Career level (Entry/Mid/Senior/Executive) |
| `is_open_to_work` | boolean | Open to opportunities |
| `is_hiring` | boolean | Currently hiring |
| `profile_completeness` | float | Profile completion % (0-100) |
| `endorsement_count` | int | Total endorsements |
| `recommendation_count` | int | LinkedIn recommendations |
| `post_frequency` | string | Content creation frequency |
| `engagement_rate` | float | Content engagement % |
| `joined_date` | date | Profile creation date |
| `last_activity` | date | Most recent activity |
| `premium_status` | boolean | Premium account |
| `creator_mode` | boolean | Creator mode enabled |
| `visibility` | string | Profile visibility setting |

**Statistics:**
- Average connections: 1,500
- Average experience: 8 years
- Average skills: 12 per profile
- Industries covered: 50+
- Locations: 100+ cities worldwide

### 2. Compatibility Pairs Dataset (`compatibility_pairs_enhanced.csv`)

**500,000+ profile pairs with compatibility analysis:**

| Column | Type | Description |
|--------|------|-------------|
| `pair_id` | string | Unique pair identifier |
| `profile_a_id` | string | First profile ID |
| `profile_b_id` | string | Second profile ID |
| **Compatibility Scores (0-100)** |
| `compatibility_score` | float | Overall compatibility (0-100) |
| `skill_match_score` | float | Overlapping skills |
| `skill_complementarity_score` | float | Complementary skills |
| `network_value_a_to_b` | float | Value A brings to B |
| `network_value_b_to_a` | float | Value B brings to A |
| `career_alignment_score` | float | Career stage alignment |
| `industry_match` | float | Industry similarity |
| `geographic_score` | float | Location compatibility |
| `seniority_match` | float | Seniority level match |
| **Derived Features** |
| `network_value_avg` | float | Average network value |
| `network_value_diff` | float | Network value difference |
| `skill_total` | float | Total skill score |
| `skill_balance` | float | Skill balance metric |
| `exp_gap_squared` | float | Experience gap squared |
| `is_mentorship_gap` | boolean | Ideal mentor-mentee gap (3-7 years) |
| `is_peer` | boolean | Peer relationship (0-2 years gap) |
| `skill_x_network` | float | Skill × Network interaction |
| `career_x_industry` | float | Career × Industry interaction |
| **Analysis** |
| `recommendation` | string | Match recommendation |
| `mutual_benefit_explanation` | string | Detailed explanation |
| `roi_job_opportunity` | float | Job opportunity score |
| `roi_mentorship_value` | float | Mentorship value score |
| `roi_collaboration_potential` | float | Collaboration score |
| `experience_gap` | int | Years of experience difference |
| `conversation_starter` | string | Personalized icebreaker |

**Score Distribution:**
- Mean compatibility: 65/100
- Excellent matches (80+): 15%
- Good matches (60-79): 40%
- Moderate matches (40-59): 35%
- Low matches (<40): 10%

### 3. Pre-trained Model (`compatibility_scorer.joblib`)

**Model Details:**
- **Algorithm:** Gradient Boosting Regressor (scikit-learn)
- **Features:** 18 engineered features
- **Performance:** R²=1.000, MAE=0.070, RMSE=0.091
- **Training Data:** 500K pairs
- **Framework:** scikit-learn 1.3+

**Usage:**
```python
import joblib
import pandas as pd

# Load model
model_data = joblib.load('compatibility_scorer.joblib')
pipeline = model_data['pipeline']
feature_names = model_data['feature_names']

# Predict
features_df = pd.DataFrame([{ ... }])  # 18 features
score = pipeline.predict(features_df)[0]
print(f"Compatibility: {score:.1f}/100")
```

---

## 🚀 Quick Start

### Load and Explore Data

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load datasets
profiles = pd.read_csv('profiles_enhanced.csv')
pairs = pd.read_csv('compatibility_pairs_enhanced.csv')

print(f"Profiles: {len(profiles):,}")
print(f"Pairs: {len(pairs):,}")

# Explore distributions
profiles['industry'].value_counts().head(10).plot(kind='barh')
plt.title('Top 10 Industries')
plt.show()
```

### Load Pre-trained Model

```python
import joblib

# Load model
model_data = joblib.load('compatibility_scorer.joblib')
pipeline = model_data['pipeline']
feature_names = model_data['feature_names']

# Make prediction
X_test = pairs[feature_names].head(1)
score = pipeline.predict(X_test)[0]
print(f"Predicted score: {score:.1f}/100")
```

### Train Your Own Model

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# Prepare data
feature_cols = [
    'skill_match_score', 'skill_complementarity_score',
    'network_value_avg', 'career_alignment_score',
    # ... other features
]
X = pairs[feature_cols]
y = pairs['compatibility_score']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
print(f"R² Score: {r2:.3f}")
```

---

## 💡 Feature Engineering Ideas

### Current Features
✅ Skill matching and complementarity  
✅ Network value (bidirectional)  
✅ Career alignment  
✅ Geographic compatibility  
✅ Experience gap analysis  

### Enhancement Ideas
🔥 **Skill embeddings** - Word2Vec/BERT for skill similarity  
🔥 **Temporal features** - Career progression patterns  
🔥 **Graph features** - Network centrality, clustering  
🔥 **Content analysis** - NLP on posts and articles  
🔥 **Behavioral features** - Engagement patterns  

---

## 🤝 Contributing to the Project

This dataset is part of an **open-source project**!

**GitHub Repository:** https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm

**How to Contribute:**
1. 🐛 Report bugs and issues
2. 💡 Suggest new features
3. 📊 Create visualizations and insights
4. 🤖 Improve the ML models
5. 📝 Enhance documentation
6. 🌐 Build applications using this data

See [CONTRIBUTING.md](https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm/blob/main/CONTRIBUTING.md) for detailed guidelines.

---

## 📚 Resources

### Notebooks
- 📓 **Starter Notebook:** Data exploration and model usage
- 📊 **EDA Notebook:** Comprehensive exploratory analysis
- 🤖 **Model Training:** Train custom models

### Documentation
- 📖 **Full Documentation:** [GitHub Repository](https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm)
- 🔧 **API Documentation:** [Live API](https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com/docs)
- 🎓 **Chrome Extension:** [Extension Folder](https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm/tree/main/chrome-extension)

### Live Demo
- 🌐 **API Endpoint:** https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com
- 🔌 **Chrome Extension:** Real-time LinkedIn scoring

---

## 📄 License

This dataset is released under the **MIT License**.

**You are free to:**
- ✅ Use commercially
- ✅ Modify and distribute
- ✅ Use privately
- ✅ Include in proprietary software

**You must:**
- ⚠️ Include the license and copyright notice

See [LICENSE](https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm/blob/main/LICENSE) for full details.

---

## 🏆 Citation

If you use this dataset in your research or project, please cite:

```bibtex
@dataset{linkedin_match_2025,
  title={LinkedIn Professional Match Dataset},
  author={[Your Name]},
  year={2025},
  publisher={Kaggle},
  url={[Your Kaggle URL]}
}
```

---

## 📧 Contact & Support

- 💬 **Kaggle Comments:** Ask questions below
- 🐛 **GitHub Issues:** [Report bugs](https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm/issues)
- 📧 **GitHub:** [@Likitha-Gedipudi](https://github.com/Likitha-Gedipudi)

---

## 🎯 Key Highlights

✨ **50K+ professional profiles** with detailed attributes  
✨ **500K+ compatibility pairs** with explainable scores  
✨ **Pre-trained model** ready to use (R²=1.0)  
✨ **18 engineered features** for ML training  
✨ **Synthetic data** - no privacy concerns  
✨ **Production-ready** - used in live API  
✨ **Open source** - contribute on GitHub  
✨ **Well-documented** - notebooks and tutorials included  

---

## 🌟 Related Kaggle Datasets

- [LinkedIn Job Postings](https://www.kaggle.com/datasets)
- [Professional Networks Dataset](https://www.kaggle.com/datasets)
- [Skill Demand Analysis](https://www.kaggle.com/datasets)

---

## ⭐ If you find this dataset useful, please upvote! ⭐

**Happy analyzing! 🚀**

Questions? Comments? Suggestions? Drop them below! 👇
