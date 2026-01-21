"""
LinkedIn Match - Fast Neural Network Training
==============================================
Optimized for CPU training with smaller dataset.

Author: Likitha Gedipudi
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import warnings
warnings.filterwarnings('ignore')

# Check dependencies
try:
    from sentence_transformers import SentenceTransformer
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    HAS_DEPS = True
except ImportError as e:
    print(f"Missing dependency: {e}")
    HAS_DEPS = False

# ============================================================
# NEURAL NETWORK MODEL
# ============================================================

class HybridNet(nn.Module):
    def __init__(self, embedding_dim, tabular_dim):
        super(HybridNet, self).__init__()
        
        self.embed_fc = nn.Sequential(
            nn.Linear(embedding_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        
        self.tabular_fc = nn.Sequential(
            nn.Linear(tabular_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU()
        )
        
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

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__" and HAS_DEPS:
    print("="*60)
    print("🚀 FAST NEURAL NETWORK TRAINING (10K samples)")
    print("="*60)
    
    # Load data - use subset for faster training
    df = pd.read_csv('linkedin_match_50k_synthetic.csv')
    df = df.sample(n=10000, random_state=42).reset_index(drop=True)
    print(f"📊 Using {len(df):,} samples for fast training")
    
    # Tabular features
    tabular_features = [
        'skill_overlap', 'skill_jaccard', 'common_skills_count',
        'role_family_match', 'seniority_match', 'company_tier_match',
        'same_location', 'target_has_grad_degree', 'target_connections',
        'experience_alignment', 'alumni_match', 'target_is_senior',
        'is_recruiter', 'remote_friendly'
    ]
    tabular_features = [f for f in tabular_features if f in df.columns]
    
    X_tabular = df[tabular_features].fillna(0).values
    y = df['compatibility_score'].values
    
    # Split
    indices = np.arange(len(y))
    train_idx, temp_idx = train_test_split(indices, test_size=0.3, random_state=42)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.5, random_state=42)
    
    print(f"   Train: {len(train_idx):,} | Val: {len(val_idx):,} | Test: {len(test_idx):,}")
    
    # Scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_tabular[train_idx])
    X_val = scaler.transform(X_tabular[val_idx])
    X_test = scaler.transform(X_tabular[test_idx])
    
    y_train, y_val, y_test = y[train_idx], y[val_idx], y[test_idx]
    
    # Generate embeddings
    print("\n🔤 Generating embeddings...")
    model_st = SentenceTransformer('all-MiniLM-L6-v2')
    
    user_headlines = df['user_headline'].fillna('').values
    target_headlines = df['target_headline'].fillna('').values
    
    user_emb = model_st.encode(user_headlines, show_progress_bar=True, batch_size=128)
    target_emb = model_st.encode(target_headlines, show_progress_bar=True, batch_size=128)
    
    print(f"   Embedding shape: {user_emb.shape}")
    
    # Prepare tensors
    device = torch.device('cpu')
    
    train_emb = np.concatenate([user_emb[train_idx], target_emb[train_idx]], axis=1)
    val_emb = np.concatenate([user_emb[val_idx], target_emb[val_idx]], axis=1)
    test_emb = np.concatenate([user_emb[test_idx], target_emb[test_idx]], axis=1)
    
    train_emb_t = torch.FloatTensor(train_emb).to(device)
    train_tab_t = torch.FloatTensor(X_train).to(device)
    train_y_t = torch.FloatTensor(y_train).unsqueeze(1).to(device)
    
    val_emb_t = torch.FloatTensor(val_emb).to(device)
    val_tab_t = torch.FloatTensor(X_val).to(device)
    val_y_t = torch.FloatTensor(y_val).unsqueeze(1).to(device)
    
    test_emb_t = torch.FloatTensor(test_emb).to(device)
    test_tab_t = torch.FloatTensor(X_test).to(device)
    
    # DataLoader
    train_dataset = TensorDataset(train_emb_t, train_tab_t, train_y_t)
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    # Model
    embedding_dim = user_emb.shape[1]
    tabular_dim = X_train.shape[1]
    
    model = HybridNet(embedding_dim, tabular_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    print(f"\n🧠 Training neural network...")
    print(f"   Embedding dim: {embedding_dim * 2}, Tabular dim: {tabular_dim}")
    
    # Train
    epochs = 30
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
        
        if (epoch + 1) % 5 == 0:
            print(f"   Epoch {epoch+1}/{epochs} - Train Loss: {train_loss/len(train_loader):.4f} | Val Loss: {val_loss:.4f}")
    
    # Load best model
    model.load_state_dict(best_model_state)
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        train_pred = model(train_emb_t, train_tab_t).cpu().numpy().flatten()
        val_pred = model(val_emb_t, val_tab_t).cpu().numpy().flatten()
        test_pred = model(test_emb_t, test_tab_t).cpu().numpy().flatten()
    
    print("\n" + "="*60)
    print("📊 NEURAL NETWORK RESULTS")
    print("="*60)
    
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
    
    print(f"   Train MAE: {metrics['train_mae']:.2f} | Val MAE: {metrics['val_mae']:.2f} | Test MAE: {metrics['test_mae']:.2f}")
    print(f"   Train RMSE: {metrics['train_rmse']:.2f} | Val RMSE: {metrics['val_rmse']:.2f} | Test RMSE: {metrics['test_rmse']:.2f}")
    print(f"   Train R²: {metrics['train_r2']:.4f} | Val R²: {metrics['val_r2']:.4f} | Test R²: {metrics['test_r2']:.4f}")
    
    # Save model
    torch.save({
        'model_state_dict': model.state_dict(),
        'embedding_dim': embedding_dim,
        'tabular_dim': tabular_dim,
        'scaler': scaler,
        'features': tabular_features,
        'metrics': metrics
    }, 'hybrid_nn_model.pt')
    
    print("\n💾 Saved neural network to hybrid_nn_model.pt")
    
    # Save metrics
    pd.DataFrame([{
        'Model': 'Hybrid Neural Network',
        'Test MAE': f"{metrics['test_mae']:.2f}",
        'Test RMSE': f"{metrics['test_rmse']:.2f}",
        'Test R²': f"{metrics['test_r2']:.4f}",
        'Train Samples': len(train_idx),
        'Test Samples': len(test_idx)
    }]).to_csv('nn_results.csv', index=False)
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE")
    print("="*60)
    print(f"""
📌 RESUME METRICS:
   - Hybrid Neural Network (768-dim embeddings + {tabular_dim} tabular features)
   - Test MAE: {metrics['test_mae']:.2f}
   - Test R²: {metrics['test_r2']:.4f}
   - Trained on {len(train_idx):,} samples, tested on {len(test_idx):,}
""")
