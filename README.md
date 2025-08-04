# School Management System

A comprehensive school management system built with Python, featuring student enrollment, attendance tracking, grade management, and reporting capabilities.

## Features

- **Authentication System**: Secure login for administrators and teachers
- **Student Management**: Enroll, edit, and manage student records
- **Attendance Tracking**: Mark and monitor student attendance
- **Grade Management**: Input and manage student exam results
- **Term Management**: Configure academic terms and assessment settings
- **Teacher Assignment**: Assign teachers to classes and subjects
- **Reporting**: Generate comprehensive academic reports

## Tech Stack

- **Backend**: Python with Firebase integration
- **Frontend**: PyQt5 for desktop GUI
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd school_system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase:
   - Create a Firebase project
   - Enable Firestore Database and Authentication
   - Download your Firebase service account credentials
   - Create a `.env` file with your Firebase configuration

4. Run the application:
```bash
python app.py
```

## Project Structure

```
school_system/
├── app.py                 # Main application entry point
├── backend/               # Backend logic and models
│   ├── auth_manager.py
│   ├── firestore_manager.py
│   └── models.py
├── frontend/              # GUI components
│   ├── admin_dashboard.py
│   ├── teacher_dashboard.py
│   └── ...
├── services/              # Firebase integration services
│   ├── firebase_auth.py
│   └── firebase_service.py
└── utils/                 # Utility functions
    └── firebase_client.py
```

## Environment Variables

Create a `.env` file in the root directory with the following structure:

```
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_auth_domain
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_storage_bucket
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

## Usage

1. **Admin Login**: Use administrator credentials to access the admin dashboard
2. **Teacher Login**: Teachers can log in to access their assigned classes
3. **Student Management**: Add, edit, or remove student records
4. **Attendance**: Mark daily attendance for students
5. **Grades**: Input and manage student assessment results
6. **Reports**: Generate and export academic reports

## License

This project is licensed under the MIT License.