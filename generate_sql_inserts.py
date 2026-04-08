import pandas as pd
import uuid
from datetime import datetime

# Read the CSV file
df = pd.read_csv('mock_students_data.csv')

sql_statements = []
student_ids = {}

for idx, row in df.iterrows():
    roll_num = row['roll_number']
    
    # Create student record (only once per student)
    if roll_num not in student_ids:
        student_id = str(uuid.uuid4())
        student_ids[roll_num] = student_id
        
        # Escape single quotes in strings
        full_name = row['full_name'].replace("'", "''")
        department = row['department'].replace("'", "''")
        
        sql_statements.append(
            f"INSERT INTO students (id, student_id, full_name, email, department, program, year_level, semester, enrollment_date, status) "
            f"VALUES ('{student_id}', '{roll_num}', '{full_name}', '{row['email']}', '{department}', "
            f"'{row['program']}', {row['year_level']}, '{row['semester']}', CURRENT_DATE, 'active') "
            f"ON CONFLICT (student_id) DO NOTHING;"
        )
    
    # Create academic record
    acad_id = str(uuid.uuid4())
    course_name = row['course_name'].replace("'", "''")
    sql_statements.append(
        f"INSERT INTO academic_records (id, student_id, semester, course_code, course_name, grade, credits, gpa) "
        f"VALUES ('{acad_id}', '{student_ids[roll_num]}', '{row['semester']}', '{row['course_code']}', "
        f"'{course_name}', {row['grade']}, {row['credits']}, {row['gpa']}) "
        f"ON CONFLICT DO NOTHING;"
    )
    
    # Create attendance record
    att_id = str(uuid.uuid4())
    sql_statements.append(
        f"INSERT INTO attendance_records (id, student_id, date, status, course_code, semester) "
        f"VALUES ('{att_id}', '{student_ids[roll_num]}', '{row['attendance_date']}', '{row['attendance_status']}', "
        f"'{row['course_code']}', '{row['semester']}') "
        f"ON CONFLICT DO NOTHING;"
    )

# Write to SQL file
with open('insert_student_data.sql', 'w', encoding='utf-8') as f:
    f.write('-- Insert 30 student records with academic and attendance data\n')
    f.write('-- Generated from mock_students_data.csv\n')
    f.write('-- Date: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n\n')
    f.write('\n'.join(sql_statements))

print('Generated SQL file: insert_student_data.sql')
print(f'   - Students: {len(student_ids)}')
print(f'   - Academic records: {len(df)}')
print(f'   - Attendance records: {len(df)}')
print(f'   - Total INSERT statements: {len(sql_statements)}')
