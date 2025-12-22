"""
FastAPI application for LinkedIn compatibility scoring.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
from pathlib import Path
from typing import List

from .schemas import (
    CompatibilityRequest,
    CompatibilityResponse,
    BatchScoreRequest,
    BatchScoreResponse,
    HealthResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="LinkedIn Professional Matching API",
    description="API for predicting professional networking compatibility",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load trained model
MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "models" / "compatibility_scorer.joblib"
model = None
feature_names = None

@app.on_event("startup")
async def load_model():
    """Load the trained model on startup."""
    global model, feature_names
    try:
        model_data = joblib.load(MODEL_PATH)
        # Model is saved as dict with 'pipeline', 'feature_names', 'model_type'
        if isinstance(model_data, dict):
            model = model_data['pipeline']
            feature_names = model_data['feature_names']
        else:
            model = model_data
        print(f"Model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        print(f"Error loading model: {e}")


def _prepare_features(request: CompatibilityRequest) -> pd.DataFrame:
    """Prepare features with engineering (must match training)."""
    features = pd.DataFrame([{
        'skill_match_score': request.skill_match_score,
        'skill_complementarity_score': request.skill_complementarity_score,
        'network_value_a_to_b': request.network_value_a_to_b,
        'network_value_b_to_a': request.network_value_b_to_a,
        'career_alignment_score': request.career_alignment_score,
        'experience_gap': request.experience_gap,
        'industry_match': request.industry_match,
        'geographic_score': request.geographic_score,
        'seniority_match': request.seniority_match,
    }])
    
    # Engineered features (same as training)
    features['network_value_avg'] = (features['network_value_a_to_b'] + 
                                     features['network_value_b_to_a']) / 2
    features['network_value_diff'] = abs(features['network_value_a_to_b'] - 
                                         features['network_value_b_to_a'])
    
    features['skill_total'] = features['skill_match_score'] + features['skill_complementarity_score']
    features['skill_balance'] = features['skill_match_score'] * features['skill_complementarity_score'] / 100
    
    features['exp_gap_squared'] = features['experience_gap'] ** 2
    features['is_mentorship_gap'] = ((features['experience_gap'] >= 3) & 
                                    (features['experience_gap'] <= 7)).astype(int)
    features['is_peer'] = (features['experience_gap'] <= 2).astype(int)
    
    # Interaction terms
    features['skill_x_network'] = features['skill_complementarity_score'] * features['network_value_avg'] / 100
    features['career_x_industry'] = features['career_alignment_score'] * features['industry_match'] / 100
    
    return features


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return {
        "status": "online",
        "message": "LinkedIn Professional Matching API",
        "model_loaded": model is not None
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy" if model is not None else "degraded",
        "message": "API is running",
        "model_loaded": model is not None
    }


@app.post("/api/v1/compatibility", response_model=CompatibilityResponse)
async def calculate_compatibility(request: CompatibilityRequest):
    """
    Calculate compatibility score between two profiles.
    
    Args:
        request: Contains profile features
        
    Returns:
        Compatibility score and explanation
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Prepare features with engineering (same as training)
        features = _prepare_features(request)
        
        # Predict compatibility score
        score = float(model.predict(features)[0])
        score = max(0, min(100, score))  # Clip to [0, 100]
        
        return {
            "compatibility_score": round(score, 2),
            "recommendation": _get_recommendation(score),
            "explanation": _generate_explanation(request, score)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/api/v1/batch-score", response_model=BatchScoreResponse)
async def batch_score(request: BatchScoreRequest):
    """
    Calculate compatibility scores for multiple profile pairs.
    
    Args:
        request: Contains list of profile feature sets
        
    Returns:
        List of compatibility scores
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        results = []
        
        for item in request.pairs:
            features = _prepare_features(item)
            
            score = float(model.predict(features)[0])
            score = max(0, min(100, score))  # Clip to [0, 100]
            
            results.append({
                "pair_id": item.pair_id,
                "compatibility_score": round(score, 2),
                "recommendation": _get_recommendation(score)
            })
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")


def _get_recommendation(score: float) -> str:
    """Generate recommendation based on score."""
    if score >= 80:
        return "Highly Recommended - Excellent mutual benefit potential"
    elif score >= 60:
        return "Recommended - Good compatibility"
    elif score >= 40:
        return "Consider - Moderate compatibility"
    else:
        return "Not Recommended - Limited mutual benefit"


def _generate_explanation(request: CompatibilityRequest, score: float) -> str:
    """Generate human-readable explanation."""
    explanations = []
    
    if request.skill_complementarity_score > 70:
        explanations.append("Strong skill complementarity")
    
    if request.career_alignment_score > 70:
        explanations.append("Good career stage alignment")
    
    if request.network_value_a_to_b > 60 or request.network_value_b_to_a > 60:
        explanations.append("Valuable network connections")
    
    if request.industry_match > 80:
        explanations.append("Same industry")
    
    if request.geographic_score > 80:
        explanations.append("Geographic proximity")
    
    if not explanations:
        explanations.append("Limited mutual benefit factors")
    
    return " | ".join(explanations)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
