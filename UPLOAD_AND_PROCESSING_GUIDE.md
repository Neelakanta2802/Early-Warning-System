# Student Data Upload and Processing Guide

## Overview
The system now supports uploading student data files (CSV, Excel, or JSON) and automatically processes them with ML models to predict student risk levels. All pages (Dashboard, Students, Risk Analysis, etc.) will work with the uploaded data.

## Supported File Formats

### 1. JSON Format (Recommended for Mock Data)
The system now supports JSON files with the following structure:

```json
{
  "student": {
    "id": "uuid",
    "student_id": "STU2024001",
    "full_name": "Student Name",
    "email": "student@university.edu",
    "department": "Computer Science",
    "program": "BS Computer Science",
    "year_level": 2,
    "semester": "Fall 2024",
    "enrollment_date": "2023-09-01",
    "status": "active"
  },
  "academic_records": [
    {
      "student_id": "STU2024001",
      "semester": "Fall 2023",
      "course_code": "CS101",
      "course_name": "Introduction to Programming",
      "grade": 85.5,
      "credits": 3,
      "gpa": 3.4
    }
  ],
  "attendance_records": [
    {
      "student_id": "STU2024001",
      "date": "2024-09-02",
      "status": "present",
      "course_code": "CS301",
      "semester": "Fall 2024"
    }
  ],
  "behavior_data": {
    "assignment_submissions_on_time": 45.5,
    "participation_score": 38.0,
    "sudden_behavior_change": true
  }
}
```

**Note:** You can also upload an array of students:
```json
[
  { "student": {...}, "academic_records": [...], ... },
  { "student": {...}, "academic_records": [...], ... }
]
```

### 2. CSV Format
CSV files should include columns like:
- `roll_number` or `student_id` or `id`
- `name` or `full_name` or `student_name`
- `email`, `department`, `program`, `year_level`, `semester`
- `course_code` or `course`
- `grade` or `score`
- `gpa`
- `date` or `attendance_date`
- `status` (present/absent/late/excused)

### 3. Excel Format (.xlsx, .xls)
Same column structure as CSV.

## How It Works

### Upload Process
1. **File Upload**: Go to "Data Upload" page and select your file (CSV, Excel, or JSON)
2. **Data Processing**: The system:
   - Parses the file
   - Creates/updates student records
   - Creates academic records (grades)
   - Creates attendance records
   - Triggers ML risk assessment for each student

### ML Risk Prediction
After uploading, the system automatically:
1. **Feature Engineering**: Extracts features from academic and attendance data:
   - GPA trends, variance, momentum
   - Attendance trends, volatility
   - Behavioral patterns
   - Historical risk scores

2. **Risk Assessment**: Uses trained ML models (Random Forest, Logistic Regression, or Gradient Boosting) to predict:
   - Risk level (low/medium/high)
   - Risk score (0-100)
   - Confidence level
   - Contributing factors

3. **Alert Generation**: Automatically creates alerts for high-risk students

## Using the Mock Data

The `mock_student_data.json` file is ready to use:

1. **Upload the File**:
   - Navigate to "Data Upload" page
   - Click "Select Files" or drag and drop `mock_student_data.json`
   - Click "Upload & Process Data"

2. **View Results**:
   - **Dashboard**: See overview of all students and risk distribution
   - **Students**: View list of all students with their risk levels
   - **Risk Analysis**: See detailed risk breakdown by department/course
   - **Student Profile**: Click on any student to see detailed risk assessment

## What Gets Processed

For each uploaded file, the system:
- ✅ Creates/updates student records
- ✅ Creates academic records (grades, GPA)
- ✅ Creates attendance records
- ✅ Triggers ML risk prediction for each student
- ✅ Generates risk assessments with scores and explanations
- ✅ Creates alerts for high-risk students
- ✅ Updates all pages automatically

## Expected Results

After uploading `mock_student_data.json`, you should see:
- **1 student** created (Alex Johnson)
- **9 academic records** (grades showing declining performance)
- **70 attendance records** (showing worsening attendance)
- **1 risk assessment** with:
  - Risk Level: **High** (due to declining GPA and poor attendance)
  - Risk Score: **~65-75** (indicating high risk)
  - Contributing Factors:
    - Critical GPA Below Threshold
    - Rapid GPA Decline
    - Critical Attendance Below Threshold
    - Rapid Attendance Decline
    - Sudden Behavioral Change

## Troubleshooting

### Upload Fails
- Check file format (must be .csv, .xlsx, .xls, or .json)
- Ensure required fields are present (student_id, full_name)
- Check backend logs for specific errors

### No Risk Assessments Created
- Ensure academic or attendance records were created
- Check that ML model is trained (go to Settings > ML Model)
- Verify backend is running and connected to database

### Data Not Showing on Pages
- Refresh the page
- Check that data was successfully created (see upload results)
- Verify database connection

## Next Steps

1. **Train ML Model**: If not already trained, go to Settings and train the model with your data
2. **Upload More Data**: Add more students to improve model accuracy
3. **Monitor Students**: Use Dashboard and Risk Analysis pages to track at-risk students
4. **Create Interventions**: Use Interventions page to assign support to high-risk students

## Technical Details

### Backend Endpoint
- **POST** `/api/upload`
- Accepts: `multipart/form-data` with file
- Returns: Processing results with counts and errors

### ML Model Integration
- Uses `risk_engine.predict_risk()` with `use_ml=True`
- Automatically triggers after each student upload
- Supports rule-based fallback if ML model not trained

### Database Integration
- Stores data in Supabase
- All tables: `students`, `academic_records`, `attendance_records`, `risk_assessments`, `alerts`
- Automatic risk assessment triggers on data creation
