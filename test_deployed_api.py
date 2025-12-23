"""
Test script for deployed Heroku API.
Tests model accuracy, latency, and edge cases.
"""

import requests
import pandas as pd
import numpy as np
import time
from typing import Dict, List
import json

# API Configuration
API_URL = "https://linkedin-match-algorithm-4ce8d98dc007.herokuapp.com"

def test_health_check():
    """Test if API is running and model is loaded."""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    
    response = requests.get(f"{API_URL}/health")
    result = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"API Status: {result['status']}")
    print(f"Model Loaded: {result['model_loaded']}")
    
    assert response.status_code == 200, "API not responding"
    assert result['model_loaded'] == True, "Model not loaded"
    print("✅ Health check passed!")


def test_single_prediction():
    """Test single compatibility prediction."""
    print("\n" + "="*80)
    print("TEST 2: Single Prediction")
    print("="*80)
    
    # Test case: High compatibility pair
    test_data = {
        "skill_match_score": 85.0,
        "skill_complementarity_score": 90.0,
        "network_value_a_to_b": 75.0,
        "network_value_b_to_a": 80.0,
        "career_alignment_score": 88.0,
        "experience_gap": 4,
        "industry_match": 95.0,
        "geographic_score": 70.0,
        "seniority_match": 85.0
    }
    
    start_time = time.time()
    response = requests.post(
        f"{API_URL}/api/v1/compatibility",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    latency = (time.time() - start_time) * 1000  # ms
    
    result = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Latency: {latency:.2f} ms")
    print(f"Compatibility Score: {result['compatibility_score']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Explanation: {result['explanation']}")
    
    assert response.status_code == 200, "Prediction failed"
    assert 0 <= result['compatibility_score'] <= 100, "Score out of range"
    assert latency < 5000, f"Latency too high: {latency}ms"
    print("✅ Single prediction passed!")
    
    return latency


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "="*80)
    print("TEST 3: Edge Cases")
    print("="*80)
    
    test_cases = [
        {
            "name": "All zeros",
            "data": {
                "skill_match_score": 0.0,
                "skill_complementarity_score": 0.0,
                "network_value_a_to_b": 0.0,
                "network_value_b_to_a": 0.0,
                "career_alignment_score": 0.0,
                "experience_gap": 0,
                "industry_match": 0.0,
                "geographic_score": 0.0,
                "seniority_match": 0.0
            }
        },
        {
            "name": "All max values",
            "data": {
                "skill_match_score": 100.0,
                "skill_complementarity_score": 100.0,
                "network_value_a_to_b": 100.0,
                "network_value_b_to_a": 100.0,
                "career_alignment_score": 100.0,
                "experience_gap": 0,
                "industry_match": 100.0,
                "geographic_score": 100.0,
                "seniority_match": 100.0
            }
        },
        {
            "name": "Large experience gap",
            "data": {
                "skill_match_score": 50.0,
                "skill_complementarity_score": 50.0,
                "network_value_a_to_b": 50.0,
                "network_value_b_to_a": 50.0,
                "career_alignment_score": 50.0,
                "experience_gap": 20,
                "industry_match": 50.0,
                "geographic_score": 50.0,
                "seniority_match": 50.0
            }
        }
    ]
    
    for test_case in test_cases:
        response = requests.post(
            f"{API_URL}/api/v1/compatibility",
            json=test_case["data"]
        )
        result = response.json()
        print(f"\n{test_case['name']}:")
        print(f"  Score: {result['compatibility_score']}")
        print(f"  Recommendation: {result['recommendation']}")
        
        assert response.status_code == 200, f"Failed on {test_case['name']}"
        assert 0 <= result['compatibility_score'] <= 100, f"Score out of range for {test_case['name']}"
    
    print("\n✅ Edge cases passed!")


def test_batch_predictions():
    """Test batch scoring endpoint."""
    print("\n" + "="*80)
    print("TEST 4: Batch Predictions")
    print("="*80)
    
    batch_data = {
        "pairs": [
            {
                "pair_id": "pair_1",
                "skill_match_score": 70.0,
                "skill_complementarity_score": 75.0,
                "network_value_a_to_b": 60.0,
                "network_value_b_to_a": 65.0,
                "career_alignment_score": 80.0,
                "experience_gap": 3,
                "industry_match": 85.0,
                "geographic_score": 55.0,
                "seniority_match": 70.0
            },
            {
                "pair_id": "pair_2",
                "skill_match_score": 40.0,
                "skill_complementarity_score": 45.0,
                "network_value_a_to_b": 30.0,
                "network_value_b_to_a": 35.0,
                "career_alignment_score": 50.0,
                "experience_gap": 10,
                "industry_match": 40.0,
                "geographic_score": 25.0,
                "seniority_match": 30.0
            }
        ]
    }
    
    start_time = time.time()
    response = requests.post(
        f"{API_URL}/api/v1/batch-score",
        json=batch_data
    )
    latency = (time.time() - start_time) * 1000
    
    result = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Batch Latency: {latency:.2f} ms")
    print(f"Pairs Processed: {len(result['results'])}")
    
    for item in result['results']:
        print(f"\n  {item['pair_id']}:")
        print(f"    Score: {item['compatibility_score']}")
        print(f"    Recommendation: {item['recommendation']}")
    
    assert response.status_code == 200, "Batch prediction failed"
    assert len(result['results']) == 2, "Not all pairs processed"
    print("\n✅ Batch predictions passed!")


def test_model_accuracy():
    """Test model accuracy against test dataset."""
    print("\n" + "="*80)
    print("TEST 5: Model Accuracy on Test Data")
    print("="*80)
    
    # Load test data
    try:
        df = pd.read_csv('data/processed/compatibility_pairs_enhanced.csv')
        
        # Sample test data (100 random pairs)
        test_sample = df.sample(n=min(100, len(df)), random_state=42)
        
        predictions = []
        actuals = []
        errors = []
        
        print(f"Testing on {len(test_sample)} pairs...")
        
        for idx, row in test_sample.iterrows():
            test_data = {
                "skill_match_score": float(row.get('skill_match_score', 0)),
                "skill_complementarity_score": float(row.get('skill_complementarity_score', 0)),
                "network_value_a_to_b": float(row.get('network_value_a_to_b', 0)),
                "network_value_b_to_a": float(row.get('network_value_b_to_a', 0)),
                "career_alignment_score": float(row.get('career_alignment_score', 0)),
                "experience_gap": int(row.get('experience_gap', 0)),
                "industry_match": float(row.get('industry_match', 0)),
                "geographic_score": float(row.get('geographic_score', 0)),
                "seniority_match": float(row.get('seniority_match', 0))
            }
            
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/compatibility",
                    json=test_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    pred_score = result['compatibility_score']
                    actual_score = row['compatibility_score']
                    
                    predictions.append(pred_score)
                    actuals.append(actual_score)
                    errors.append(abs(pred_score - actual_score))
                    
            except Exception as e:
                print(f"  Error on row {idx}: {e}")
                continue
        
        if predictions:
            # Calculate metrics
            mae = np.mean(errors)
            rmse = np.sqrt(np.mean(np.array(errors) ** 2))
            
            # R² score
            ss_res = np.sum((np.array(actuals) - np.array(predictions)) ** 2)
            ss_tot = np.sum((np.array(actuals) - np.mean(actuals)) ** 2)
            r2 = 1 - (ss_res / ss_tot)
            
            print(f"\n📊 Accuracy Metrics:")
            print(f"  • Samples Tested: {len(predictions)}")
            print(f"  • Mean Absolute Error (MAE): {mae:.3f}")
            print(f"  • Root Mean Squared Error (RMSE): {rmse:.3f}")
            print(f"  • R² Score: {r2:.3f}")
            print(f"  • Max Error: {max(errors):.3f}")
            print(f"  • Min Error: {min(errors):.3f}")
            
            # Score distribution
            print(f"\n📈 Score Distribution:")
            print(f"  • Actual - Mean: {np.mean(actuals):.1f}, Std: {np.std(actuals):.1f}")
            print(f"  • Predicted - Mean: {np.mean(predictions):.1f}, Std: {np.std(predictions):.1f}")
            
            print("\n✅ Accuracy test completed!")
            
            return {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'samples': len(predictions)
            }
        else:
            print("❌ No successful predictions")
            return None
            
    except FileNotFoundError:
        print("⚠️  Test data not found. Skipping accuracy test.")
        return None


def test_latency_under_load():
    """Test API latency under load."""
    print("\n" + "="*80)
    print("TEST 6: Latency Under Load")
    print("="*80)
    
    test_data = {
        "skill_match_score": 75.0,
        "skill_complementarity_score": 80.0,
        "network_value_a_to_b": 70.0,
        "network_value_b_to_a": 75.0,
        "career_alignment_score": 85.0,
        "experience_gap": 5,
        "industry_match": 90.0,
        "geographic_score": 65.0,
        "seniority_match": 75.0
    }
    
    n_requests = 10
    latencies = []
    
    print(f"Sending {n_requests} sequential requests...")
    
    for i in range(n_requests):
        start = time.time()
        response = requests.post(
            f"{API_URL}/api/v1/compatibility",
            json=test_data
        )
        latency = (time.time() - start) * 1000
        latencies.append(latency)
        
        if response.status_code != 200:
            print(f"  Request {i+1}: FAILED")
        
    print(f"\n📊 Latency Statistics:")
    print(f"  • Mean: {np.mean(latencies):.2f} ms")
    print(f"  • Median: {np.median(latencies):.2f} ms")
    print(f"  • Min: {np.min(latencies):.2f} ms")
    print(f"  • Max: {np.max(latencies):.2f} ms")
    print(f"  • Std Dev: {np.std(latencies):.2f} ms")
    
    print("\n✅ Load test completed!")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*80)
    print("🧪 DEPLOYED API TEST SUITE")
    print("="*80)
    print(f"API URL: {API_URL}")
    
    try:
        test_health_check()
        test_single_prediction()
        test_edge_cases()
        test_batch_predictions()
        accuracy_metrics = test_model_accuracy()
        test_latency_under_load()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        
        if accuracy_metrics:
            print("\n📋 SUMMARY:")
            print(f"  • Model MAE: {accuracy_metrics['mae']:.3f}")
            print(f"  • Model RMSE: {accuracy_metrics['rmse']:.3f}")
            print(f"  • Model R²: {accuracy_metrics['r2']:.3f}")
            print(f"  • Test Samples: {accuracy_metrics['samples']}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
