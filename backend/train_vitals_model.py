# backend/train_vitals_model_lr.py
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
import joblib
import json
from datetime import datetime

def train_logistic_regression(csv_path='training_data.csv'):
    """
    Train Logistic Regression model and output all metrics
    """
    print("="*70)
    print("LOGISTIC REGRESSION MODEL TRAINING")
    print("="*70)
    
    # Load data
    print(f"\n📂 Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} records")
    
    # Prepare target
    df['risk_target'] = (df['Risk Category'] == 'High Risk').astype(int)
    
    # Count classes
    class_counts = df['risk_target'].value_counts()
    print(f"\n📊 Class Distribution:")
    print(f"   Low Risk: {class_counts.get(0, 0)} ({class_counts.get(0, 0)/len(df)*100:.1f}%)")
    print(f"   High Risk: {class_counts.get(1, 0)} ({class_counts.get(1, 0)/len(df)*100:.1f}%)")
    
    # Feature columns
    feature_columns = [
        'Heart Rate', 'Respiratory Rate', 'Body Temperature',
        'Oxygen Saturation', 'Systolic Blood Pressure', 'Diastolic Blood Pressure',
        'Age', 'Derived_HRV', 'Derived_Pulse_Pressure', 'Derived_BMI', 'Derived_MAP'
    ]
    
    # Add gender
    df['Gender_encoded'] = (df['Gender'] == 'Male').astype(int)
    feature_columns.append('Gender_encoded')
    
    X = df[feature_columns]
    y = df['risk_target']
    
    print(f"\n🔧 Features used ({len(feature_columns)}):")
    for i, feat in enumerate(feature_columns, 1):
        print(f"   {i}. {feat}")
    
    # Split data (80% train, 20% test)
    print(f"\n📊 Data Split:")
    print(f"   Training Set Size: 80% of dataset")
    print(f"   Test Set Size: 20% of dataset")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training samples: {len(X_train)} ({len(X_train)/len(X)*100:.0f}%)")
    print(f"   Test samples: {len(X_test)} ({len(X_test)/len(X)*100:.0f}%)")
    
    # Scale features (important for Logistic Regression)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # ============================================================
    # TRAIN LOGISTIC REGRESSION
    # ============================================================
    print(f"\n{'='*70}")
    print("TRAINING LOGISTIC REGRESSION")
    print(f"{'='*70}")
    
    model = LogisticRegression(
        class_weight='balanced',  # Handle imbalanced data
        C=1.0,                    # Regularization strength
        max_iter=1000,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    print(f"\n📊 Model Parameters:")
    print(f"   Algorithm: Logistic Regression")
    print(f"   Regularization (C): {model.C}")
    print(f"   Class Weight: balanced")
    print(f"   Features: {model.n_features_in_}")
    
    # ============================================================
    # CROSS-VALIDATION (5-Fold)
    # ============================================================
    print(f"\n{'='*70}")
    print("CROSS-VALIDATION (5-Fold)")
    print(f"{'='*70}")
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    
    print(f"\n📊 Cross-Validation Folds: 5")
    for i, score in enumerate(cv_scores, 1):
        print(f"   Fold {i}: Accuracy = {score:.3f} ({score*100:.1f}%)")
    print(f"\n   Mean CV Accuracy: {cv_scores.mean():.3f} ({cv_scores.mean()*100:.1f}%)")
    print(f"   CV Std Dev: {cv_scores.std():.4f}")
    
    # ============================================================
    # PREDICTIONS AND METRICS
    # ============================================================
    print(f"\n{'='*70}")
    print("MODEL PERFORMANCE METRICS")
    print(f"{'='*70}")
    
    # Make predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate all metrics
    accuracy = accuracy_score(y_test, y_pred)
    sensitivity = recall_score(y_test, y_pred)  # Sensitivity = Recall for positive class
    specificity = recall_score(y_test, y_pred, pos_label=0)  # Specificity for negative class
    precision = precision_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    # Confusion Matrix
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    print(f"\n📈 Primary Metrics:")
    print(f"   {'Accuracy':<20} {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"   {'Sensitivity (Recall)':<20} {sensitivity:.3f} ({sensitivity*100:.1f}%)")
    print(f"   {'Specificity':<20} {specificity:.3f} ({specificity*100:.1f}%)")
    print(f"   {'Precision':<20} {precision:.3f} ({precision*100:.1f}%)")
    print(f"   {'F1-Score':<20} {f1:.3f} ({f1*100:.1f}%)")
    
    print(f"\n📊 Additional Metrics:")
    print(f"   {'ROC-AUC':<20} {roc_auc:.3f}")
    
    print(f"\n📊 Confusion Matrix:")
    print(f"   {'':<10} {'Predicted Low':<15} {'Predicted High':<15}")
    print(f"   {'Actual Low':<10} {tn:<15} {fp:<15}")
    print(f"   {'Actual High':<10} {fn:<15} {tp:<15}")
    
    # ============================================================
    # COEFFICIENT ANALYSIS (Feature Impact)
    # ============================================================
    print(f"\n{'='*70}")
    print("FEATURE COEFFICIENTS (Logistic Regression)")
    print(f"{'='*70}")
    
    coefficients = pd.DataFrame({
        'feature': feature_columns,
        'coefficient': model.coef_[0],
        'abs_coefficient': np.abs(model.coef_[0])
    }).sort_values('abs_coefficient', ascending=False)
    
    print("\nPositive coefficients = Increases risk")
    print("Negative coefficients = Decreases risk\n")
    
    for i, row in coefficients.head(10).iterrows():
        direction = "⬆️ INCREASES risk" if row['coefficient'] > 0 else "⬇️ DECREASES risk"
        print(f"   {row['feature']:30s}: {row['coefficient']:+.4f} ({direction})")
    
    # ============================================================
    # SAVE MODEL AND ARTIFACTS
    # ============================================================
    print(f"\n{'='*70}")
    print("SAVING MODEL AND ARTIFACTS")
    print(f"{'='*70}")
    
    # Create ai directory if it doesn't exist
    ai_dir = Path(__file__).parent / 'app' / 'ai'
    ai_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    joblib.dump(model, ai_dir / 'vitals_risk_model_lr.pkl')
    print(f"✓ Model saved: {ai_dir}/vitals_risk_model_lr.pkl")
    
    # Save scaler
    joblib.dump(scaler, ai_dir / 'feature_scaler_lr.pkl')
    print(f"✓ Scaler saved: {ai_dir}/feature_scaler_lr.pkl")
    
    # ============================================================
    # SAVE COMPLETE METRICS TO JSON
    # ============================================================
    metrics = {
        'model_info': {
            'algorithm': 'Logistic Regression',
            'regularization_C': float(model.C),
            'class_weight': 'balanced',
            'training_date': datetime.now().isoformat(),
            'n_samples_total': len(df),
            'n_features': len(feature_columns),
            'features_used': feature_columns
        },
        'data_split': {
            'training_size': len(X_train),
            'training_percentage': 80,
            'test_size': len(X_test),
            'test_percentage': 20,
            'cv_folds': 5
        },
        'performance_metrics': {
            'accuracy': float(accuracy),
            'accuracy_percentage': float(accuracy * 100),
            'sensitivity': float(sensitivity),
            'sensitivity_percentage': float(sensitivity * 100),
            'specificity': float(specificity),
            'specificity_percentage': float(specificity * 100),
            'precision': float(precision),
            'precision_percentage': float(precision * 100),
            'f1_score': float(f1),
            'f1_score_percentage': float(f1 * 100),
            'roc_auc': float(roc_auc)
        },
        'confusion_matrix': {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp)
        },
        'cross_validation': {
            'folds': 5,
            'scores': [float(s) for s in cv_scores],
            'mean_accuracy': float(cv_scores.mean()),
            'std_accuracy': float(cv_scores.std())
        },
        'coefficients': [
            {'feature': row['feature'], 'coefficient': float(row['coefficient'])} 
            for _, row in coefficients.head(15).iterrows()
        ]
    }
    
    # Save metrics to file
    with open(ai_dir / 'model_metrics_lr.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Metrics saved: {ai_dir}/model_metrics_lr.json")
    
    # ============================================================
    # PRINT SUMMARY TABLE
    # ============================================================
    print(f"\n{'='*70}")
    print("LOGISTIC REGRESSION - COMPLETE SUMMARY")
    print(f"{'='*70}")
    
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│              LOGISTIC REGRESSION PERFORMANCE                 │
├─────────────────────────────────────────────────────────────┤
│ Parameter              │ Value                              │
├─────────────────────────────────────────────────────────────┤
│ Algorithm              │ Logistic Regression                │
│ Regularization (C)     │ 1.0                                │
│ Training Set Size      │ 80% ({len(X_train)} samples)       │
│ Test Set Size          │ 20% ({len(X_test)} samples)        │
│ Cross-Validation Folds │ 5                                  │
├─────────────────────────────────────────────────────────────┤
│ Accuracy               │ {accuracy*100:.1f}% ({accuracy:.3f})              │
│ Sensitivity            │ {sensitivity*100:.1f}% ({sensitivity:.3f})              │
│ Specificity            │ {specificity*100:.1f}% ({specificity:.3f})              │
│ F1-Score               │ {f1*100:.1f}% ({f1:.3f})                 │
│ ROC-AUC                │ {roc_auc:.3f}                             │
└─────────────────────────────────────────────────────────────┘
""")
    
    return metrics

def compare_models():
    """Compare Logistic Regression vs Random Forest"""
    print("\n" + "="*70)
    print("MODEL COMPARISON")
    print("="*70)
    
    ai_dir = Path(__file__).parent / 'app' / 'ai'
    
    # Load Logistic Regression metrics
    lr_metrics_file = ai_dir / 'model_metrics_lr.json'
    rf_metrics_file = ai_dir / 'model_metrics.json'
    
    if not lr_metrics_file.exists():
        print("\n⚠️ Run Logistic Regression training first:")
        print("   python train_vitals_model_lr.py training_data.csv")
        return
    
    if not rf_metrics_file.exists():
        print("\n⚠️ Run Random Forest training first:")
        print("   python train_vitals_model.py training_data.csv")
        return
    
    with open(lr_metrics_file, 'r') as f:
        lr = json.load(f)
    
    with open(rf_metrics_file, 'r') as f:
        rf = json.load(f)
    
    print("\n" + "="*70)
    print("📊 MODEL PERFORMANCE COMPARISON")
    print("="*70)
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODEL COMPARISON TABLE                               │
├────────────────────────────────┬─────────────────┬─────────────────────────┤
│ Metric                         │ Logistic Reg    │ Random Forest           │
├────────────────────────────────┼─────────────────┼─────────────────────────┤
│ Accuracy                       │ {lr['performance_metrics']['accuracy_percentage']:.1f}% ({lr['performance_metrics']['accuracy']:.3f}){' ':<8} │ {rf['performance_metrics']['accuracy_percentage']:.1f}% ({rf['performance_metrics']['accuracy']:.3f}){' ':<8} │
│ Sensitivity (Recall)           │ {lr['performance_metrics']['sensitivity_percentage']:.1f}% ({lr['performance_metrics']['sensitivity']:.3f}){' ':<8} │ {rf['performance_metrics']['sensitivity_percentage']:.1f}% ({rf['performance_metrics']['sensitivity']:.3f}){' ':<8} │
│ Specificity                    │ {lr['performance_metrics']['specificity_percentage']:.1f}% ({lr['performance_metrics']['specificity']:.3f}){' ':<8} │ {rf['performance_metrics']['specificity_percentage']:.1f}% ({rf['performance_metrics']['specificity']:.3f}){' ':<8} │
│ F1-Score                       │ {lr['performance_metrics']['f1_score_percentage']:.1f}% ({lr['performance_metrics']['f1_score']:.3f}){' ':<8} │ {rf['performance_metrics']['f1_score_percentage']:.1f}% ({rf['performance_metrics']['f1_score']:.3f}){' ':<8} │
│ ROC-AUC                        │ {lr['performance_metrics']['roc_auc']:.3f}{' ':<25} │ {rf['performance_metrics']['roc_auc']:.3f}{' ':<25} │
├────────────────────────────────┼─────────────────┼─────────────────────────┤
│ Cross-Validation Mean          │ {lr['cross_validation']['mean_accuracy']:.3f}{' ':<25} │ {rf['cross_validation']['mean_accuracy']:.3f}{' ':<25} │
│ Cross-Validation Std           │ {lr['cross_validation']['std_accuracy']:.4f}{' ':<25} │ {rf['cross_validation']['std_accuracy']:.4f}{' ':<25} │
└────────────────────────────────┴─────────────────┴─────────────────────────┘
""")
    
    # Recommendation
    lr_f1 = lr['performance_metrics']['f1_score']
    rf_f1 = rf['performance_metrics']['f1_score']
    
    print("\n📌 RECOMMENDATION:")
    if rf_f1 > lr_f1:
        improvement = (rf_f1 - lr_f1) / lr_f1 * 100
        print(f"   ✅ Random Forest performs better (F1-Score: {rf_f1:.3f} vs {lr_f1:.3f})")
        print(f"   📈 Improvement: {improvement:.1f}% better F1-Score")
        print(f"   💡 Use Random Forest for better accuracy at cost of interpretability")
    else:
        improvement = (lr_f1 - rf_f1) / rf_f1 * 100
        print(f"   ✅ Logistic Regression performs better (F1-Score: {lr_f1:.3f} vs {rf_f1:.3f})")
        print(f"   📈 Improvement: {improvement:.1f}% better F1-Score")
        print(f"   💡 Use Logistic Regression for better interpretability")
    
    print("\n   For clinical decision support, Logistic Regression is often preferred")
    print("   because you can explain WHY a patient is at risk (coefficient analysis)")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        compare_models()
    else:
        csv_file = sys.argv[1] if len(sys.argv) > 1 else 'training_data.csv'
        metrics = train_logistic_regression(csv_file)