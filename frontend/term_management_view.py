from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QFormLayout, QLineEdit, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class TermManagementView(QWidget):
    """View for managing academic terms"""
    
    def __init__(self, id_token, user_uid):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Manage Academic Terms")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Term input form
        form_layout = QFormLayout()
        
        self.term_name_input = QLineEdit()
        form_layout.addRow("Term Name:", self.term_name_input)
        
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Start Date:", self.start_date_input)
        
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate().addMonths(3))
        form_layout.addRow("End Date:", self.end_date_input)
        
        button_layout = QHBoxLayout()
        self.add_term_button = QPushButton("Add Term")
        self.clear_form_button = QPushButton("Clear")
        
        button_layout.addWidget(self.add_term_button)
        button_layout.addWidget(self.clear_form_button)
        
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        
        # Terms table
        self.terms_table = QTableView()
        main_layout.addWidget(self.terms_table)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.add_term_button.clicked.connect(self.add_term)
        self.clear_form_button.clicked.connect(self.clear_form)
    
    def add_term(self):
        """Handle adding a new term"""
        # Placeholder implementation
        QMessageBox.information(self, "Add Term", "Term add functionality not yet implemented")
    
    def clear_form(self):
        """Clear the input form"""
        self.term_name_input.clear()
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDate(QDate.currentDate().addMonths(3))
