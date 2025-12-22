# Dataset Generation Guide

## 🎯 Why Datasets Are Not in GitHub

The enhanced datasets (`profiles_enhanced.csv` and `compatibility_pairs_enhanced.csv`) are **too large for GitHub** (181 MB and 68 MB respectively). Instead, you have two options:

## Option 1: Download from Kaggle (Recommended)

Once uploaded, the datasets will be available at:
**[Kaggle Dataset Link - Coming Soon]**

## Option 2: Generate Locally (5 minutes)

### Prerequisites
```bash
pip install -r requirements.txt
```

### Generate All Datasets
```bash
python scripts/regenerate_enhanced_data.py
```

This will create:
- `data/processed/profiles_enhanced.csv` (50K profiles, ~68 MB)
- `data/processed/compatibility_pairs_enhanced.csv` (500K pairs, ~181 MB)
- `data/processed/conversation_starters.csv` (AI-generated icebreakers)
- `data/processed/skills_network.csv` (Skills supply/demand analysis)
- `data/processed/red_flags_top_profiles.csv` (Spam/problematic profiles)
- `data/processed/hidden_gems_top_profiles.csv` (Undervalued connections)
- `data/processed/metadata_enhanced.json` (Dataset statistics)

**Expected runtime**: ~3-5 minutes on a modern laptop

### What You Get
```
Dataset Statistics:
✅ 50,000 professional profiles
✅ 500,000 compatibility pairs
✅ Red flags detection (connection collectors, job hoppers, ghosts)
✅ Hidden gems identification (rising stars, super connectors)
✅ ROI predictions (job opportunities, mentorship, collaboration)
✅ AI conversation starters
✅ Skills network analysis
```

## Option 3: Train ML Models (Optional)

After generating datasets, train production models:
```bash
python scripts/train_all_models.py
```

This creates:
- `data/models/compatibility_scorer.joblib` (XGBoost regressor)
- `data/models/red_flag_classifier.joblib` (RandomForest classifier)
- `data/models/connection_recommender.joblib` (Hybrid recommender)

## 📊 Expected Output Structure

```
data/
├── processed/
│   ├── profiles_enhanced.csv          (68 MB)
│   ├── compatibility_pairs_enhanced.csv (181 MB)
│   ├── conversation_starters.csv       (62 KB)
│   ├── skills_network.csv              (5 KB)
│   ├── red_flags_top_profiles.csv      (Small)
│   ├── hidden_gems_top_profiles.csv    (Small)
│   └── metadata_enhanced.json          (Small)
└── models/
    ├── compatibility_scorer.joblib
    └── training_results.json
```

## 🔥 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Likitha-Gedipudi/LinkedIn_Match_Algorithm.git
cd LinkedIn_Match_Algorithm

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate datasets
python scripts/regenerate_enhanced_data.py

# 4. Explore the data
jupyter notebook notebooks/01_dataset_overview.ipynb
```

## ⚠️ Known Issues

- **Red flag classifier training fails**: Synthetic data has class imbalance (no true positive samples). This is expected for demo purposes. For production, collect real labeled data.
- **Perfect compatibility scores**: Models achieve R²=1.0 because targets are formula-based. For production, use real engagement/connection success data.

## 📦 File Sizes

| File | Size | In Git? |
|------|------|---------|
| profiles_enhanced.csv | 68 MB | ❌ Too large |
| compatibility_pairs_enhanced.csv | 181 MB | ❌ Too large |
| conversation_starters.csv | 62 KB | ✅ Yes |
| skills_network.csv | 5 KB | ✅ Yes |
| metadata_enhanced.json | 10 KB | ✅ Yes |
| models/*.joblib | ~50 MB | ✅ Yes |

## 🚀 Next Steps

1. Generate datasets using the script above
2. Explore the Kaggle notebook: `notebooks/01_dataset_overview.ipynb`
3. Read the full dataset documentation: `KAGGLE_README.md`
4. Build your own recommendation engine using the models in `src/models/`

## 💡 Pro Tips

- **Fast generation**: The script uses vectorized pandas operations. On an M1 Mac, it takes ~3 minutes.
- **Customization**: Edit `src/scrapers/synthetic_generator.py` to change profile archetypes or industry distributions.
- **Real data**: Replace synthetic generation with real LinkedIn API calls (requires OAuth + scraping compliance).
- **Scaling**: For 1M+ profiles, switch to Apache Spark or Dask for distributed processing.

---

**Questions?** Open an issue on GitHub or check out the comprehensive documentation in `KAGGLE_README.md`.
