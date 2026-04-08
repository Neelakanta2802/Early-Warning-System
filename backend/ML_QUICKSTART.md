# ML Quick Start Guide

## Initial Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
Create a `.env` file with:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_ANON_KEY=your_anon_key
```

3. **Start the Backend**
```bash
python backend/main.py
# or
uvicorn backend.main:app --reload
```

## Training Your First Model

### Step 1: Prepare Data
Ensure you have student data in the database:
- Students table populated
- Academic records (grades, GPA)
- Attendance records

### Step 2: Train Model
```bash
# Using curl
curl -X POST "http://localhost:8000/api/ml/train" \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "random_forest",
    "use_mock_labels": true,
    "test_size": 0.2
  }'
```

Or using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/ml/train",
    json={
        "model_type": "random_forest",
        "use_mock_labels": True,
        "test_size": 0.2
    }
)
print(response.json())
```

### Step 3: Check Model Status
```bash
curl "http://localhost:8000/api/ml/model/info"
```

## Using the Model

### Get Risk Assessment for a Student
```bash
curl "http://localhost:8000/api/students/{student_id}/risk?include_trend=true&include_explanation=true"
```

### Evaluate All Students
The monitoring engine automatically evaluates all active students every hour (configurable).

To manually trigger:
```bash
curl -X POST "http://localhost:8000/api/students/{student_id}/evaluate"
```

## Model Management

### Check if Retraining is Needed
```bash
curl "http://localhost:8000/api/ml/model/retrain-check"
```

### Retrain Model
```bash
curl -X POST "http://localhost:8000/api/ml/model/retrain" \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "random_forest",
    "use_mock_labels": false
  }'
```

### Check Data Drift
```bash
curl "http://localhost:8000/api/ml/model/drift"
```

### Get Model Performance
```bash
curl "http://localhost:8000/api/ml/model/performance"
```

## Understanding Outputs

### Risk Assessment Response
```json
{
  "assessment": {
    "risk_level": "high",
    "risk_score": 75.5,
    "confidence_level": 0.85,
    "explanation": "..."
  },
  "trend": {
    "direction": "increasing",
    "escalation_detected": true,
    "message": "..."
  },
  "explanation": {
    "top_factors": [
      {
        "feature": "current_gpa",
        "importance": 0.3,
        "impact": "Critical GPA of 1.8 significantly increases risk"
      }
    ]
  }
}
```

### Model Training Response
```json
{
  "success": true,
  "model_path": "models/risk_model_1.0.pkl",
  "metrics": {
    "accuracy": 0.85,
    "f1_score": 0.82,
    "precision": 0.80,
    "recall": 0.84
  },
  "n_samples": 150,
  "trained_at": "2024-01-15T10:30:00"
}
```

## Best Practices

1. **Start with Mock Labels**: If you don't have labeled data, use `use_mock_labels: true` for initial training
2. **Monitor Performance**: Check model performance weekly
3. **Retrain Regularly**: Retrain every 30 days or when performance drops
4. **Check Drift**: Monitor data drift monthly
5. **Review Explanations**: Always review ML explanations for transparency

## Troubleshooting

### "Insufficient training data"
- Need at least 10 students with data
- Ensure academic and attendance records exist

### "No trained model found"
- Train a model first using `/api/ml/train`

### "Model performance below threshold"
- Retrain with more data
- Try different model types
- Check data quality

## Next Steps

1. Review `ML_IMPLEMENTATION.md` for detailed documentation
2. Customize thresholds in `config.py`
3. Add custom features in `data_processing.py`
4. Integrate with frontend for visualization
