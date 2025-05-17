from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QFormLayout, QLineEdit, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from utils.firebase_client import FirebaseClient
from datetime import datetime
import uuid

class TermTableModel(QAbstractTableModel):
    """Table model for academic terms"""
    
    def __init__(self, terms=None):
        super().__init__()
        self.terms = terms or []
        self.headers = ["ID", "Name", "Start Date", "End Date"]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.terms)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        term = self.terms[index.row()]
        col = index.column()
        
        if col == 0:
            return term.get('id', '')
        elif col == 1:
            return term.get('name', '')
        elif col == 2:
            return term.get('start_date', '')
        elif col == 3:
            return term.get('end_date', '')
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def update_terms(self, terms):
        self.beginResetModel()
        self.terms = terms
        self.endResetModel()

class TermManagementView(QWidget):
    """View for managing academic terms"""
    
    def __init__(self, id_token, user_uid):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.setup_ui()
        self.load_terms()
    
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
        self.term_model = TermTableModel()
        self.terms_table.setModel(self.term_model)
        main_layout.addWidget(self.terms_table)
        
        # Delete term button
        self.delete_term_button = QPushButton("Delete Selected Term")
        main_layout.addWidget(self.delete_term_button)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.add_term_button.clicked.connect(self.add_term)
        self.clear_form_button.clicked.connect(self.clear_form)
        self.delete_term_button.clicked.connect(self.delete_term)
    
    def load_terms(self):
        """Load terms from Firebase"""
        try:
            terms = self.firebase.get_collection("terms")
            self.term_model.update_terms(terms)
            # Adjust column widths
            self.terms_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load terms: {str(e)}")
    
    def add_term(self):
        """Handle adding a new term"""
        name = self.term_name_input.text().strip()
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a term name.")
            return
        
        if self.start_date_input.date() >= self.end_date_input.date():
            QMessageBox.warning(self, "Date Error", "End date must be after start date.")
            return
        
        try:
            # Generate a unique term ID
            term_id = str(uuid.uuid4())
            
            # Create the term in Firebase
            term_data = {
                "name": name,
                "start_date": start_date,
                "end_date": end_date
            }
            
            self.firebase.create_document("terms", term_id, term_data)
            
            # Refresh the terms list
            self.load_terms()
            
            # Clear the form
            self.clear_form()
            
            QMessageBox.information(self, "Success", "Term added successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add term: {str(e)}")
    
    def delete_term(self):
        """Delete the selected term"""
        selected_indexes = self.terms_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a term to delete.")
            return
        
        # Get the term ID from the first column of the selected row
        row = selected_indexes[0].row()
        term_id = self.term_model.terms[row].get('id', '')
        
        if not term_id:
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete term '{self.term_model.terms[row].get('name', '')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        try:
            # Delete the term using the REST API
            url = f"{self.firebase.base_url}/terms/{term_id}?key={self.firebase.api_key}"
            headers = {}
            if self.firebase.id_token:
                headers["Authorization"] = f"Bearer {self.firebase.id_token}"
            
            import requests
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            # Refresh the terms list
            self.load_terms()
            
            QMessageBox.information(self, "Success", "Term deleted successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete term: {str(e)}")
    
    def clear_form(self):
        """Clear the input form"""
        self.term_name_input.clear()
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDate(QDate.currentDate().addMonths(3))
