from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.utils import secure_filename
import openpyxl
from openpyxl import Workbook
import os
from datetime import datetime
import json
import re

app = Flask(__name__)
CORS(app)

# Validation functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_mobile(mobile):
    """Validate mobile number (exactly 10 digits)"""
    # Remove any spaces, dashes, or other characters
    mobile_clean = re.sub(r'[^\d]', '', mobile)
    return len(mobile_clean) == 10 and mobile_clean.isdigit()

def validate_name(name):
    """Validate name (should contain only letters, spaces, and common name characters)"""
    # Allow letters, spaces, hyphens, apostrophes, and dots
    pattern = r'^[a-zA-Z\s.\'-]+$'
    return len(name.strip()) >= 2 and re.match(pattern, name) is not None

# MongoDB connection with error handling
client = None
db = None
students_collection = None

def connect_to_mongodb():
    """Connect to MongoDB with error handling"""
    global client, db, students_collection
    try:
        # Try default port first (27017), then fallback to 27018
        try:
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
            client.server_info()  # Force connection to check if it works
            print("[SUCCESS] Connected to MongoDB on port 27017")
        except Exception as e:
            print(f"[FAILED] Connection to port 27017 failed: {e}")
            print("Trying port 27018...")
            try:
                client = MongoClient('mongodb://localhost:27018/', serverSelectionTimeoutMS=5000)
                client.server_info()
                print("[SUCCESS] Connected to MongoDB on port 27018")
            except Exception as e2:
                print(f"[FAILED] Connection to port 27018 also failed: {e2}")
                # Reset to None on failure
                client = None
                db = None
                students_collection = None
                raise
        
        # Ensure we have a valid client before accessing database
        if not client:
            raise Exception("MongoDB client is None")
        
        db = client['student_management']
        students_collection = db['students']
        
        # Verify collection is accessible by trying a simple operation
        try:
            students_collection.find_one({})
        except Exception as e:
            raise Exception(f"Collection access failed: {e}")
        
        print("[SUCCESS] Database 'student_management' and collection 'students' ready")
        return True
    except Exception as e:
        print(f"[ERROR] MongoDB Connection Error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure MongoDB is installed and running")
        print("2. Check if MongoDB is running on the correct port")
        print("3. Try starting MongoDB with: mongod (or check Windows Services)")
        print("4. Default MongoDB port is 27017")
        print("5. Run 'python test_mongodb_connection.py' to test connection")
        print("\n[WARNING] App will start but database operations will fail until MongoDB is connected.")
        # Reset to None on failure
        client = None
        db = None
        students_collection = None
        return False

# Try to connect on startup
connect_to_mongodb()

# Ensure uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Custom JSON encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

@app.route('/')
def index():
    return render_template('index.html')

# Error handlers to return JSON instead of HTML
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    import traceback
    error_trace = traceback.format_exc()
    print(f"Internal server error: {error_trace}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(NotImplementedError)
def not_implemented(error):
    import traceback
    error_trace = traceback.format_exc()
    print(f"NotImplementedError: {error_trace}")
    return jsonify({'error': f'Database operation not supported: {str(error)}'}), 500

# Note: We don't catch all exceptions here as it would interfere with Flask's normal error handling
# Instead, we ensure all API routes have proper try-catch blocks

# Get all students with optional search
@app.route('/api/students', methods=['GET'])
def get_students():
    # Ensure connection is valid - use explicit None comparison
    if students_collection is None or client is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        # Double-check collection is valid
        if students_collection is None:
            return jsonify({'error': 'Database collection not initialized'}), 503
        
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            # Search across all fields (case-insensitive)
            query = {
                '$or': [
                    {'reg_no': {'$regex': search_query, '$options': 'i'}},
                    {'name': {'$regex': search_query, '$options': 'i'}},
                    {'email': {'$regex': search_query, '$options': 'i'}},
                    {'mobile': {'$regex': search_query, '$options': 'i'}},
                    {'address': {'$regex': search_query, '$options': 'i'}}
                ]
            }
        else:
            query = {}
        
        students = list(students_collection.find(query).sort('name', 1))
        
        # Convert ObjectId to string
        for student in students:
            student['_id'] = str(student['_id'])
        
        return jsonify(students)
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_students: {error_trace}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# Get single student
@app.route('/api/students/<student_id>', methods=['GET'])
def get_student(student_id):
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        if student:
            student['_id'] = str(student['_id'])
            return jsonify(student)
        return jsonify({'error': 'Student not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid student ID or database error: {str(e)}'}), 400

# Create new student
@app.route('/api/students', methods=['POST'])
def create_student():
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    data = request.json
    
    # Validate required fields
    required_fields = ['reg_no', 'name', 'email', 'mobile', 'address']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate name
    if not validate_name(data['name']):
        return jsonify({'error': 'Name should contain only letters, spaces, and common name characters (minimum 2 characters)'}), 400
    
    # Validate email
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format. Please enter a valid email address'}), 400
    
    # Validate mobile (10 digits)
    mobile_clean = re.sub(r'[^\d]', '', data['mobile'])
    if not validate_mobile(data['mobile']):
        return jsonify({'error': 'Mobile number must be exactly 10 digits'}), 400
    
    # Validate address
    if len(data['address'].strip()) < 5:
        return jsonify({'error': 'Address must be at least 5 characters long'}), 400
    
    # Check if reg_no already exists
    if students_collection.find_one({'reg_no': data['reg_no']}):
        return jsonify({'error': 'Registration number already exists'}), 400
    
    # Insert student - automatically saved to MongoDB database
    result = students_collection.insert_one({
        'reg_no': data['reg_no'].strip(),
        'name': data['name'].strip(),
        'email': data['email'].strip().lower(),
        'mobile': mobile_clean,  # Store cleaned mobile number
        'address': data['address'].strip()
    })
    
    # Verify the data was saved by retrieving it from database
    student = students_collection.find_one({'_id': result.inserted_id})
    if student:
        student['_id'] = str(student['_id'])
        return jsonify(student), 201
    else:
        return jsonify({'error': 'Failed to save student to database'}), 500

# Update student
@app.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['reg_no', 'name', 'email', 'mobile', 'address']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate name
        if not validate_name(data['name']):
            return jsonify({'error': 'Name should contain only letters, spaces, and common name characters (minimum 2 characters)'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format. Please enter a valid email address'}), 400
        
        # Validate mobile (10 digits)
        mobile_clean = re.sub(r'[^\d]', '', data['mobile'])
        if not validate_mobile(data['mobile']):
            return jsonify({'error': 'Mobile number must be exactly 10 digits'}), 400
        
        # Validate address
        if len(data['address'].strip()) < 5:
            return jsonify({'error': 'Address must be at least 5 characters long'}), 400
        
        # Check if reg_no already exists for another student
        existing = students_collection.find_one({'reg_no': data['reg_no']})
        if existing and str(existing['_id']) != student_id:
            return jsonify({'error': 'Registration number already exists'}), 400
        
        # Update student - automatically saved to MongoDB database
        update_data = {
            'reg_no': data['reg_no'].strip(),
            'name': data['name'].strip(),
            'email': data['email'].strip().lower(),
            'mobile': mobile_clean,  # Store cleaned mobile number
            'address': data['address'].strip()
        }
        
        result = students_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Student not found in database'}), 404
        
        # Verify the update was saved by retrieving from database
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        if student:
            student['_id'] = str(student['_id'])
            return jsonify(student)
        else:
            return jsonify({'error': 'Failed to update student in database'}), 500
    except Exception as e:
        return jsonify({'error': f'Invalid student ID or database error: {str(e)}'}), 400

# Delete student
@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        # Delete from MongoDB database - automatically synced
        result = students_collection.delete_one({'_id': ObjectId(student_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Student not found in database'}), 404
        # Verify deletion by checking if record still exists
        verify = students_collection.find_one({'_id': ObjectId(student_id)})
        if verify:
            return jsonify({'error': 'Failed to delete student from database'}), 500
        return jsonify({'message': 'Student deleted successfully from database'})
    except Exception as e:
        return jsonify({'error': f'Invalid student ID or database error: {str(e)}'}), 400

# Clear all students
@app.route('/api/students/clear', methods=['DELETE'])
def clear_all_students():
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        result = students_collection.delete_many({})
        return jsonify({
            'message': f'Successfully deleted {result.deleted_count} student(s)',
            'deleted_count': result.deleted_count
        })
    except Exception as e:
        return jsonify({'error': f'Error clearing data: {str(e)}'}), 500

# Import from Excel
@app.route('/api/students/import', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file format. Please upload Excel file (.xlsx or .xls)'}), 400
    
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Initialize counters
        imported_count = 0
        errors = []
        total_rows_processed = 0
        
        # Read Excel file - use context manager to ensure proper cleanup
        workbook = None
        try:
            workbook = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            sheet = workbook.active
            
            # Expected columns: Reg No, Name, Email, Mobile, Address
            # Try to detect header row - check if first row looks like headers
            first_row = None
            start_row = 2  # Default to row 2 (assuming row 1 is header)
            
            try:
                first_row_values = list(sheet.iter_rows(min_row=1, max_row=1, values_only=True))[0]
                # Check if first row contains header-like text
                header_keywords = ['reg', 'name', 'email', 'mobile', 'address']
                first_row_text = ' '.join([str(cell).lower() if cell else '' for cell in first_row_values])
                if any(keyword in first_row_text for keyword in header_keywords):
                    start_row = 2  # First row is header, start from row 2
                else:
                    start_row = 1  # No header row, start from row 1
            except:
                start_row = 2  # Default to row 2 if detection fails
            
            for row_idx, row in enumerate(sheet.iter_rows(min_row=start_row, values_only=True), start=start_row):
                # Skip if all cells are empty or None
                if not any(cell is not None and str(cell).strip() for cell in row):
                    continue
                
                total_rows_processed += 1
                
                try:
                    # Extract values, handling None and empty strings
                    reg_no = str(row[0]).strip() if row[0] is not None and str(row[0]).strip() else ''
                    name = str(row[1]).strip() if len(row) > 1 and row[1] is not None and str(row[1]).strip() else ''
                    email = str(row[2]).strip() if len(row) > 2 and row[2] is not None and str(row[2]).strip() else ''
                    mobile = str(row[3]).strip() if len(row) > 3 and row[3] is not None and str(row[3]).strip() else ''
                    address = str(row[4]).strip() if len(row) > 4 and row[4] is not None and str(row[4]).strip() else ''
                    
                    # Required fields: reg_no and name
                    if not reg_no or not name:
                        errors.append(f'Row {row_idx}: Missing required fields (Reg No and Name are required)')
                        continue
                    
                    # Validate name
                    if not validate_name(name):
                        errors.append(f'Row {row_idx}: Invalid name format (must contain only letters, spaces, and common name characters, minimum 2 characters)')
                        continue
                    
                    # Validate email (optional but must be valid if provided)
                    if email and not validate_email(email):
                        errors.append(f'Row {row_idx}: Invalid email format')
                        continue
                    
                    # Validate and clean mobile (optional but must be valid if provided)
                    mobile_clean = re.sub(r'[^\d]', '', mobile)
                    if mobile_clean and not validate_mobile(mobile_clean):
                        errors.append(f'Row {row_idx}: Mobile number must be exactly 10 digits (if provided)')
                        continue
                    
                    # Validate address (optional but must be at least 5 chars if provided)
                    if address and len(address) < 5:
                        errors.append(f'Row {row_idx}: Address must be at least 5 characters (if provided)')
                        continue
                    
                    # Check if reg_no already exists
                    if students_collection.find_one({'reg_no': reg_no}):
                        errors.append(f'Row {row_idx}: Registration number {reg_no} already exists in database')
                        continue
                    
                    # Insert student - automatically saved to MongoDB database
                    result = students_collection.insert_one({
                        'reg_no': reg_no,
                        'name': name,
                        'email': email.lower() if email else '',
                        'mobile': mobile_clean if mobile_clean else '',
                        'address': address if address else ''
                    })
                    
                    # Verify the data was saved by retrieving it from database
                    verify = students_collection.find_one({'_id': result.inserted_id})
                    if verify:
                        imported_count += 1
                        print(f"[SUCCESS] Imported student: {reg_no} - {name}")
                    else:
                        errors.append(f'Row {row_idx}: Failed to save to database')
                except Exception as e:
                    errors.append(f'Row {row_idx}: {str(e)}')
                    print(f"[ERROR] Row {row_idx} error: {str(e)}")
            
            # If no rows were processed at all, provide helpful message
            if total_rows_processed == 0:
                errors.append('No data rows found in Excel file. Please ensure your file has data rows with at least Reg No and Name columns.')
        finally:
            # Close workbook before deleting file
            if workbook:
                workbook.close()
        
        # Clean up uploaded file - now safe to delete
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Could not delete temporary file {filepath}: {e}")
        
        # Provide detailed response
        response_data = {
            'message': f'Import completed: {imported_count} student(s) imported and saved to MongoDB database' if imported_count > 0 else 'Import completed with no students imported',
            'imported': imported_count,
            'errors': errors,
            'saved_to_database': imported_count > 0,
            'total_rows_processed': total_rows_processed
        }
        
        print(f"[IMPORT SUMMARY] Imported: {imported_count}, Errors: {len(errors)}, Total rows processed: {total_rows_processed}")
        
        return jsonify(response_data)
    except Exception as e:
        # Try to clean up file even on error
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up file {filepath}: {cleanup_error}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

# Export to Excel
@app.route('/api/students/export', methods=['GET'])
def export_excel():
    if students_collection is None:
        if not connect_to_mongodb():
            return jsonify({'error': 'Database connection failed. Please ensure MongoDB is running.'}), 503
    
    try:
        students = list(students_collection.find().sort('name', 1))
        
        # Create workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Students'
        
        # Headers
        headers = ['Reg No', 'Name', 'Email', 'Mobile', 'Address']
        sheet.append(headers)
        
        # Style headers
        from openpyxl.styles import Font, PatternFill
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        
        for cell in sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
        
        # Add data
        for student in students:
            sheet.append([
                student.get('reg_no', ''),
                student.get('name', ''),
                student.get('email', ''),
                student.get('mobile', ''),
                student.get('address', '')
            ])
        
        # Auto-adjust column widths
        for column in sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass
            adjusted_width = min(max_length + 2, 50)
            sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to temporary file
        filename = f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        workbook.save(filepath)
        
        return send_file(filepath, as_attachment=True, download_name='students.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({'error': f'Error exporting file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

