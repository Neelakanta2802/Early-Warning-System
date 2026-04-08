# UI Requirements vs ML Models Analysis

## UI Pages and Their Requirements

### 1. Dashboard (`Dashboard.tsx`)
**Required Data:**
- Total students count
- High-risk students count
- New risk alerts (last 7 days)
- Attendance breaches
- Risk distribution (low/medium/high counts)
- Risk trend over time (visual)
- Recently flagged students (from alerts table)
- Active interventions count
- Unacknowledged alerts count

**ML Models Needed:**
- ✅ Risk prediction (XGBoost/LightGBM/CatBoost/Neural Network/Ensemble)
- ✅ Risk level classification (low/medium/high)
- ✅ Alert generation (early_warning.py)
- ✅ Risk trend analysis (time series forecasting)

**Status:** ✅ **FULLY SUPPORTED**

### 2. StudentsPage (`StudentsPage.tsx`)
**Required Data:**
- Student list with risk levels
- Risk scores (0-100)
- Risk trends (up/down/stable)
- Risk explanations (top factors)
- Department filtering
- Risk level filtering
- Sorting by risk, score, name, department

**ML Models Needed:**
- ✅ Risk prediction with scores
- ✅ Risk level classification
- ✅ Top factors extraction (feature importance)
- ✅ Risk trend calculation (comparing current vs previous)

**Status:** ✅ **FULLY SUPPORTED**

### 3. RiskAnalysisPage (`RiskAnalysisPage.tsx`)
**Required Data:**
- Department-wise risk distribution
- Low/medium/high risk counts per department
- Risk percentages per department

**ML Models Needed:**
- ✅ Risk prediction (aggregated by department)
- ✅ Risk level classification

**Status:** ✅ **FULLY SUPPORTED**

### 4. AlertsPage (`AlertsPage.tsx`)
**Required Data:**
- Alerts with severity (critical/high/medium/low)
- Alert types: `high_risk`, `attendance_drop`, `performance_decline`, `behavioral_anomaly`
- Alert messages
- Acknowledgment status
- Student information linked to alerts

**ML Models Needed:**
- ✅ Alert detection (early_warning.py)
- ✅ Severity classification
- ✅ Alert type classification
- ✅ Behavioral anomaly detection (IsolationForest)

**Status:** ✅ **FULLY SUPPORTED**

### 5. InterventionsPage (`InterventionsPage.tsx`)
**Required Data:**
- Intervention tracking (pending/in_progress/completed)
- Students needing action (high/medium risk without interventions)
- Recommended interventions based on risk level/score

**ML Models Needed:**
- ✅ Risk prediction (to identify high/medium risk students)
- ✅ Intervention recommendation logic (rule-based, can be enhanced with ML)

**Status:** ✅ **SUPPORTED** (Intervention recommendations are rule-based, which is appropriate)

### 6. StudentProfile (`StudentProfile.tsx`)
**Required Data:**
- Risk assessment with detailed explanation
- Risk trend analysis (up/down/stable)
- Academic records
- Attendance records
- Alerts history
- Interventions history
- Performance trends
- Attendance trends
- Top risk factors with impact

**ML Models Needed:**
- ✅ Risk prediction with explanations
- ✅ Risk trend analysis
- ✅ Top factors extraction
- ✅ Performance trend analysis (GPA trends)
- ✅ Attendance trend analysis

**Status:** ✅ **FULLY SUPPORTED**

### 7. PlanningAnalyticsPage (`PlanningAnalyticsPage.tsx`)
**Required Data:**
- Department risk heatmap
- Resource planning (counselors needed, hours estimated)
- At-risk percentages
- Risk concentration by department

**ML Models Needed:**
- ✅ Risk prediction (aggregated)
- ✅ Resource planning calculations (rule-based, appropriate)

**Status:** ✅ **FULLY SUPPORTED**

### 8. ReportsPage (`ReportsPage.tsx`)
**Required Data:**
- Report generation (static UI, backend not implemented yet)

**ML Models Needed:**
- ⚠️ Not implemented (but can use existing ML models)

**Status:** ⚠️ **PARTIALLY SUPPORTED** (UI exists, backend report generation not implemented)

## Current ML Models Inventory

### ✅ Implemented Models:
1. **Risk Prediction Models:**
   - XGBoost
   - LightGBM
   - CatBoost
   - Neural Networks (TensorFlow/Keras)
   - Ensemble Stacking
   - Random Forest (fallback)
   - Logistic Regression (fallback)
   - Gradient Boosting (fallback)

2. **Time Series Forecasting:**
   - Statsmodels ARIMA/Seasonal Decomposition
   - Trend analysis

3. **Anomaly Detection:**
   - IsolationForest for behavioral anomalies

4. **Feature Engineering:**
   - GPA trends, momentum, acceleration
   - Attendance trends, patterns
   - Academic performance metrics
   - Behavioral indicators

5. **Early Warning System:**
   - High risk detection
   - Attendance threshold breaches
   - Performance decline detection
   - Rapid GPA/attendance decline
   - Behavioral anomalies
   - Consecutive absences
   - Sudden drops

## Potential Issues & Fixes Needed

### Issue 1: Data Not Displaying in UI
**Root Cause:** Likely database RLS issues or data not being created properly
**Fix:** Already addressed in previous fixes (service role key, error handling)

### Issue 2: Alerts Not Being Created
**Root Cause:** Alerts are created in `monitoring.py` but may fail silently
**Fix Needed:** Verify alert creation is working, check database permissions

### Issue 3: Risk Explanations Not Showing
**Root Cause:** Top factors may not be properly stored in `factors` JSONB field
**Fix Needed:** Verify factors are being saved correctly

### Issue 4: Risk Trends Not Calculating
**Root Cause:** Requires at least 2 risk assessments to calculate trend
**Fix Needed:** Ensure risk assessments are created on upload and periodically

## Recommendations

1. **All ML models are sufficient** - No new models needed
2. **Focus on data flow** - Ensure data is being created and saved correctly
3. **Verify alert creation** - Check if alerts are being created after risk assessment
4. **Test end-to-end** - Upload data → Risk assessment → Alerts → UI display

## Next Steps

1. Verify alerts are being created in database
2. Check if risk assessments have proper factors/explanation
3. Ensure frontend is fetching data correctly
4. Test complete flow: Upload → ML Prediction → Alerts → UI Display
