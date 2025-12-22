# LinkedIn Professional Matching System - Quick Start

## 🚀 Get Started in 5 Minutes

This guide will help you generate a complete LinkedIn compatibility dataset with 50,000+ profiles and 500,000+ compatibility pairs.

---

## Step 1: Setup Environment

```bash
cd linkedin_match

# Run automated setup
./scripts/setup.sh
```

The setup script will:
- Check Python version (3.10+ required)
- Create virtual environment
- Install all dependencies
- Create directory structure
- Generate configuration files

---

## Step 2: Activate Environment

```bash
source venv/bin/activate
```

---

## Step 3: Generate Synthetic Data

Since web scraping requires API keys and rate limiting, start with synthetic data:

```bash
# Generate 50,000 realistic professional profiles
python scripts/run_scraper.py --source synthetic --count 50000
```

This creates: `data/raw/synthetic_profiles_50000.json`

**What you get:**
- 50,000 diverse professional profiles
- Realistic names, locations, companies
- Skills, experience, education
- Goals, needs, and offerings
- Multiple seniority levels and industries

---

## Step 4: Generate Compatibility Dataset

Process profiles and calculate compatibility scores:

```bash
# Generate full dataset with compatibility pairs
python scripts/generate_dataset.py
```

**Processing Pipeline:**
1. ✅ Loads raw profiles
2. ✅ Cleans and validates data
3. ✅ Normalizes schema across sources
4. ✅ Generates 500K+ profile pairs
5. ✅ Calculates compatibility features
6. ✅ Exports final dataset files

---

## Step 5: Access Your Dataset

Your generated files are in `data/processed/`:

### `profiles.csv` (50,000+ rows)
Profile-level data with:
- Basic info (name, location, role)
- Skills and experience
- Goals and needs
- Calculated features

### `compatibility_pairs.csv` (500,000+ rows)
Pair-level compatibility scores with:
- `compatibility_score` (0-100): Overall match quality
- `skill_match_score`: Skill overlap
- `skill_complementarity_score`: How skills complement
- `network_value_a_to_b`: Network value direction
- `career_alignment_score`: Mentorship potential
- `geographic_score`: Location proximity
- `mutual_benefit_explanation`: Human-readable reasons

### `metadata.json`
Dataset statistics and distributions

---

## 📊 Example Use Cases

### 1. Analyze Top Connections
```python
import pandas as pd

df = pd.read_csv('data/processed/compatibility_pairs.csv')

# Find goldmine connections (score > 80)
top_matches = df[df['compatibility_score'] > 80]
print(f"Found {len(top_matches)} high-value connections")

# Analyze what makes connections valuable
print(top_matches.groupby('mutual_benefit_explanation').size())
```

### 2. Build Recommendation System
```python
# Get top 10 recommendations for a user
user_id = "some_profile_id"
recommendations = df[df['profile_a_id'] == user_id] \
    .nlargest(10, 'compatibility_score')

print("Top recommended connections:")
print(recommendations[['profile_b_id', 'compatibility_score', 'mutual_benefit_explanation']])
```

### 3. Network Gap Analysis
```python
profiles = pd.read_csv('data/processed/profiles.csv')

# Find undervalued profiles (high skills, low connections)
hidden_gems = profiles[
    (profiles['skills'].str.len() > 15) &  # Many skills
    (profiles['connections'] < 500)  # Few connections
]
print(f"Found {len(hidden_gems)} hidden gem profiles")
```

---

## 🔄 Add Real Data (Optional)

### LinkedIn Scraping
**⚠️ Important:** Only scrape PUBLIC profiles, respect robots.txt

```bash
# Create file with public profile URLs
echo "https://linkedin.com/in/public-profile-1
https://linkedin.com/in/public-profile-2" > linkedin_urls.txt

# Run scraper (very slow, respects rate limits)
python scripts/run_scraper.py \
    --source linkedin \
    --profile-urls-file linkedin_urls.txt \
    --profiles 100
```

### GitHub Scraping
Requires GitHub Personal Access Token

```bash
# Set token in .env
echo 'LINKEDIN_MATCH_SCRAPERS_GITHUB_API_TOKEN=your_token_here' >> .env

# Scrape GitHub users
python scripts/run_scraper.py \
    --source github \
    --query "location:san-francisco language:python" \
    --profiles 500
```

After scraping, re-run `python scripts/generate_dataset.py` to process new data.

---

## 🐳 Docker Deployment (Optional)

For production deployment:

```bash
# Build and start all services
docker-compose up -d

# Services:
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
# - API: localhost:8000
```

---

## 📈 Dataset Statistics

After generation, you'll have:

| Metric | Value |
|--------|-------|
| Total Profiles | 50,000+ |
| Total Pairs | 500,000+ |
| Features per Pair | 11 |
| Avg Compatibility | ~55-65/100 |
| Industries | 14 |
| Seniority Levels | 4 |
| Skills Coverage | 100+ unique skills |

---

## 🎯 What Makes This Dataset Unique?

1. **Mutual Benefit Focus**: Unlike simple skill matching, calculates bidirectional value
2. **Explainable AI**: Every score comes with human-readable explanations
3. **Career Alignment**: Considers mentorship potential, not just peer matching
4. **Network Value**: Models how connections can introduce you to others
5. **Geographic Context**: Accounts for location and remote preferences

---

## 🤝 Kaggle Competition Ready

This dataset is designed for:
- Recommendation system challenges
- Graph neural network experiments
- Explainable AI research
- Professional network analysis
- Feature engineering practice

Upload to Kaggle:
```bash
# Compress dataset
cd data/processed
tar -czf linkedin_compatibility_dataset.tar.gz *.csv metadata.json

# Upload to Kaggle Datasets
# Visit: https://www.kaggle.com/datasets
```

---

## 📝 Configuration

Edit `config/config.yaml` to customize:
- Feature weights (skill vs network vs career)
- Scraper rate limits
- Synthetic data quality
- Compatibility thresholds

---

## 🐛 Troubleshooting

**ModuleNotFoundError?**
```bash
source venv/bin/activate  # Activate environment
pip install -r requirements.txt  # Reinstall deps
```

**No profiles generated?**
```bash
ls -la data/raw/  # Check for JSON files
python scripts/run_scraper.py --source synthetic --count 1000  # Generate data
```

**Compatibility calculation slow?**
- Reduce `--max-pairs` in generate_dataset.py
- Use `--max-profiles` to limit dataset size

---

## 🎓 Next Steps

- **Build ML Model**: Use compatibility scores for supervised learning
- **Create API**: Deploy FastAPI service (see docker-compose.yml)
- **Add Features**: Extend CompatibilityFeatureEngine with custom logic
- **Visualize**: Create network graphs of high-value connections
- **Kaggle**: Share dataset and start a competition!

---

## 📧 Questions?

Check the full README.md for detailed documentation.

**Happy networking! 🚀**
