from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from frontend.manage_students_view import ManageStudentsView
from frontend.term_management_view import TermManagementView
from frontend.assign_teachers_view import AssignTeachersView
from frontend.reports_view import ReportsView

class AdminDashboard(QWidget):
    """Dashboard view for administrators"""
    
    # Add logout signal
    logout_requested = Signal()
    
    def __init__(self, id_token, user_uid, name=""):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.user_name = name
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title with admin name
        title_text = f"Administrator Dashboard - Welcome, {self.user_name}" if self.user_name else "Administrator Dashboard"
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
        
        # Tab widget for different admin functions
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.students_tab = ManageStudentsView(self.id_token, self.user_uid)
        self.terms_tab = TermManagementView(self.id_token, self.user_uid)
        self.teachers_tab = AssignTeachersView(self.id_token, self.user_uid)
        self.reports_tab = ReportsView(self.id_token, self.user_uid, is_admin=True)
        
        # Add tabs to widget
        self.tab_widget.addTab(self.students_tab, "Manage Students")
        self.tab_widget.addTab(self.teachers_tab, "Assign Teachers")
        self.tab_widget.addTab(self.terms_tab, "Manage Terms")
        self.tab_widget.addTab(self.reports_tab, "Reports")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
    
    def handle_logout(self):
        """Handle logout button click"""
        self.logout_requested.emit()
