# Student Management System

A web-based student management system built with Flask (Python) backend and HTML/CSS/JavaScript frontend. Features include CRUD operations, multi-field search, and Excel import/export functionality.

## Features

- **Student Management**: Add, edit, delete, and view student records
- **Search Functionality**: Search students by Registration Number, Name, Email, Mobile, or Address
- **Excel Import/Export**: Import student data from Excel files and export to Excel
- **Responsive Design**: Fully responsive for mobile, tablet, and desktop devices
- **Modern UI**: Clean and modern user interface with smooth animations

## Student Data Fields

- Registration Number (Reg No)
- Name
- Email ID
- Mobile Number
- Address

## Prerequisites

- Python 3.7 or higher
- MongoDB installed and running on localhost:27017

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MongoDB:**
   - Make sure MongoDB is installed and running on `localhost:27017`
   - If MongoDB is running on a different host/port, update the connection string in `app.py`

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`

## Excel Import Format

When importing from Excel, the file should have the following columns in order:
1. Reg No
2. Name
3. Email
4. Mobile
5. Address

The first row should contain headers (which will be skipped). Data starts from row 2.

## Usage

### Adding a Student
1. Click the "Add New Student" button
2. Fill in all required fields
3. Click "Save"

### Editing a Student
1. Click the "Edit" button next to the student you want to edit
2. Modify the fields
3. Click "Save"

### Deleting a Student
1. Click the "Delete" button next to the student you want to delete
2. Confirm the deletion

### Searching Students
- Type in the search bar to search across all fields (Reg No, Name, Email, Mobile, Address)
- Search is case-insensitive and supports partial matching

### Importing from Excel
1. Click "Import Excel"
2. Select an Excel file (.xlsx or .xls)
3. The system will import all valid records

### Exporting to Excel
1. Click "Export Excel"
2. The system will download an Excel file with all student records

## Project Structure

```
Student Website/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Main frontend page
├── static/
│   ├── css/
│   │   └── style.css      # Styling
│   └── js/
│       └── main.js        # Frontend JavaScript
├── uploads/               # Excel upload directory
└── README.md              # This file
```

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **Excel Handling**: openpyxl

## Notes

- The application uses MongoDB for data storage
- Excel files are temporarily stored in the `uploads/` directory during processing
- The search functionality searches across all student fields simultaneously
- All form fields are required for adding/editing students

