# ---------------------------------------------
# Student Website (Full Flask App with MongoDB Atlas)
# Updated: 2025-11-11
# ---------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import datetime
import openpyxl
from dotenv import load_dotenv
import os

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Flask Setup ----------
app = Flask(__name__)
CORS(app)

# ---------- MongoDB Atlas Setup ----------
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    db = client["student_database"]
    collection = db["students"]
    print("[SUCCESS] Connected to MongoDB Atlas ✅")
except Exception as e:
    print(f"[ERROR] MongoDB Atlas Connection Failed: {e}")
    client = None
    db = None
    collection = None

# ---------- Helper Function ----------
def get_students():
    try:
        data = list(collection.find({}, {"_id": 0}))
        return data
    except Exception as e:
        print(f"[ERROR] Fetching students failed: {e}")
        return []

# ---------- Routes ----------

@app.route('/')
def index():
    try:
        students = get_students()
        return render_template('index.html', students=students)
    except Exception as e:
        return f"Error loading students: {e}"

@app.route('/add', methods=['POST'])
def add_student():
    try:
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_student = {
            "name": name,
            "email": email,
            "department": department,
            "created_at": created_at
        }

        collection.insert_one(new_student)
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error adding student: {e}"

@app.route('/api/students', methods=['GET'])
def api_students():
    data = get_students()
    return jsonify(data)

@app.route('/delete/<email>', methods=['GET'])
def delete_student(email):
    try:
        collection.delete_one({"email": email})
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error deleting student: {e}"

@app.route('/export', methods=['GET'])
def export_to_excel():
    try:
        students = get_students()
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Students"

        headers = ["Name", "Email", "Department", "Created_At"]
        sheet.append(headers)

        for s in students:
            sheet.append([s["name"], s["email"], s["department"], s["created_at"]])

        filename = "students_export.xlsx"
        workbook.save(filename)
        return jsonify({"status": "success", "message": f"Exported to {filename}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ---------- Health Check ----------
@app.route('/health')
def health_check():
    return jsonify({"status": "running", "database": bool(db)})

# ---------- Error Handlers ----------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# ---------- Run ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
