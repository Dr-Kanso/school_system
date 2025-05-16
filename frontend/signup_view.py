from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox, QSpacerItem, QComboBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from backend.auth_manager import AuthManager
from backend.firestore_manager import FirestoreManager

class SignupView(QWidget):
    """Signup view for user registration"""
    
    # Signals
    signup_successful = Signal(str, str, str, str)  # id_token, user_uid, role, name
    login_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.auth_manager = AuthManager()
        self.firestore_manager = FirestoreManager()
        self.setup_ui()
    
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
        subtitle_label = QLabel("Create a new account")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Add spacing
        main_layout.addSpacerItem(QSpacerItem(20, 40))
        
        # Form layout for signup fields
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        form_layout.addRow("Full Name:", self.name_input)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addRow("Email:", self.email_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)
        
        # Confirm password field
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Role selection
        self.role_dropdown = QComboBox()
        self.role_dropdown.addItems(["teacher", "administrator"])
        form_layout.addRow("Role:", self.role_dropdown)
        
        main_layout.addLayout(form_layout)
        
        # Add spacing
        main_layout.addSpacerItem(QSpacerItem(20, 20))
        
        # Signup button
        self.signup_button = QPushButton("Sign Up")
        self.signup_button.setMinimumHeight(40)
        self.signup_button.clicked.connect(self.handle_signup)
        main_layout.addWidget(self.signup_button)
        
        # Login link
        login_layout = QHBoxLayout()
        login_layout.addStretch()
        login_label = QLabel("Already have an account?")
        login_layout.addWidget(login_label)
        
        login_link = QPushButton("Log in")
        login_link.setFlat(True)
        login_link.setCursor(Qt.PointingHandCursor)
        login_link.clicked.connect(self.handle_login_requested)
        login_layout.addWidget(login_link)
        login_layout.addStretch()
        
        main_layout.addLayout(login_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def handle_signup(self):
        """Handle signup button click"""
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role = self.role_dropdown.currentText()
        
        # Input validation
        if not name or not email or not password or not confirm_password:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Password Error", "Passwords do not match.")
            return
        
        # Attempt to signup
        success, id_token, user_uid, error_message = self.auth_manager.sign_up(email, password)
        
        if success:
            # Create user profile in Firestore
            profile_success, profile_error = self.firestore_manager.create_user_profile(
                id_token, user_uid, email, role, name
            )
            
            if profile_success:
                self.signup_successful.emit(id_token, user_uid, role, name)
            else:
                QMessageBox.warning(
                    self, 
                    "Profile Creation Failed", 
                    f"Account was created but profile setup failed: {profile_error}"
                )
        else:
            QMessageBox.critical(self, "Signup Failed", f"Failed to create account: {error_message}")
    
    def handle_login_requested(self):
        """Handle login link click"""
        self.login_requested.emit()
