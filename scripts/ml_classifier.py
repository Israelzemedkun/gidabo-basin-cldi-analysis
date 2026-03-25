import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# ── Load data ──────────────────────────────────────────────────────────────────
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'gidabo_degradation_samples.csv'))
df = pd.read_csv(data_path)
print(f"Loaded {len(df)} samples with columns: {', '.join(df.columns)}")

# ── Normalize NDVI, BSI, SI columns to [0, 1] ─────────────────────────────────
index_cols = ['NDVI_2000', 'NDVI_2024', 'BSI_2000', 'BSI_2024', 'SI_2000', 'SI_2024']
scaler = MinMaxScaler()
normed = scaler.fit_transform(df[index_cols])
normed_df = pd.DataFrame(normed, columns=[c + '_norm' for c in index_cols], index=df.index)
df = pd.concat([df, normed_df], axis=1)

# ── Compute CLDI (2024) ────────────────────────────────────────────────────────
# NDVI weighted 0.5 (primary vegetation-loss signal at 30 m in Ethiopian Rift context)
# BSI weighted 0.3 (soil exposure follows vegetation removal)
# SI weighted 0.2 (salinity is localised to lower rift floor)
df['CLDI'] = (
    0.5 * (1 - df['NDVI_2024_norm'])
    + 0.3 * df['BSI_2024_norm']
    + 0.2 * df['SI_2024_norm']
)

# ── Compute CLDI_2000 for temporal comparison ──────────────────────────────────
df['CLDI_2000'] = (
    0.5 * (1 - df['NDVI_2000_norm'])
    + 0.3 * df['BSI_2000_norm']
    + 0.2 * df['SI_2000_norm']
)

# ── Re-derive Degradation_Status from CLDI ────────────────────────────────────
def classify_cldi(cldi):
    if cldi > 0.5:
        return 'Degraded'
    elif cldi < 0.3:
        return 'Improved'
    return 'Stable'

df['Degradation_Status'] = df['CLDI'].apply(classify_cldi)
print("\nDegradation status distribution:")
print(df['Degradation_Status'].value_counts())

# ── Features and target ────────────────────────────────────────────────────────
features = ['NDVI_2000', 'NDVI_2024', 'BSI_2000', 'BSI_2024',
            'SI_2000', 'SI_2024', 'NDVI_Change', 'SI_Change', 'CLDI']
X = df[features]
y = df['Degradation_Status']

# ── Train / test split ─────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Random Forest classifier ───────────────────────────────────────────────────
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

# ── Evaluation ─────────────────────────────────────────────────────────────────
print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred, labels=['Degraded', 'Stable', 'Improved']))

# ── Save model ─────────────────────────────────────────────────────────────────
models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
os.makedirs(models_dir, exist_ok=True)
model_path = os.path.join(models_dir, 'rf_model.pkl')
joblib.dump(rf, model_path)
print(f"\nModel saved to {model_path}")

# ── Persist updated CSV (with CLDI columns and revised Degradation_Status) ─────
df.to_csv(data_path, index=False)
print(f"Updated CSV saved to {data_path}")
