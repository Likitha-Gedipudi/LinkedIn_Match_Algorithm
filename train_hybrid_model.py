"""
LinkedIn Match - Hybrid Model Training
======================================
Trains both XGBoost baseline and Neural Network with embeddings.

Architecture:
- XGBoost: Tabular features only (baseline)
- Neural Network: Sentence Transformer embeddings + tabular features

Author: Likitha Gedipudi
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import pickle
import warnings
warnings.filterwarnings('ignore')

# Check for optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("⚠️ sentence-transformers not installed. Run: pip install sentence-transformers")

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ PyTorch not installed. Run: pip install torch")

# ============================================================
# DATA LOADING & FEATURE ENGINEERING
# ============================================================

def load_and_prepare_data(filepath: str):
    """Load dataset and prepare features"""
    
    print("📊 Loading dataset...")
    df = pd.read_csv(filepath)
    print(f"   Loaded {len(df):,} samples")
    
    # Select tabular features
    tabular_features = [
        'skill_overlap', 'skill_jaccard', 'common_skills_count',
        'role_family_match', 'seniority_match', 'company_tier_match',
        'same_location', 'target_has_grad_degree', 'target_connections',
        'experience_alignment', 'alumni_match', 'target_is_senior',
        'is_recruiter', 'remote_friendly',
        'user_seniority_level', 'target_seniority_level',
        'user_years_exp', 'target_years_exp', 'user_connections'
    ]
    
    # Encode categorical features
    label_encoders = {}
    categorical_cols = ['user_family', 'target_family', 'user_company_tier', 'target_company_tier']
    
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
            tabular_features.append(f'{col}_encoded')
    
    # Filter to existing columns
    tabular_features = [f for f in tabular_features if f in df.columns]
    
    print(f"   Using {len(tabular_features)} tabular features")
    
    X_tabular = df[tabular_features].fillna(0).values
    y = df['compatibility_score'].values
    
    # Get headlines for embedding
    user_headlines = df['user_headline'].fillna('').values
    target_headlines = df['target_headline'].fillna('').values
    
    return X_tabular, y, user_headlines, target_headlines, tabular_features, df

# ============================================================
# MODEL 1: XGBOOST BASELINE
# ============================================================

def train_xgboost(X_train, X_val, X_test, y_train, y_val, y_test):
    """Train XGBoost regressor (baseline)"""
    
    print("\n" + "="*60)
    print("🌳 TRAINING XGBOOST (BASELINE)")
    print("="*60)
    
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    y_pred_test = model.predict(X_test)
    
    # Metrics
    metrics = {
        'train_mae': mean_absolute_error(y_train, y_pred_train),
        'val_mae': mean_absolute_error(y_val, y_pred_val),
        'test_mae': mean_absolute_error(y_test, y_pred_test),
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
        'val_rmse': np.sqrt(mean_squared_error(y_val, y_pred_val)),
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
        'train_r2': r2_score(y_train, y_pred_train),
        'val_r2': r2_score(y_val, y_pred_val),
        'test_r2': r2_score(y_test, y_pred_test)
    }
    
    print(f"\n📊 XGBoost Results:")
    print(f"   Train MAE: {metrics['train_mae']:.2f} | Val MAE: {metrics['val_mae']:.2f} | Test MAE: {metrics['test_mae']:.2f}")
    print(f"   Train RMSE: {metrics['train_rmse']:.2f} | Val RMSE: {metrics['val_rmse']:.2f} | Test RMSE: {metrics['test_rmse']:.2f}")
    print(f"   Train R²: {metrics['train_r2']:.4f} | Val R²: {metrics['val_r2']:.4f} | Test R²: {metrics['test_r2']:.4f}")
    
    return model, metrics

# ============================================================
# GENERATE EMBEDDINGS
# ============================================================

def generate_embeddings(user_headlines, target_headlines):
    """Generate sentence embeddings for headlines"""
    
    if not HAS_SENTENCE_TRANSFORMERS:
        print("⚠️ Sentence Transformers not available, skipping embeddings")
        return None, None
    
    print("\n" + "="*60)
    print("🔤 GENERATING SENTENCE EMBEDDINGS")
    print("="*60)
    
    # Use a lightweight model for speed
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim embeddings
    
    print("   Encoding user headlines...")
    user_embeddings = model.encode(user_headlines, show_progress_bar=True, batch_size=256)
    
    print("   Encoding target headlines...")
    target_embeddings = model.encode(target_headlines, show_progress_bar=True, batch_size=256)
    
    print(f"   Embedding shape: {user_embeddings.shape}")
    
    return user_embeddings, target_embeddings

# ============================================================
# MODEL 2: NEURAL NETWORK WITH EMBEDDINGS
# ============================================================

class HybridNet(nn.Module):
    """Neural network combining embeddings + tabular features"""
    
    def __init__(self, embedding_dim, tabular_dim):
        super(HybridNet, self).__init__()
        
        # Embedding processing
        self.embed_fc = nn.Sequential(
            nn.Linear(embedding_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        
        # Tabular processing
        self.tabular_fc = nn.Sequential(
            nn.Linear(tabular_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU()
        )
        
        # Combined
        self.combined_fc = nn.Sequential(
            nn.Linear(64 + 32, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, embeddings, tabular):
        embed_out = self.embed_fc(embeddings)
        tabular_out = self.tabular_fc(tabular)
        combined = torch.cat([embed_out, tabular_out], dim=1)
        return self.combined_fc(combined)


def train_neural_network(X_train_tab, X_val_tab, X_test_tab,
                         user_emb_train, user_emb_val, user_emb_test,
                         target_emb_train, target_emb_val, target_emb_test,
                         y_train, y_val, y_test,
                         epochs=50, batch_size=256):
    """Train hybrid neural network"""
    
    if not HAS_TORCH:
        print("⚠️ PyTorch not available, skipping neural network")
        return None, None
    
    print("\n" + "="*60)
    print("🧠 TRAINING HYBRID NEURAL NETWORK")
    print("="*60)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"   Device: {device}")
    
    # Combine user and target embeddings
    train_emb = np.concatenate([user_emb_train, target_emb_train], axis=1)
    val_emb = np.concatenate([user_emb_val, target_emb_val], axis=1)
    test_emb = np.concatenate([user_emb_test, target_emb_test], axis=1)
    
    # Convert to tensors
    train_emb_t = torch.FloatTensor(train_emb).to(device)
    train_tab_t = torch.FloatTensor(X_train_tab).to(device)
    train_y_t = torch.FloatTensor(y_train).unsqueeze(1).to(device)
    
    val_emb_t = torch.FloatTensor(val_emb).to(device)
    val_tab_t = torch.FloatTensor(X_val_tab).to(device)
    val_y_t = torch.FloatTensor(y_val).unsqueeze(1).to(device)
    
    test_emb_t = torch.FloatTensor(test_emb).to(device)
    test_tab_t = torch.FloatTensor(X_test_tab).to(device)
    
    # Create data loader
    train_dataset = TensorDataset(train_emb_t, train_tab_t, train_y_t)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize model
    embedding_dim = user_emb_train.shape[1]
    tabular_dim = X_train_tab.shape[1]
    
    model = HybridNet(embedding_dim, tabular_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    print(f"   Embedding dim: {embedding_dim * 2}")
    print(f"   Tabular dim: {tabular_dim}")
    print(f"   Training for {epochs} epochs...")
    
    best_val_loss = float('inf')
    best_model_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        
        for emb_batch, tab_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(emb_batch, tab_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Validation
        model.eval()
        with torch.no_grad():
            val_pred = model(val_emb_t, val_tab_t)
            val_loss = criterion(val_pred, val_y_t).item()
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
        
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{epochs} - Train Loss: {train_loss/len(train_loader):.4f} | Val Loss: {val_loss:.4f}")
    
    # Load best model
    model.load_state_dict(best_model_state)
    
    # Final evaluation
    model.eval()
    with torch.no_grad():
        train_pred = model(train_emb_t, train_tab_t).cpu().numpy().flatten()
        val_pred = model(val_emb_t, val_tab_t).cpu().numpy().flatten()
        test_pred = model(test_emb_t, test_tab_t).cpu().numpy().flatten()
    
    metrics = {
        'train_mae': mean_absolute_error(y_train, train_pred),
        'val_mae': mean_absolute_error(y_val, val_pred),
        'test_mae': mean_absolute_error(y_test, test_pred),
        'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
        'val_rmse': np.sqrt(mean_squared_error(y_val, val_pred)),
        'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
        'train_r2': r2_score(y_train, train_pred),
        'val_r2': r2_score(y_val, val_pred),
        'test_r2': r2_score(y_test, test_pred)
    }
    
    print(f"\n📊 Neural Network Results:")
    print(f"   Train MAE: {metrics['train_mae']:.2f} | Val MAE: {metrics['val_mae']:.2f} | Test MAE: {metrics['test_mae']:.2f}")
    print(f"   Train RMSE: {metrics['train_rmse']:.2f} | Val RMSE: {metrics['val_rmse']:.2f} | Test RMSE: {metrics['test_rmse']:.2f}")
    print(f"   Train R²: {metrics['train_r2']:.4f} | Val R²: {metrics['val_r2']:.4f} | Test R²: {metrics['test_r2']:.4f}")
    
    return model, metrics

# ============================================================
# MAIN TRAINING PIPELINE
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🚀 LINKEDIN MATCH - HYBRID MODEL TRAINING")
    print("="*60)
    
    # Load data
    X_tabular, y, user_headlines, target_headlines, feature_names, df = \
        load_and_prepare_data('linkedin_match_50k_synthetic.csv')
    
    # Split data
    print("\n📊 Splitting data...")
    indices = np.arange(len(y))
    train_idx, temp_idx = train_test_split(indices, test_size=0.3, random_state=42)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.5, random_state=42)
    
    X_train = X_tabular[train_idx]
    X_val = X_tabular[val_idx]
    X_test = X_tabular[test_idx]
    
    y_train = y[train_idx]
    y_val = y[val_idx]
    y_test = y[test_idx]
    
    print(f"   Train: {len(train_idx):,} | Val: {len(val_idx):,} | Test: {len(test_idx):,}")
    
    # Scale tabular features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # ============================================================
    # TRAIN XGBOOST BASELINE
    # ============================================================
    xgb_model, xgb_metrics = train_xgboost(
        X_train_scaled, X_val_scaled, X_test_scaled,
        y_train, y_val, y_test
    )
    
    # Save XGBoost model
    with open('xgboost_model.pkl', 'wb') as f:
        pickle.dump({'model': xgb_model, 'scaler': scaler, 'features': feature_names}, f)
    print("💾 Saved XGBoost model to xgboost_model.pkl")
    
    # ============================================================
    # TRAIN NEURAL NETWORK (if dependencies available)
    # ============================================================
    nn_metrics = None
    
    if HAS_SENTENCE_TRANSFORMERS and HAS_TORCH:
        # Generate embeddings
        user_emb, target_emb = generate_embeddings(user_headlines, target_headlines)
        
        if user_emb is not None:
            user_emb_train = user_emb[train_idx]
            user_emb_val = user_emb[val_idx]
            user_emb_test = user_emb[test_idx]
            
            target_emb_train = target_emb[train_idx]
            target_emb_val = target_emb[val_idx]
            target_emb_test = target_emb[test_idx]
            
            nn_model, nn_metrics = train_neural_network(
                X_train_scaled, X_val_scaled, X_test_scaled,
                user_emb_train, user_emb_val, user_emb_test,
                target_emb_train, target_emb_val, target_emb_test,
                y_train, y_val, y_test,
                epochs=50
            )
            
            if nn_model is not None:
                torch.save(nn_model.state_dict(), 'hybrid_nn_model.pt')
                print("💾 Saved Neural Network to hybrid_nn_model.pt")
    
    # ============================================================
    # COMPARISON SUMMARY
    # ============================================================
    print("\n" + "="*60)
    print("📊 MODEL COMPARISON SUMMARY")
    print("="*60)
    
    comparison = pd.DataFrame({
        'Model': ['XGBoost (Baseline)'],
        'Test MAE': [f"{xgb_metrics['test_mae']:.2f}"],
        'Test RMSE': [f"{xgb_metrics['test_rmse']:.2f}"],
        'Test R²': [f"{xgb_metrics['test_r2']:.4f}"]
    })
    
    if nn_metrics:
        comparison = pd.concat([comparison, pd.DataFrame({
            'Model': ['Hybrid Neural Network'],
            'Test MAE': [f"{nn_metrics['test_mae']:.2f}"],
            'Test RMSE': [f"{nn_metrics['test_rmse']:.2f}"],
            'Test R²': [f"{nn_metrics['test_r2']:.4f}"]
        })], ignore_index=True)
    
    print(comparison.to_string(index=False))
    comparison.to_csv('model_comparison.csv', index=False)
    
    # Feature importance
    print("\n🔍 TOP 10 FEATURE IMPORTANCE (XGBoost):")
    importance = pd.DataFrame({
        'Feature': feature_names,
        'Importance': xgb_model.feature_importances_
    }).sort_values('Importance', ascending=False)
    print(importance.head(10).to_string(index=False))
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE - RESUME METRICS:")
    print("="*60)
    print(f"""
📌 WHAT YOU CAN CLAIM:
- Trained XGBoost regressor on 50,000 synthetic LinkedIn profile pairs
- Test MAE: {xgb_metrics['test_mae']:.2f}, Test R²: {xgb_metrics['test_r2']:.4f}
- Engineered {len(feature_names)} features including skill overlap, role affinity, seniority
- Train/Val/Test split: 35,000 / 7,500 / 7,500
""")
    
    if nn_metrics:
        print(f"""- Hybrid Neural Network with Sentence Transformer embeddings
- Neural Network Test MAE: {nn_metrics['test_mae']:.2f}, Test R²: {nn_metrics['test_r2']:.4f}
- Combined 768-dim text embeddings with {len(feature_names)} tabular features
""")
