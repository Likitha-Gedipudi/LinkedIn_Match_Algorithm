#!/bin/bash

# GitHub Repository Setup Script
# Run this to initialize and push your repository to GitHub

echo "🚀 LinkedIn Match - GitHub Setup"
echo "=================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "📝 Step 1: Initialize Git Repository"
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

echo ""
echo "📝 Step 2: Add all files (respecting .gitignore)"
git add .
echo "✅ Files staged for commit"

echo ""
echo "📝 Step 3: Create initial commit"
git commit -m "Initial commit: LinkedIn Match ML system

- 50K+ professional profiles dataset
- 500K+ compatibility pairs
- Pre-trained Gradient Boosting model (R²=1.0)
- FastAPI backend deployed on Heroku
- Chrome extension for real-time scoring
- Comprehensive documentation
- Open source (MIT License)"

echo "✅ Initial commit created"

echo ""
echo "📝 Step 4: Create main branch"
git branch -M main
echo "✅ Main branch created"

echo ""
echo "=========================================="
echo "🎯 Next Steps:"
echo "=========================================="
echo ""
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Repository name: linkedin-match"
echo "   Description: AI-powered professional networking compatibility scoring system"
echo "   Public repository"
echo "   DON'T initialize with README (we have one)"
echo ""
echo "3. After creating the repo, run these commands:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/linkedin-match.git"
echo "   git push -u origin main"
echo ""
echo "4. Enable GitHub Issues and Discussions"
echo ""
echo "5. Add topics to your repo:"
echo "   machine-learning, linkedin, recommendation-system,"
echo "   chrome-extension, scikit-learn, fastapi, heroku"
echo ""
echo "6. Update these files with your GitHub URL:"
echo "   - README.md (add GitHub link)"
echo "   - KAGGLE_DATASET_README.md (add GitHub link)"
echo "   - notebooks/kaggle_starter_notebook.ipynb (add GitHub link)"
echo ""
echo "=========================================="
echo "✅ Repository ready to push!"
echo "=========================================="
