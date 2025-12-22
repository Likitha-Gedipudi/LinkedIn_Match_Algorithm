"""
Pydantic schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class CompatibilityRequest(BaseModel):
    """Request schema for compatibility scoring."""
    skill_match_score: float = Field(..., ge=0, le=100, description="Skill overlap score")
    skill_complementarity_score: float = Field(..., ge=0, le=100, description="Skill complementarity score")
    network_value_a_to_b: float = Field(..., ge=0, le=100, description="Network value from A to B")
    network_value_b_to_a: float = Field(..., ge=0, le=100, description="Network value from B to A")
    career_alignment_score: float = Field(..., ge=0, le=100, description="Career alignment score")
    experience_gap: int = Field(..., ge=0, description="Years of experience difference")
    industry_match: float = Field(..., ge=0, le=100, description="Industry match score")
    geographic_score: float = Field(..., ge=0, le=100, description="Geographic proximity score")
    seniority_match: float = Field(..., ge=0, le=100, description="Seniority match score")

    class Config:
        json_schema_extra = {
            "example": {
                "skill_match_score": 75.0,
                "skill_complementarity_score": 85.0,
                "network_value_a_to_b": 65.0,
                "network_value_b_to_a": 70.0,
                "career_alignment_score": 80.0,
                "experience_gap": 5,
                "industry_match": 90.0,
                "geographic_score": 60.0,
                "seniority_match": 70.0
            }
        }


class CompatibilityResponse(BaseModel):
    """Response schema for compatibility scoring."""
    compatibility_score: float = Field(..., description="Overall compatibility score (0-100)")
    recommendation: str = Field(..., description="Recommendation text")
    explanation: str = Field(..., description="Human-readable explanation")

    class Config:
        json_schema_extra = {
            "example": {
                "compatibility_score": 78.5,
                "recommendation": "Recommended - Good compatibility",
                "explanation": "Strong skill complementarity | Good career stage alignment | Valuable network connections"
            }
        }


class BatchScoreItem(BaseModel):
    """Individual item in batch scoring request."""
    pair_id: str = Field(..., description="Unique identifier for this pair")
    skill_match_score: float = Field(..., ge=0, le=100)
    skill_complementarity_score: float = Field(..., ge=0, le=100)
    network_value_a_to_b: float = Field(..., ge=0, le=100)
    network_value_b_to_a: float = Field(..., ge=0, le=100)
    career_alignment_score: float = Field(..., ge=0, le=100)
    experience_gap: int = Field(..., ge=0)
    industry_match: float = Field(..., ge=0, le=100)
    geographic_score: float = Field(..., ge=0, le=100)
    seniority_match: float = Field(..., ge=0, le=100)


class BatchScoreRequest(BaseModel):
    """Request schema for batch scoring."""
    pairs: List[BatchScoreItem] = Field(..., description="List of profile pairs to score")

    class Config:
        json_schema_extra = {
            "example": {
                "pairs": [
                    {
                        "pair_id": "pair_001",
                        "skill_match_score": 75.0,
                        "skill_complementarity_score": 85.0,
                        "network_value_a_to_b": 65.0,
                        "network_value_b_to_a": 70.0,
                        "career_alignment_score": 80.0,
                        "experience_gap": 5,
                        "industry_match": 90.0,
                        "geographic_score": 60.0,
                        "seniority_match": 70.0
                    }
                ]
            }
        }


class BatchScoreResultItem(BaseModel):
    """Individual result in batch scoring response."""
    pair_id: str
    compatibility_score: float
    recommendation: str


class BatchScoreResponse(BaseModel):
    """Response schema for batch scoring."""
    results: List[BatchScoreResultItem]

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "pair_id": "pair_001",
                        "compatibility_score": 78.5,
                        "recommendation": "Recommended - Good compatibility"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    message: str
    model_loaded: bool

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "API is running",
                "model_loaded": True
            }
        }
