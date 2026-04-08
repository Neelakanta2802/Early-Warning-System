# Advanced ML Models Overview

## Current Model Capabilities

### ✅ Implemented Models

#### 1. **XGBoost** (Default - Most Powerful)
- **Type**: Extreme Gradient Boosting
- **Accuracy**: Highest among tree-based models
- **Features**:
  - Early stopping for overfitting prevention
  - Handles missing values automatically
  - Feature importance analysis
  - Fast training with histogram-based method
- **Best For**: Highest accuracy requirements, large datasets

#### 2. **LightGBM**
- **Type**: Light Gradient Boosting Machine
- **Accuracy**: Very high, often matches XGBoost
- **Features**:
  - Extremely fast training
  - Lower memory usage
  - Excellent for large datasets
  - Leaf-wise tree growth
- **Best For**: Large datasets, fast training needs

#### 3. **CatBoost**
- **Type**: Categorical Boosting
- **Accuracy**: High, especially with categorical features
- **Features**:
  - Automatic handling of categorical features
  - Robust to overfitting
  - No need for feature scaling
- **Best For**: Datasets with categorical features

#### 4. **Neural Network (Deep Learning)**
- **Type**: Multi-Layer Perceptron (MLP)
- **Accuracy**: Excellent for complex patterns
- **Features**:
  - Deep learning for complex relationships
  - Batch normalization
  - Dropout for regularization
  - Early stopping and learning rate reduction
- **Best For**: Complex non-linear patterns, large feature sets

#### 5. **Ensemble Stacking**
- **Type**: Voting Classifier combining multiple models
- **Accuracy**: Often best overall
- **Features**:
  - Combines XGBoost, LightGBM, CatBoost
  - Soft voting for probability averaging
  - Reduces individual model weaknesses
- **Best For**: Maximum accuracy, production use

#### 6. **Random Forest** (Baseline)
- **Type**: Ensemble of decision trees
- **Accuracy**: Good baseline
- **Features**: Robust, interpretable

#### 7. **Logistic Regression** (Baseline)
- **Type**: Linear model
- **Accuracy**: Good for linear relationships
- **Features**: Fast, interpretable

#### 8. **Gradient Boosting** (Baseline)
- **Type**: Sequential ensemble
- **Accuracy**: Good
- **Features**: Handles non-linear relationships

### 🔧 Advanced Features

#### 1. **Hyperparameter Optimization (Optuna)**
- Automated hyperparameter tuning
- Bayesian optimization
- Cross-validation based selection
- Supports XGBoost and LightGBM
- **Usage**: Set `optimize_hyperparameters=true` in training API

#### 2. **Time Series Forecasting**
- Predicts future risk trends
- Linear regression based forecasting
- Trend analysis (increasing/decreasing/stable)
- Confidence intervals
- **Usage**: Automatically used in risk trend analysis

#### 3. **Anomaly Detection**
- Isolation Forest for outlier detection
- Identifies unusual student patterns
- Configurable contamination rate
- **Usage**: Detects behavioral anomalies

#### 4. **Feature Engineering**
- 30+ engineered features
- GPA momentum and acceleration
- Attendance volatility
- Rolling averages
- Subject variance
- Temporal patterns

## Model Comparison

| Model | Accuracy | Speed | Memory | Best Use Case |
|-------|----------|-------|--------|---------------|
| **XGBoost** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Production, highest accuracy |
| **LightGBM** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Large datasets, fast training |
| **CatBoost** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Categorical features |
| **Neural Network** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Complex patterns |
| **Ensemble** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Maximum accuracy |
| **Random Forest** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Baseline, interpretable |
| **Logistic Regression** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Fast, linear relationships |

## Predictions Made

### 1. **Risk Level Classification**
- **Low Risk** (0-30 score)
- **Medium Risk** (30-60 score)
- **High Risk** (60-100 score)
- **Confidence**: Probability-based confidence scores

### 2. **Risk Score Prediction**
- Continuous score from 0-100
- Weighted combination of factors
- ML probability mapping

### 3. **Future Risk Trends**
- 30-day risk forecast
- Trend direction (increasing/decreasing/stable)
- Confidence intervals

### 4. **Dropout Probability**
- Probability of student dropping out
- Based on risk, attendance, GPA trends
- Weighted combination model

### 5. **Anomaly Detection**
- Unusual behavior patterns
- Isolation Forest scoring
- Outlier identification

## Model Training

### Training Endpoint
```
POST /api/ml/train
{
  "model_type": "xgboost",  // or lightgbm, neural_network, ensemble, etc.
  "use_mock_labels": false,
  "test_size": 0.2,
  "optimize_hyperparameters": true  // Use Optuna for optimization
}
```

### Supported Model Types
- `random_forest` - Baseline Random Forest
- `logistic_regression` - Baseline Logistic Regression
- `gradient_boosting` - Baseline Gradient Boosting
- `xgboost` - **XGBoost (Recommended)**
- `lightgbm` - **LightGBM (Fast)**
- `catboost` - CatBoost
- `neural_network` - **Deep Neural Network**
- `ensemble` - **Ensemble Stacking (Best Accuracy)**
- `hybrid` - Rule-based + ML

## Installation

Install all advanced models:
```bash
pip install xgboost lightgbm catboost tensorflow optuna statsmodels scipy
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Performance Expectations

### Accuracy (F1 Score)
- **XGBoost**: 0.85-0.95 (depending on data quality)
- **LightGBM**: 0.85-0.95
- **Ensemble**: 0.88-0.96 (best)
- **Neural Network**: 0.83-0.92
- **Random Forest**: 0.75-0.85

### Training Time (1000 samples)
- **XGBoost**: ~5-10 seconds
- **LightGBM**: ~2-5 seconds (fastest)
- **Neural Network**: ~30-60 seconds
- **Ensemble**: ~10-20 seconds
- **Random Forest**: ~3-8 seconds

## Recommendations

### For Production Use:
1. **Start with XGBoost** - Best balance of accuracy and speed
2. **Use Ensemble** - For maximum accuracy
3. **Enable Hyperparameter Optimization** - For best performance

### For Development/Testing:
1. **Use LightGBM** - Fast training, good accuracy
2. **Use Random Forest** - Quick baseline

### For Maximum Accuracy:
1. **Use Ensemble** - Combines multiple models
2. **Enable Hyperparameter Optimization** - Fine-tune parameters
3. **Use Neural Network** - For complex patterns

## Model Selection Guide

- **Small Dataset (< 100 students)**: Random Forest or Logistic Regression
- **Medium Dataset (100-1000)**: XGBoost or LightGBM
- **Large Dataset (> 1000)**: LightGBM or Ensemble
- **Need Fast Training**: LightGBM
- **Need Highest Accuracy**: Ensemble or XGBoost with optimization
- **Complex Patterns**: Neural Network
- **Categorical Features**: CatBoost

## Next Steps

1. **Install Dependencies**: Run `pip install -r requirements.txt`
2. **Train Model**: Use `/api/ml/train` endpoint with `model_type="xgboost"`
3. **Enable Optimization**: Set `optimize_hyperparameters=true` for best results
4. **Monitor Performance**: Check metrics in model info endpoint
