from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from frontend.attendance_register_view import AttendanceRegisterView
from frontend.input_results_view import InputResultsView
from frontend.reports_view import ReportsView

class TeacherDashboard(QWidget):
    """Dashboard view for teachers"""
    
    # Add logout signal
    logout_requested = Signal()
    
    def __init__(self, id_token, user_uid, name=""):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.user_name = name
        # Debug: Print the user_uid to verify it's set correctly
        print(f"Teacher Dashboard initialized with user_uid: {self.user_uid}")
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title with teacher name
        title_text = f"Teacher Dashboard - Welcome, {self.user_name}" if self.user_name else "Teacher Dashboard"
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setFixedWidth(100)
        self.logout_button.clicked.connect(self.handle_logout)  # Connect to logout handler
        header_layout.addWidget(self.logout_button)
        
        main_layout.addLayout(header_layout)
        
        # Tab widget for different teacher functions
        self.tab_widget = QTabWidget()
        
        # Create tabs and ensure user_uid is passed correctly
        self.attendance_tab = AttendanceRegisterView(self.id_token, self.user_uid)
        self.results_tab = InputResultsView(self.id_token, self.user_uid)
        self.reports_tab = ReportsView(self.id_token, self.user_uid, is_admin=False)
        
        # Add tabs to widget
        self.tab_widget.addTab(self.attendance_tab, "Attendance Register")
        self.tab_widget.addTab(self.results_tab, "Input Results")
        self.tab_widget.addTab(self.reports_tab, "View Reports")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
    
    def handle_logout(self):
        """Handle logout button click"""
        self.logout_requested.emit()
