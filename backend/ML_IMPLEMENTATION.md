# ML/AI Implementation Documentation

## Overview

This document describes the complete AI/ML implementation for the Early Warning System (EWS) for identifying at-risk students. The system uses a hybrid approach combining machine learning models with rule-based logic for robust, interpretable risk prediction.

## Architecture

### Components

1. **Feature Engineering** (`data_processing.py`)
   - Advanced temporal feature extraction
   - Rolling averages and momentum indicators
   - Behavioral anomaly detection
   - Academic and attendance trend analysis

2. **ML Training Pipeline** (`ml_training.py`)
   - Train/validation split
   - Cross-validation
   - Multiple model types (Random Forest, Logistic Regression, Gradient Boosting)
   - Comprehensive evaluation metrics

3. **Risk Engine** (`risk_engine.py`)
   - Hybrid ML + rule-based scoring
   - Model inference
   - Risk level classification
   - Confidence calculation

4. **Model Explainability** (`model_explainability.py`)
   - SHAP values for feature importance
   - Human-readable explanations
   - Global and local feature importance

5. **Trend Analysis** (`trend_analysis.py`)
   - Temporal risk trend detection
   - Escalation detection
   - Future risk projection
   - Period comparison

6. **Model Management** (`model_management.py`)
   - Automatic retraining
   - Data drift detection
   - Model versioning
   - Performance monitoring

7. **Early Warning Detection** (`early_warning.py`)
   - Alert generation
   - Threshold-based warnings
   - Alert cooldown management

## Features

### Academic Features
- Current GPA
- GPA trend (slope over time)
- GPA variance (volatility)
- GPA momentum (recent change rate)
- GPA acceleration (change in trend)
- Rolling averages (3 and 6 semesters)
- Failed courses count
- Low grade count
- Subject variance
- Credits completed

### Attendance Features
- Overall attendance percentage
- Attendance trend
- Recent absent days
- Late count
- Attendance volatility
- Attendance momentum
- Consecutive absences
- Rolling averages (7 and 14 days)
- Sudden drop detection
- Subject-wise attendance

### Behavioral Features
- Assignment submission rate
- Sudden behavior change detection
- Participation score

### Historical Features
- Previous risk score
- Warning count
- Intervention count
- Years enrolled

### Demographic Features
- First-generation student status

## Model Types

### 1. Random Forest
- **Use Case**: Default model, good balance of accuracy and interpretability
- **Parameters**: 100 estimators, max depth 10, balanced class weights
- **Advantages**: Handles non-linear relationships, feature importance available

### 2. Logistic Regression
- **Use Case**: Interpretable baseline model
- **Parameters**: LBFGS solver, balanced class weights
- **Advantages**: Highly interpretable, fast training

### 3. Gradient Boosting
- **Use Case**: Higher accuracy when more data available
- **Parameters**: 100 estimators, max depth 5, learning rate 0.1
- **Advantages**: Best accuracy, handles complex patterns

### 4. Hybrid (Rule-Based + ML)
- **Use Case**: Fallback when ML confidence is low
- **Approach**: 60% rule-based + 40% ML
- **Advantages**: Robust, always provides prediction

## Training Pipeline

### Data Preparation
1. Fetch student records from database
2. Extract academic and attendance records
3. Engineer features using `DataProcessor`
4. Generate labels (from risk assessments or mock labels)

### Training Process
1. Train/validation split (80/20)
2. Feature scaling
3. Model training
4. Evaluation on test set
5. Cross-validation (5-fold)
6. Model saving with metadata

### Evaluation Metrics
- Accuracy
- Precision (weighted)
- Recall (weighted)
- F1-score (weighted)
- ROC-AUC
- Confusion matrix
- Classification report

## Model Explainability

### SHAP Values
- Local explanations for individual predictions
- Feature importance ranking
- Impact direction (increases/decreases risk)

### Human-Readable Explanations
- Top contributing factors
- Impact descriptions
- Summary messages

### Example Explanation
```
Primary risk factors:
1. Critical GPA of 1.8 significantly increases risk
2. Very low attendance at 45.2% is a major risk factor
3. Rapid GPA decline of -0.5 indicates deteriorating performance

Academic performance is critically low (GPA: 1.80).
Attendance is critically low (45.2%).
```

## Trend Analysis

### Risk Trend Detection
- **Increasing**: Gradual risk increase
- **Increasing Rapidly**: Fast risk escalation
- **Decreasing**: Risk improvement
- **Stable**: No significant change

### Escalation Detection
- Detects risk score increases > 15 points
- Identifies sudden changes (> 2 standard deviations)
- Tracks risk level changes (low → medium → high)

### Future Projection
- Linear projection of risk score
- 30-day ahead forecast
- Helps with proactive intervention planning

## Model Management

### Retraining Strategy
- **Automatic**: Every 30 days
- **Performance-based**: When F1-score < 0.7
- **Drift-based**: When data distribution changes significantly

### Data Drift Detection
- Compares current feature distributions with training data
- Detects shifts > 15% in feature means
- Triggers retraining when drift detected

### Model Versioning
- Semantic versioning (major.minor.patch)
- Metadata tracking (training date, metrics, sample count)
- Version history maintained

## API Endpoints

### Training & Model Management
- `POST /api/ml/train` - Train new model
- `GET /api/ml/model/info` - Get model information
- `GET /api/ml/model/versions` - List all versions
- `POST /api/ml/model/retrain` - Retrain model
- `GET /api/ml/model/retrain-check` - Check if retraining needed
- `GET /api/ml/model/performance` - Get performance metrics
- `GET /api/ml/model/drift` - Check for data drift

### Evaluation
- `POST /api/ml/evaluate` - Evaluate model on test data
- `GET /api/ml/features/importance` - Get feature importance

### Student Risk Assessment
- `GET /api/students/{id}/risk` - Get risk with trend and explanation
- `GET /api/students/{id}/trend` - Get trend analysis

## Usage Examples

### Training a Model
```python
# Train with real labels
POST /api/ml/train
{
    "model_type": "random_forest",
    "use_mock_labels": false,
    "test_size": 0.2
}

# Train with mock labels (if real labels unavailable)
POST /api/ml/train
{
    "model_type": "gradient_boosting",
    "use_mock_labels": true
}
```

### Getting Risk Assessment with Explanation
```python
GET /api/students/{student_id}/risk?include_trend=true&include_explanation=true
```

### Checking if Retraining is Needed
```python
GET /api/ml/model/retrain-check
```

## Production Considerations

### Performance
- Model inference: < 100ms per student
- Batch processing: Supports parallel evaluation
- Caching: Risk assessments cached to reduce computation

### Reliability
- Fallback to rule-based when ML fails
- Model versioning for rollback capability
- Performance monitoring and alerts

### Interpretability
- All predictions include explanations
- Feature importance available
- Human-readable risk factors

### Scalability
- Handles thousands of students
- Efficient feature extraction
- Optimized database queries

## Best Practices

1. **Regular Retraining**: Retrain every 30 days or when performance drops
2. **Monitor Drift**: Check for data drift monthly
3. **Validate Predictions**: Compare ML predictions with rule-based baseline
4. **Track Performance**: Monitor F1-score, precision, recall over time
5. **Explain Predictions**: Always provide explanations for transparency
6. **Version Control**: Keep model versions for comparison and rollback

## Future Enhancements

1. **Deep Learning**: Add neural networks for complex pattern detection
2. **Ensemble Methods**: Combine multiple models for better accuracy
3. **Time Series Models**: LSTM/GRU for temporal pattern recognition
4. **Active Learning**: Improve model with human feedback
5. **A/B Testing**: Compare model versions in production
6. **Real-time Updates**: Stream processing for immediate risk updates

## Troubleshooting

### Model Not Training
- Check if sufficient data available (minimum 10 samples)
- Verify database connection
- Check feature extraction errors

### Low Model Performance
- Increase training data
- Try different model types
- Check for data quality issues
- Adjust feature engineering

### High False Positives
- Adjust risk thresholds
- Increase precision weight in training
- Review feature importance

### Data Drift Warnings
- Retrain model with current data
- Investigate data collection changes
- Update feature distributions

## References

- Scikit-learn Documentation: https://scikit-learn.org/
- SHAP Documentation: https://shap.readthedocs.io/
- Early Warning Systems in Education: Research best practices
