from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QFormLayout, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ManageStudentsView(QWidget):
    """View for managing student records"""
    
    def __init__(self, id_token, user_uid):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Manage Students")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Student input form
        form_layout = QFormLayout()
        
        self.student_name_input = QLineEdit()
        form_layout.addRow("Student Name:", self.student_name_input)
        
        self.student_id_input = QLineEdit()
        form_layout.addRow("Student ID:", self.student_id_input)
        
        self.class_input = QLineEdit()
        form_layout.addRow("Class:", self.class_input)
        
        button_layout = QHBoxLayout()
        self.add_student_button = QPushButton("Add Student")
        self.clear_form_button = QPushButton("Clear")
        
        button_layout.addWidget(self.add_student_button)
        button_layout.addWidget(self.clear_form_button)
        
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        
        # Students table
        self.students_table = QTableView()
        main_layout.addWidget(self.students_table)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.add_student_button.clicked.connect(self.add_student)
        self.clear_form_button.clicked.connect(self.clear_form)
    
    def add_student(self):
        """Handle adding a new student"""
        # Placeholder implementation
        QMessageBox.information(self, "Add Student", "Student add functionality not yet implemented")
    
    def clear_form(self):
        """Clear the input form"""
        self.student_name_input.clear()
        self.student_id_input.clear()
        self.class_input.clear()
