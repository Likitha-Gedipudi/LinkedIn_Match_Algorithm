# Contributing to LinkedIn Match

First off, thank you for considering contributing to LinkedIn Match! 🎉

It's people like you that make LinkedIn Match such a great tool for the community.

## 🌟 Ways to Contribute

We welcome all types of contributions:

### 🎯 Beginner-Friendly Contributions
- 📝 Improve documentation
- 🐛 Report bugs
- 📊 Create data visualizations
- ✍️ Write tutorials or blog posts
- 🎨 Design improvements (UI/UX)
- 🧪 Write tests

### 🔥 Intermediate Contributions
- ⚡ Improve feature engineering
- 🔧 Optimize model performance
- 📈 Add new ML models
- 🌐 API enhancements
- 🔍 Add data validation
- 📱 Chrome extension improvements

### 🚀 Advanced Contributions
- 🧠 Deep learning models
- 🕸️ Graph Neural Networks
- 🔬 Explainable AI (SHAP/LIME)
- 🎭 Real-time learning
- 📡 Distributed training
- 🌍 Web dashboard (React/Streamlit)

---

## 🚦 Getting Started

### 1. Fork the Repository

Click the "Fork" button at the top right of this page.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/linkedin-match.git
cd linkedin-match
```

### 3. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 5. Make Your Changes

Write your code, following our coding standards (see below).

### 6. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 7. Lint Your Code

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/

# All at once
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### 8. Commit Your Changes

```bash
git add .
git commit -m "feat: add amazing feature"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### 9. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 10. Open a Pull Request

Go to the original repository and click "New Pull Request".

---

## 📋 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some additions:

```python
# Good: Clear variable names
compatibility_score = calculate_score(profile_a, profile_b)

# Bad: Unclear names
cs = calc(p1, p2)

# Good: Type hints
def predict_compatibility(features: pd.DataFrame) -> float:
    return model.predict(features)[0]

# Good: Docstrings
def extract_skills(profile: Dict[str, Any]) -> List[str]:
    """
    Extract skills from a profile dictionary.
    
    Args:
        profile: Dictionary containing profile data
        
    Returns:
        List of skill names
    """
    return profile.get('skills', [])
```

### Code Organization

- **One class per file** (unless closely related)
- **Functions should do one thing** (< 50 lines ideally)
- **Use descriptive names** (avoid abbreviations)
- **Add type hints** to all functions
- **Write docstrings** for all public functions/classes

### Testing

- Write tests for all new features
- Aim for **> 80% code coverage**
- Use descriptive test names: `test_compatibility_scorer_returns_score_between_0_and_100`
- Use fixtures for common test data

```python
# tests/test_scorer.py
import pytest
from src.models.compatibility_scorer import CompatibilityScorer

@pytest.fixture
def sample_features():
    return {
        'skill_match_score': 75,
        'network_value_avg': 60,
        # ... other features
    }

def test_scorer_predicts_valid_score(sample_features):
    scorer = CompatibilityScorer()
    score = scorer.predict(sample_features)
    assert 0 <= score <= 100
```

---

## 📂 Project Structure

```
linkedin_match/
├── src/
│   ├── scrapers/       # Data collection
│   ├── features/       # Feature engineering
│   ├── models/         # ML models
│   ├── api/            # FastAPI backend
│   └── utils/          # Utilities
├── chrome-extension/   # Browser extension
├── tests/              # Test suite
├── scripts/            # Helper scripts
├── notebooks/          # Jupyter notebooks
└── docs/               # Documentation
```

---

## 🎯 Contribution Ideas

### Improve Model Performance

**Current:** R²=1.0 on synthetic data  
**Goal:** Work with real engagement data

```python
# Idea: Add new features
def calculate_engagement_score(profile_a, profile_b):
    """Predict likelihood of mutual engagement."""
    # Implementation here
    pass
```

### Add New Data Sources

Currently: LinkedIn (public), GitHub  
**Ideas:**
- Twitter/X professional profiles
- Academic papers (Google Scholar)
- Stack Overflow reputation
- Open source contributions

### Build Web Dashboard

Create a React/Streamlit interface:
- Upload profiles → Get compatibility scores
- Visualize network graph
- Bulk profile analysis
- A/B test different models

### Explainable AI

Add SHAP values for model interpretability:

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
shap.summary_plot(shap_values, X)
```

### Real-Time Learning

Implement online learning for model updates:
- User feedback on recommendations
- Actual connection acceptance rates
- Engagement metrics

---

## 🐛 Reporting Bugs

### Before Submitting

1. Check if the bug has already been reported
2. Check if it's reproducible with the latest code
3. Gather information about your environment

### Bug Report Template

```markdown
**Description:**
Clear description of the bug.

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Environment:**
- OS: [e.g., macOS 13.0]
- Python: [e.g., 3.11.0]
- Dependencies: [output of `pip freeze`]

**Additional Context:**
Screenshots, error messages, logs, etc.
```

---

## 💡 Feature Requests

We love feature ideas! To suggest a feature:

1. **Check existing issues** to avoid duplicates
2. **Open a GitHub Issue** with label `enhancement`
3. **Describe the feature** clearly
4. **Explain the use case** and benefits
5. **Optional:** Propose an implementation

---

## 📖 Documentation

### Improving Documentation

Documentation is as important as code! You can help by:

- Fixing typos
- Adding examples
- Clarifying explanations
- Adding docstrings
- Creating tutorials

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots/diagrams when helpful
- Keep README.md up to date

---

## 🏆 Recognition

All contributors will be:

- ✨ **Listed in CONTRIBUTORS.md**
- 📰 **Mentioned in release notes**
- 🌟 **Acknowledged in README.md**
- 🎖️ **Given GitHub contributor badge**

---

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age
- Body size
- Disability
- Ethnicity
- Gender identity
- Experience level
- Nationality
- Personal appearance
- Race
- Religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**
- ✅ Using welcoming language
- ✅ Respecting differing viewpoints
- ✅ Accepting constructive criticism
- ✅ Focusing on what's best for the community
- ✅ Showing empathy

**Unacceptable behavior:**
- ❌ Harassment or trolling
- ❌ Personal attacks
- ❌ Publishing others' private information
- ❌ Other unprofessional conduct

---

## ❓ Questions?

- 💬 **GitHub Discussions:** Ask questions, share ideas
- 🐛 **GitHub Issues:** Report bugs, request features
- 📧 **Email:** [Add your email if you want]

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to LinkedIn Match! 🚀**

Together, we're making professional networking smarter and more efficient!
