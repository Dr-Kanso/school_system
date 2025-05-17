from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox, QSpacerItem, QCheckBox
)
from PySide6.QtCore import Signal, Qt, QSettings
from PySide6.QtGui import QFont

from backend.auth_manager import AuthManager

class LoginView(QWidget):
    """Login view for authentication"""
    
    # Signals
    login_successful = Signal(str, str)  # id_token, user_uid
    signup_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.auth_manager = AuthManager()
        self.setup_ui()
        self.load_remembered_credentials()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(200, 100, 200, 100)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel("School Management System")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Login to your account")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Add spacing
        main_layout.addSpacerItem(QSpacerItem(20, 40))
        
        # Form layout for login fields
        form_layout = QFormLayout()
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addRow("Email:", self.email_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)
        
        main_layout.addLayout(form_layout)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember my details")
        main_layout.addWidget(self.remember_checkbox)
        
        # Add spacing
        main_layout.addSpacerItem(QSpacerItem(20, 20))
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_button)
        
        # Signup link
        signup_layout = QHBoxLayout()
        signup_layout.addStretch()
        signup_label = QLabel("Don't have an account?")
        signup_layout.addWidget(signup_label)
        
        signup_link = QPushButton("Sign up")
        signup_link.setFlat(True)
        signup_link.setCursor(Qt.PointingHandCursor)
        signup_link.clicked.connect(self.handle_signup_requested)
        signup_layout.addWidget(signup_link)
        signup_layout.addStretch()
        
        main_layout.addLayout(signup_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Input validation
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return
        
        # Attempt to login
        success, id_token, user_uid, error_message = self.auth_manager.sign_in(email, password)
        
        if success:
            # Save credentials if remember checkbox is checked
            if self.remember_checkbox.isChecked():
                self.save_remembered_credentials(email)
            else:
                # Clear any saved credentials if not checked
                self.clear_remembered_credentials()
                
            self.login_successful.emit(id_token, user_uid)
        else:
            QMessageBox.critical(self, "Login Failed", f"Failed to login: {error_message}")
    
    def handle_signup_requested(self):
        """Handle signup link click"""
        self.signup_requested.emit()
        
    def save_remembered_credentials(self, email):
        """Save the email for future logins"""
        settings = QSettings("SchoolSystem", "LoginDetails")
        settings.setValue("remembered_email", email)
    
    def load_remembered_credentials(self):
        """Load saved email if exists"""
        settings = QSettings("SchoolSystem", "LoginDetails")
        remembered_email = settings.value("remembered_email", "")
        if remembered_email:
            self.email_input.setText(remembered_email)
            self.remember_checkbox.setChecked(True)
    
    def clear_remembered_credentials(self):
        """Clear any saved credentials"""
        settings = QSettings("SchoolSystem", "LoginDetails")
        settings.remove("remembered_email")
