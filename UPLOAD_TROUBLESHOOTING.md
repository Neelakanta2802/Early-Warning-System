# Upload Troubleshooting Guide

## Recent Fixes Applied

### Backend (`main.py`)
1. ✅ Added file validation (checks if file exists and has content)
2. ✅ Added detailed logging for file uploads
3. ✅ Improved error messages with specific details
4. ✅ Better JSON parsing error handling
5. ✅ File size logging

### Frontend (`api.ts` & `DataUploadPage.tsx`)
1. ✅ Improved error handling in API client
2. ✅ Better error messages displayed to user
3. ✅ Failed uploads now tracked in history
4. ✅ Removed Content-Type header (let browser set it with boundary)

## Common Issues and Solutions

### Issue: "File not found" Error

**Possible Causes:**
1. File not selected properly
2. Backend not receiving the file
3. CORS issue
4. Backend not running

**Solutions:**

1. **Check Backend is Running:**
   ```powershell
   # Test backend health
   Invoke-WebRequest -Uri "http://localhost:8000/api/health"
   ```

2. **Check Browser Console:**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Look for error messages when uploading
   - Check Network tab to see the actual request/response

3. **Verify File Selection:**
   - Make sure file is actually selected (should show filename)
   - Try a different file format (CSV, Excel, or JSON)
   - Check file size (should be reasonable, not 0 bytes)

4. **Check API URL:**
   - Frontend should connect to `http://localhost:8000`
   - Check browser console for CORS errors
   - Verify `.env` file has correct `VITE_API_URL` if set

5. **Test with Mock Data:**
   - Use the provided `mock_student_data.json`
   - Make sure file is in a location you can access
   - Try uploading from different location

### Issue: "File is empty" Error

**Solution:**
- Make sure the file has content
- Check file encoding (should be UTF-8 for JSON)
- Try recreating the file

### Issue: "Invalid JSON format" Error

**Solution:**
- Validate JSON syntax using a JSON validator
- Check for trailing commas
- Ensure proper structure (see `mock_student_data.json` for reference)

### Issue: Backend Not Responding

**Solution:**
1. Check if backend is running:
   ```powershell
   netstat -ano | findstr "8000"
   ```

2. Restart backend:
   ```powershell
   cd "project/backend"
   python run.py
   ```

3. Check backend logs for errors

## Testing the Upload

### Step 1: Verify Backend
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/health"
```
Should return: `{"status":"healthy",...}`

### Step 2: Test File Upload (using PowerShell)
```powershell
$filePath = "project\mock_student_data.json"
$fileContent = Get-Content $filePath -Raw
$boundary = [System.Guid]::NewGuid().ToString()
$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"mock_student_data.json`"",
    "Content-Type: application/json",
    "",
    $fileContent,
    "--$boundary--"
)
$body = $bodyLines -join "`r`n"
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/upload" -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary"
$response.Content
```

### Step 3: Check Browser Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Upload a file
4. Click on the `/api/upload` request
5. Check:
   - Request payload (should show file data)
   - Response (should show success/error)
   - Status code (200 = success, 4xx/5xx = error)

## Expected Behavior

### Successful Upload Response:
```json
{
  "success": true,
  "filename": "mock_student_data.json",
  "students_processed": 1,
  "students_created": 1,
  "academic_records_created": 9,
  "attendance_records_created": 70,
  "risk_assessments_created": 1,
  "errors": []
}
```

### Error Response:
```json
{
  "detail": "Error message here"
}
```

## Debug Steps

1. **Check Backend Logs:**
   - Look for log messages starting with "Received file upload"
   - Check for error messages

2. **Check Frontend Console:**
   - Open browser console
   - Look for error messages
   - Check Network tab for failed requests

3. **Verify File Format:**
   - JSON: Must be valid JSON
   - CSV: Must have proper headers
   - Excel: Must be .xlsx or .xls format

4. **Check Database Connection:**
   - Backend needs Supabase credentials
   - Check `.env` file in backend directory
   - Verify database is accessible

## Still Having Issues?

1. Check backend terminal for detailed error messages
2. Check browser console for frontend errors
3. Verify both servers are running (backend on 8000, frontend on 5173)
4. Try uploading a smaller test file first
5. Check file permissions (make sure file is readable)
