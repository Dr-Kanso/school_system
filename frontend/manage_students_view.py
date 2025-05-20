from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QFormLayout, QLineEdit, QMessageBox, QComboBox,
    QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont
from utils.firebase_client import FirebaseClient
import uuid

class StudentTableModel(QAbstractTableModel):
    """Table model for students"""
    
    def __init__(self, students=None):
        super().__init__()
        self.students = students or []
        self.headers = ["ID", "Name", "Year Group", "Subjects"]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.students)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        student = self.students[index.row()]
        col = index.column()
        
        if col == 0:
            return student.get('id', '')
        elif col == 1:
            # Display full name by combining first_name and last_name
            first_name = student.get('first_name', '')
            last_name = student.get('last_name', '')
            
            # If either first_name or last_name exists, use them
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()
            
            # Fallback to old 'name' field for backward compatibility
            return student.get('name', '')
        elif col == 2:
            return student.get('year_group', '')
        elif col == 3:
            subjects = student.get('subjects', [])
            if isinstance(subjects, list):
                return ", ".join(subjects)
            return str(subjects)
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def update_students(self, students):
        self.beginResetModel()
        self.students = students
        self.endResetModel()
    
    def sort(self, column, order):
        """Sort table by given column number and order"""
        self.beginResetModel()
        
        # Define sort key functions based on column
        if column == 0:  # ID
            self.students = sorted(self.students, key=lambda x: x.get('id', ''), 
                                 reverse=(order == Qt.DescendingOrder))
        elif column == 1:  # Name
            self.students = sorted(self.students, key=lambda x: (x.get('first_name', '').lower(), x.get('last_name', '').lower()), 
                                 reverse=(order == Qt.DescendingOrder))
        elif column == 2:  # Year Group
            self.students = sorted(self.students, key=lambda x: x.get('year_group', ''), 
                                 reverse=(order == Qt.DescendingOrder))
        elif column == 3:  # Subjects
            self.students = sorted(self.students, 
                                 key=lambda x: ", ".join(x.get('subjects', [])) if isinstance(x.get('subjects', []), list) else str(x.get('subjects', [])), 
                                 reverse=(order == Qt.DescendingOrder))
        
        self.endResetModel()

class ManageStudentsView(QWidget):
    """View for managing student records"""
    
    def __init__(self, id_token, user_uid):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.all_students = []  # Store all students for filtering
        self.setup_ui()
        self.load_students()
    
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
        
        # Filter by Year Group
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Year Group:"))
        self.year_filter_dropdown = QComboBox()
        self.year_filter_dropdown.addItem("All")
        self.year_filter_dropdown.addItems(["Y7", "Y8", "Y9", "Y10", "Y11"])
        self.year_filter_dropdown.currentTextChanged.connect(self.filter_students)
        filter_layout.addWidget(self.year_filter_dropdown)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # Student input form
        form_layout = QFormLayout()
        
        # Replace single name field with first and last name fields
        self.first_name_input = QLineEdit()
        form_layout.addRow("First Name:", self.first_name_input)
        
        self.last_name_input = QLineEdit()
        form_layout.addRow("Last Name:", self.last_name_input)
        
        self.year_group_dropdown = QComboBox()
        self.year_group_dropdown.addItems(["Y7", "Y8", "Y9", "Y10", "Y11"])
        form_layout.addRow("Year Group:", self.year_group_dropdown)
        
        # Add subject selection
        subjects_group = QGroupBox("Subjects")
        subjects_layout = QVBoxLayout()
        
        self.subject_checkboxes = {}
        for subject in ["Maths", "English", "Science", "French"]:
            checkbox = QCheckBox(subject)
            self.subject_checkboxes[subject] = checkbox
            subjects_layout.addWidget(checkbox)
        
        subjects_group.setLayout(subjects_layout)
        form_layout.addRow("", subjects_group)
        
        button_layout = QHBoxLayout()
        self.add_student_button = QPushButton("Add Student")
        self.clear_form_button = QPushButton("Clear")
        
        button_layout.addWidget(self.add_student_button)
        button_layout.addWidget(self.clear_form_button)
        
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        
        # Students table
        self.students_table = QTableView()
        self.student_model = StudentTableModel()
        
        # Set up proxy model for sorting
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.student_model)
        self.students_table.setModel(self.proxy_model)
        
        # Enable sorting
        self.students_table.setSortingEnabled(True)
        self.students_table.horizontalHeader().setSectionsClickable(True)
        self.students_table.horizontalHeader().setStyleSheet("::section { background-color: #f0f0f0; }")
        
        main_layout.addWidget(self.students_table)
        
        # Delete student button
        self.delete_student_button = QPushButton("Delete Selected Student")
        main_layout.addWidget(self.delete_student_button)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.add_student_button.clicked.connect(self.add_student)
        self.clear_form_button.clicked.connect(self.clear_form)
        self.delete_student_button.clicked.connect(self.delete_student)
    
    def load_students(self):
        """Load students from Firebase"""
        try:
            students = self.firebase.get_collection("students")
            self.all_students = students  # Store all students
            
            # Apply current filter
            self.filter_students(self.year_filter_dropdown.currentText())
            
            # Adjust column widths
            self.students_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load students: {str(e)}")
    
    def filter_students(self, year_group):
        """Filter students by year group"""
        if year_group == "All":
            self.student_model.update_students(self.all_students)
        else:
            filtered_students = [s for s in self.all_students if s.get('year_group') == year_group]
            self.student_model.update_students(filtered_students)
        
        # Preserve sorting if already sorted
        if self.students_table.horizontalHeader().sortIndicatorSection() >= 0:
            section = self.students_table.horizontalHeader().sortIndicatorSection()
            order = self.students_table.horizontalHeader().sortIndicatorOrder()
            self.students_table.sortByColumn(section, order)
    
    def add_student(self):
        """Handle adding a new student"""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        year_group = self.year_group_dropdown.currentText()
        
        # Get selected subjects
        selected_subjects = []
        for subject, checkbox in self.subject_checkboxes.items():
            if checkbox.isChecked():
                selected_subjects.append(subject)
        
        if not first_name:
            QMessageBox.warning(self, "Input Error", "Please enter a first name.")
            return
        
        if not last_name:
            QMessageBox.warning(self, "Input Error", "Please enter a last name.")
            return
        
        if not selected_subjects:
            QMessageBox.warning(self, "Input Error", "Please select at least one subject.")
            return
        
        try:
            # Generate a unique student ID
            student_id = str(uuid.uuid4())
            
            # Create the student in Firebase with first_name and last_name
            student_data = {
                "first_name": first_name,
                "last_name": last_name,
                "year_group": year_group,
                "subjects": selected_subjects
            }
            
            self.firebase.create_document("students", student_id, student_data)
            
            # Refresh the students list
            self.load_students()
            
            # Only clear the name fields, keep subject selections
            self.first_name_input.clear()
            self.last_name_input.clear()
            
            QMessageBox.information(self, "Success", "Student added successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add student: {str(e)}")
    
    def delete_student(self):
        """Delete the selected student"""
        selected_indexes = self.students_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a student to delete.")
            return
        
        # Get the source model index from proxy model
        source_row = self.proxy_model.mapToSource(selected_indexes[0]).row()
        student = self.student_model.students[source_row]
        student_id = student.get('id', '')
        
        if not student_id:
            return
        
        # Build student name from first_name and last_name if available
        first_name = student.get('first_name', '')
        last_name = student.get('last_name', '')
        
        if first_name or last_name:
            student_name = f"{first_name} {last_name}".strip()
        else:
            # Fallback to old name field
            student_name = student.get('name', '')
            
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete student '{student_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        try:
            # Delete the student using the REST API
            url = f"{self.firebase.base_url}/students/{student_id}?key={self.firebase.api_key}"
            headers = {}
            if self.firebase.id_token:
                headers["Authorization"] = f"Bearer {self.firebase.id_token}"
            
            import requests
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            # Refresh the students list
            self.load_students()
            
            QMessageBox.information(self, "Success", "Student deleted successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete student: {str(e)}")
    
    def clear_form(self):
        """Clear the input form"""
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.year_group_dropdown.setCurrentIndex(0)
        for checkbox in self.subject_checkboxes.values():
            checkbox.setChecked(False)
