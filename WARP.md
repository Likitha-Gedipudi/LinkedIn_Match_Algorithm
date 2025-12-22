# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Commands

### Setup and Installation
```bash
# Initial setup (creates venv, installs dependencies, creates directories)
./scripts/setup.sh

# Manual setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Configuration
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with appropriate settings
```

### Data Generation and Processing
```bash
# Generate synthetic profiles (fastest way to get started)
python scripts/run_scraper.py --source synthetic --count 50000

# Scrape real data (requires setup)
python scripts/run_scraper.py --source linkedin --profile-urls-file urls.txt --profiles 1000
python scripts/run_scraper.py --source github --query "location:usa language:python" --profiles 500

# Generate enhanced datasets with all features (~5 minutes)
python scripts/regenerate_enhanced_data.py

# Process raw data and create compatibility pairs
python scripts/generate_dataset.py
```

### Model Training and Evaluation
```bash
# Train all ML models (compatibility scorer, red flag classifier, recommender)
python scripts/train_all_models.py

# Models are saved to: data/models/
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scrapers.py -v

# Run tests in parallel
pytest tests/ -n auto
```

### Code Quality
```bash
# Format code with Black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/

# Sort imports
isort src/ tests/

# Run all linters (recommended before commits)
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### API Development
```bash
# Start development server (with auto-reload)
uvicorn src.api.main:app --reload --port 8000

# API will be available at http://localhost:8000
# Docs at http://localhost:8000/docs
# ReDoc at http://localhost:8000/redoc
```

### Docker Deployment
```bash
# Build images
docker-compose build

# Start all services (PostgreSQL, Redis, API, Worker)
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale workers
docker-compose up -d --scale worker=3

# Stop services
docker-compose down
```

### Notebooks
```bash
# Start Jupyter Lab
jupyter lab

# Key notebooks:
# - notebooks/01_dataset_overview.ipynb - Dataset exploration
# - notebooks/kaggle_starter_linkedin_match.ipynb - Kaggle submission guide
```

### Version Control
**IMPORTANT**: When making commits to this repository, do NOT add Warp as a co-author. Do not include `Co-Authored-By: Warp <agent@warp.dev>` or any similar attribution in commit messages.

## High-Level Architecture

### System Overview
This is an **enterprise-grade ML system** for predicting professional networking compatibility on LinkedIn. The system analyzes profiles and calculates mutual benefit scores between profile pairs, generating a comprehensive dataset with 50K+ profiles and 500K+ compatibility pairs.

### Core Pipeline Flow
1. **Data Collection** (Scrapers) → 2. **Processing** (Data Pipeline) → 3. **Feature Engineering** → 4. **Model Training/Inference** → 5. **API/Output**

### Key Architectural Components

#### 1. Scrapers (`src/scrapers/`)
**Pattern**: Template Method with base class providing common scraping functionality

- `base_scraper.py`: Abstract base class with:
  - Rate limiting (respects platform limits)
  - Proxy rotation and user agent randomization
  - Automatic retries with exponential backoff
  - robots.txt compliance
  - Request session management

- `linkedin_scraper.py`: Public data only, TOS compliant
- `github_scraper.py`: Uses official GitHub API with token auth
- `synthetic_generator.py`: Creates realistic profiles for testing/augmentation (50K+ profiles in ~3 minutes)

**Design principle**: All scrapers extend `BaseScraper` and implement `scrape()` method. Rate limiting and error handling are centralized.

#### 2. Configuration System (`src/utils/config.py`)
**Pattern**: Pydantic-based configuration with hierarchical structure

- Configuration loaded from YAML files (`config/config.yaml`)
- Environment variable overrides supported (e.g., `LINKEDIN_MATCH_SCRAPERS_GITHUB_API_TOKEN`)
- Nested config classes: AppConfig, DatabaseConfig, ScraperConfig, DataConfig, FeatureConfig, ModelConfig
- Type validation and defaults handled by Pydantic
- Connection URLs generated dynamically (PostgreSQL, Redis)

**Important**: Config is injected throughout the system. Always use `get_config()` from utils rather than hardcoding values.

#### 3. Feature Engineering (`src/features/`)
**Core insight**: This system calculates **bidirectional mutual benefit**, not just similarity.

`compatibility_features.py` - Main feature engine with weighted scoring:
- **Skill Match** (Jaccard similarity): Overlapping skills between profiles
- **Skill Complementarity** (40% weight): How well A's needs match B's offerings and vice versa
- **Network Value** (30% weight): Bidirectional - connection count, seniority, industry relevance
- **Career Alignment** (20% weight): Experience gap analysis (optimal mentor-mentee: 3-7 years, peers: 0-2 years)
- **Geographic Score** (10% weight): Location proximity with remote preference handling
- **ROI Predictors**: Job opportunity score, mentorship value, collaboration potential
- **Explainable AI**: Every score includes human-readable `mutual_benefit_explanation`

`red_flags_detector.py`: Identifies problematic profiles (connection collectors, job hoppers, ghost profiles)

`hidden_gems_detector.py`: Finds undervalued profiles (rising stars, super connectors with low visibility)

`conversation_generator.py`: AI-powered icebreakers based on compatibility features

**Key Design**: Features are calculated per-pair, not per-profile. Each pair has distinct A→B and B→A network values.

#### 4. Models (`src/models/`)
**Architecture**: Multiple specialized models rather than one monolithic model

- `compatibility_scorer.py`: XGBoost regression model predicting 0-100 compatibility score
- `red_flag_classifier.py`: Random Forest classifier for profile quality assessment
- `connection_recommender.py`: Hybrid collaborative filtering + content-based recommender

**Training Note**: Current models achieve R²=1.0 on synthetic data because targets are formula-based. For production, replace with real engagement data.

#### 5. Data Pipeline (`src/data/`)
**Pattern**: ETL with validation and normalization

- `processors.py`: Schema normalization across multiple data sources (LinkedIn, GitHub, synthetic)
- `validators.py`: Data quality checks, required field validation, deduplication
- `storage.py`: Handles multiple export formats (CSV, Parquet, JSON)

**Processing Flow**: Raw JSON → Validation → Normalization → Feature Engineering → Processed CSV/Parquet

#### 6. API (`src/api/`)
**Framework**: FastAPI with production-ready features

- `main.py`: Application setup with middleware (CORS, auth, rate limiting)
- `endpoints.py`: REST endpoints for compatibility scoring, batch scoring, recommendations
- `schemas.py`: Pydantic request/response models

**Authentication**: JWT-based, configured via `config.yaml` (secret key, expiration)
**Rate Limiting**: Configurable requests per minute with burst allowance

### Data Flow Example
```
User Request → run_scraper.py
  ↓
SyntheticProfileGenerator.generate_batch(50000)
  ↓
data/raw/synthetic_profiles_50000.json
  ↓
generate_dataset.py loads profiles
  ↓
CompatibilityFeatureEngine.calculate_features() for each pair
  ↓
11 feature scores + explanations calculated
  ↓
data/processed/compatibility_pairs_enhanced.csv (500K rows)
```

### Configuration-Driven Design
Almost everything is configurable via `config/config.yaml`:
- Scraper rate limits, timeouts, proxy lists
- Feature weights (skill vs network vs career vs geographic)
- Model hyperparameters (learning rate, epochs, architecture)
- Database connections (PostgreSQL, Redis)
- API settings (auth, CORS, rate limits)

**Pattern**: Services receive config object in constructor, not raw parameters.

### Important Patterns to Follow

1. **Logging**: Use `get_logger()` from utils, not raw `print()` statements. Structured logging with context.

2. **Error Handling**: Scrapers use tenacity for retries. Data pipeline validates at each step with informative errors.

3. **Type Hints**: Full type annotations throughout. Use `from typing import` for complex types.

4. **Dependency Injection**: Config and logger injected into classes rather than imported globally.

5. **Batch Processing**: All data operations work in batches (configurable `batch_size` in config) for memory efficiency.

### Key Files to Understand First
1. `src/utils/config.py` - Configuration structure and loading
2. `src/scrapers/base_scraper.py` - Common scraping patterns
3. `src/features/compatibility_features.py` - Core business logic for scoring
4. `scripts/run_scraper.py` - Entry point for data collection
5. `scripts/regenerate_enhanced_data.py` - Complete pipeline example

### Dataset Files Location
- **Raw data**: `data/raw/` (JSON format from scrapers)
- **Processed data**: `data/processed/` (CSV/Parquet with features)
- **Models**: `data/models/` (joblib serialized models)
- **Logs**: `data/logs/` (application logs)

Note: Large dataset files (profiles_enhanced.csv ~68MB, compatibility_pairs_enhanced.csv ~181MB) are .gitignored. Regenerate with `python scripts/regenerate_enhanced_data.py`.

### Testing Approach
- Test structure in `tests/` directory (currently minimal, ready for expansion)
- Use pytest fixtures for common test data
- Mock external API calls (GitHub, database) in tests
- Integration tests should use synthetic data, not real scraping

### Environment Variables
Key environment variables (can be set in `.env` file):
- `LINKEDIN_MATCH_SCRAPERS_GITHUB_API_TOKEN` - GitHub API token for scraping
- `POSTGRES_PASSWORD` - Database password for Docker deployment
- `DATABASE_URL` - Full PostgreSQL connection URL
- `REDIS_URL` - Redis connection URL

### Important Constraints
1. **Ethical Scraping**: Only scrape public data, respect rate limits, follow TOS
2. **Data Privacy**: No PII storage, GDPR compliance built-in
3. **Rate Limits**: All scrapers have configurable, conservative rate limits
4. **Memory Usage**: Batch processing for large datasets (configurable batch size)

### Common Development Tasks

**Adding a new feature to compatibility scoring:**
1. Add calculation method to `CompatibilityFeatureEngine` class
2. Update `calculate_features()` to include new feature
3. Add feature weight to config schema in `config.py`
4. Update `_calculate_overall_compatibility()` to incorporate weight
5. Regenerate dataset with new feature

**Adding a new data source scraper:**
1. Create new scraper class inheriting from `BaseScraper`
2. Implement `scrape()` method with source-specific logic
3. Add config section in `config/config.example.yaml`
4. Add command-line option in `scripts/run_scraper.py`
5. Update data processor to normalize new source schema

**Modifying feature weights:**
- Edit `config/config.yaml` under `features:` section
- Weights in CompatibilityFeatureEngine: skill_complementarity (0.40), network_value (0.30), career_alignment (0.20), geographic (0.10)
- Regenerate dataset to apply new weights
