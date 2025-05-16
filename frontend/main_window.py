from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtCore import Slot

from frontend.login_view import LoginView
from frontend.signup_view import SignupView
from frontend.admin_dashboard import AdminDashboard
from frontend.teacher_dashboard import TeacherDashboard

from backend.auth_manager import AuthManager
from backend.firestore_manager import FirestoreManager

class MainWindow(QMainWindow):
    """Main window for the School Management System application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Management System")
        self.resize(1200, 800)
        
        # Initialize managers
        self.auth_manager = AuthManager()
        self.firestore_manager = FirestoreManager()
        
        # Initialize current user data
        self.current_user = None
        self.id_token = None
        self.user_uid = None
        
        # Set up the stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create views
        self.login_view = LoginView()
        self.signup_view = SignupView()
        self.admin_dashboard = None
        self.teacher_dashboard = None
        
        # Add views to stacked widget
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.signup_view)
        
        # Connect signals from login view
        self.login_view.login_successful.connect(self.on_login_successful)
        self.login_view.signup_requested.connect(self.show_signup_view)
        
        # Connect signals from signup view
        self.signup_view.signup_successful.connect(self.on_signup_successful)
        self.signup_view.login_requested.connect(self.show_login_view)
        
        # Show login view by default
        self.stacked_widget.setCurrentWidget(self.login_view)
    
    @Slot(str, str)
    def on_login_successful(self, id_token, user_uid):
        """Handle successful login"""
        self.id_token = id_token
        self.user_uid = user_uid
        
        # Get the user's profile from Firestore
        success, profile, error_message = self.firestore_manager.get_user_profile(id_token, user_uid)
        
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to get user profile: {error_message}")
            return
        
        role = profile.get("role", "")
        name = profile.get("name", "")
        
        # Show the appropriate dashboard based on the user's role
        if role == "administrator":
            if not self.admin_dashboard:
                self.admin_dashboard = AdminDashboard(self.id_token, self.user_uid, name)
                self.stacked_widget.addWidget(self.admin_dashboard)
            self.stacked_widget.setCurrentWidget(self.admin_dashboard)
        elif role == "teacher":
            if not self.teacher_dashboard:
                self.teacher_dashboard = TeacherDashboard(self.id_token, self.user_uid, name)
                self.stacked_widget.addWidget(self.teacher_dashboard)
            self.stacked_widget.setCurrentWidget(self.teacher_dashboard)
        else:
            QMessageBox.warning(self, "Unknown Role", f"User has unknown role: {role}")
    
    @Slot(str, str, str, str)
    def on_signup_successful(self, id_token, user_uid, role, name):
        """Handle successful signup"""
        self.id_token = id_token
        self.user_uid = user_uid
        
        # Show the appropriate dashboard based on the user's role
        if role == "administrator":
            if not self.admin_dashboard:
                self.admin_dashboard = AdminDashboard(self.id_token, self.user_uid, name)
                self.stacked_widget.addWidget(self.admin_dashboard)
            self.stacked_widget.setCurrentWidget(self.admin_dashboard)
        elif role == "teacher":
            if not self.teacher_dashboard:
                self.teacher_dashboard = TeacherDashboard(self.id_token, self.user_uid, name)
                self.stacked_widget.addWidget(self.teacher_dashboard)
            self.stacked_widget.setCurrentWidget(self.teacher_dashboard)
    
    @Slot()
    def show_signup_view(self):
        """Switch to signup view"""
        self.stacked_widget.setCurrentWidget(self.signup_view)
    
    @Slot()
    def show_login_view(self):
        """Switch to login view"""
        self.stacked_widget.setCurrentWidget(self.login_view)
