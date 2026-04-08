# Universal File Format Support

## Overview
The upload system now supports **ALL file formats** with automatic format detection. The backend intelligently detects the file type and encoding, then processes it accordingly.

## Supported Formats

### Automatically Detected Formats

1. **JSON** (`.json`, `.jsonl`)
   - Single student objects
   - Arrays of students
   - Nested structures

2. **Excel** (`.xlsx`, `.xls`, `.xlsm`, `.xlsb`)
   - All Excel formats
   - Multiple sheets (first sheet used)

3. **CSV** (`.csv`)
   - Comma-separated values
   - Standard CSV format

4. **TSV** (`.tsv`, `.txt` with tabs)
   - Tab-separated values
   - Auto-detected delimiter

5. **Text Files** (`.txt`, any text format)
   - Auto-detected delimiters (comma, tab, semicolon, pipe)
   - Auto-detected encoding (UTF-8, ASCII, etc.)

6. **Other Formats**
   - Any file format will be attempted
   - Falls back to text/CSV parsing if other formats fail

## How It Works

### Automatic Detection Process

1. **File Extension Check**
   - Checks file extension first (`.json`, `.csv`, `.xlsx`, etc.)

2. **Content Type Check**
   - Checks MIME type from browser/upload

3. **Content Analysis**
   - Tries to parse as JSON first
   - Checks for CSV delimiters (comma, tab, semicolon, pipe)
   - Falls back to Excel format
   - Last resort: text parsing

4. **Encoding Detection**
   - Uses `chardet` library to detect file encoding
   - Falls back to UTF-8 if detection fails
   - Handles various encodings (UTF-8, ASCII, Latin-1, etc.)

### Delimiter Detection

For text/CSV files, the system automatically detects:
- **Comma** (`,`) - Standard CSV
- **Tab** (`\t`) - TSV format
- **Semicolon** (`;`) - European CSV
- **Pipe** (`|`) - Pipe-delimited

## Usage

### Frontend
- **No restrictions** - Upload any file type
- File picker accepts all files (`accept="*/*"`)
- Backend handles format detection automatically

### Backend
- Automatically detects format
- Logs detected format and encoding
- Provides detailed error messages if parsing fails

## Example File Formats

### JSON Format
```json
{
  "student": {
    "student_id": "STU001",
    "full_name": "John Doe"
  },
  "academic_records": [...],
  "attendance_records": [...]
}
```

### CSV Format
```csv
student_id,full_name,grade,gpa,course_code
STU001,John Doe,85.5,3.4,CS101
```

### TSV Format
```tsv
student_id	full_name	grade	gpa	course_code
STU001	John Doe	85.5	3.4	CS101
```

### Excel Format
- Standard Excel spreadsheet
- First row as headers
- Data in subsequent rows

## Error Handling

### Format Detection Failures
- Tries multiple parsing methods
- Provides specific error messages
- Suggests format corrections if possible

### Encoding Issues
- Auto-detects encoding
- Handles encoding errors gracefully
- Falls back to UTF-8

### Parsing Errors
- Detailed error messages
- Row-by-row error tracking
- Continues processing valid rows

## Logging

The system logs:
- File name and size
- Detected format type
- Detected encoding
- Delimiter used (for CSV/TSV)
- Processing statistics

## Benefits

1. **User-Friendly**: No need to worry about file format
2. **Flexible**: Works with any data format
3. **Robust**: Multiple fallback mechanisms
4. **Intelligent**: Auto-detects format and encoding
5. **Error-Resilient**: Continues processing even with some errors

## Technical Details

### Dependencies Added
- `chardet==5.2.0` - Encoding detection

### Code Changes
- Backend: Enhanced format detection logic
- Frontend: Removed file type restrictions
- Both: Improved error handling

## Troubleshooting

### File Not Parsing
1. Check file encoding (should be UTF-8 for best results)
2. Verify file structure matches expected format
3. Check backend logs for detected format
4. Try saving file in a different format

### Encoding Issues
1. Save file as UTF-8
2. Check for special characters
3. Review backend logs for detected encoding

### Format Detection Issues
1. Ensure file has proper extension
2. Check file content structure
3. Review backend logs for detection process

## Future Enhancements

Potential additions:
- XML format support
- PDF text extraction
- Database import formats
- API endpoint integration
- Cloud storage integration
