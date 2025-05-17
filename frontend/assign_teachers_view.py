from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QMessageBox,
    QCheckBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from utils.firebase_client import FirebaseClient
import uuid

class TeacherAssignmentTableModel(QAbstractTableModel):
    """Table model for teacher assignments"""
    
    def __init__(self, assignments=None):
        super().__init__()
        self.assignments = assignments or []
        self.headers = ["Teacher", "Year Groups", "Subject", "Assignment ID"]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.assignments)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        assignment = self.assignments[index.row()]
        col = index.column()
        
        if col == 0:
            return assignment.get('teacher_name', '')
        elif col == 1:
            year_groups = assignment.get('year_groups', [])
            return ", ".join(year_groups) if year_groups else "None"
        elif col == 2:
            return assignment.get('subject', '')
        elif col == 3:
            return assignment.get('id', '')
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def update_assignments(self, assignments):
        self.beginResetModel()
        self.assignments = assignments
        self.endResetModel()

class AssignTeachersView(QWidget):
    """View for assigning teachers to year groups and subjects"""
    
    def __init__(self, id_token, user_uid):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.teachers = []
        self.year_groups = ["Y7", "Y8", "Y9", "Y10", "Y11"]
        self.subjects = ["Maths", "English", "Science", "French"]
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Assign Teachers")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Assignment input form
        form_layout = QFormLayout()
        
        self.teacher_dropdown = QComboBox()
        self.teacher_dropdown.addItem("Select Teacher...")
        form_layout.addRow("Teacher:", self.teacher_dropdown)
        
        # Year group selection with checkboxes
        year_group_group = QGroupBox("Year Groups")
        year_group_layout = QGridLayout()
        
        self.year_group_checkboxes = {}
        for i, year_group in enumerate(self.year_groups):
            checkbox = QCheckBox(year_group)
            self.year_group_checkboxes[year_group] = checkbox
            # Arrange in a 3x2 grid
            row = i // 3
            col = i % 3
            year_group_layout.addWidget(checkbox, row, col)
        
        year_group_group.setLayout(year_group_layout)
        form_layout.addRow("", year_group_group)
        
        self.subject_dropdown = QComboBox()
        self.subject_dropdown.addItem("Select Subject...")
        self.subject_dropdown.addItems(self.subjects)
        form_layout.addRow("Subject:", self.subject_dropdown)
        
        button_layout = QHBoxLayout()
        self.assign_button = QPushButton("Assign Teacher")
        self.clear_form_button = QPushButton("Clear")
        
        button_layout.addWidget(self.assign_button)
        button_layout.addWidget(self.clear_form_button)
        
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        
        # Assignments table
        self.assignments_table = QTableView()
        self.assignment_model = TeacherAssignmentTableModel()
        self.assignments_table.setModel(self.assignment_model)
        main_layout.addWidget(self.assignments_table)
        
        # Delete assignment button
        self.delete_assignment_button = QPushButton("Delete Selected Assignment")
        main_layout.addWidget(self.delete_assignment_button)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.assign_button.clicked.connect(self.assign_teacher)
        self.clear_form_button.clicked.connect(self.clear_form)
        self.delete_assignment_button.clicked.connect(self.delete_assignment)
    
    def load_data(self):
        """Load teachers and assignments from Firebase"""
        self.load_teachers()
        self.load_assignments()
    
    def load_teachers(self):
        """Load teachers from Firebase"""
        try:
            teachers = self.firebase.query_collection("users", "role", "==", "teacher")
            
            # Clear and add to dropdown
            self.teacher_dropdown.clear()
            self.teacher_dropdown.addItem("Select Teacher...")
            
            # Store the full teacher data
            self.teachers = teachers
            
            for teacher in teachers:
                # Add name and ID to dropdown
                self.teacher_dropdown.addItem(teacher.get('name', ''), teacher.get('id', ''))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load teachers: {str(e)}")
    
    def load_assignments(self):
        """Load teacher assignments from Firebase"""
        try:
            assignments = self.firebase.get_collection("teacher_assignments")
            
            # Add teacher names for display
            for assignment in assignments:
                teacher_id = assignment.get('teacher_id', '')
                
                # Find teacher name
                for teacher in self.teachers:
                    if teacher.get('id') == teacher_id:
                        assignment['teacher_name'] = teacher.get('name', '')
                        break
                else:
                    assignment['teacher_name'] = f"Unknown ({teacher_id})"
            
            # Update the table model
            self.assignment_model.update_assignments(assignments)
            
            # Adjust column widths
            self.assignments_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load assignments: {str(e)}")
    
    def assign_teacher(self):
        """Handle assigning a teacher to year groups and subject"""
        teacher_id = self.teacher_dropdown.currentData()
        selected_year_groups = [yg for yg, cb in self.year_group_checkboxes.items() if cb.isChecked()]
        subject = self.subject_dropdown.currentText()
        
        if not teacher_id or teacher_id == "Select Teacher...":
            QMessageBox.warning(self, "Input Error", "Please select a teacher.")
            return
        
        if not selected_year_groups:
            QMessageBox.warning(self, "Input Error", "Please select at least one year group.")
            return
        
        if subject == "Select Subject...":
            QMessageBox.warning(self, "Input Error", "Please select a subject.")
            return
        
        try:
            # Check for existing assignment to avoid duplicates
            existing_assignments = self.firebase.query_collection("teacher_assignments", "teacher_id", "==", teacher_id)
            for assignment in existing_assignments:
                if assignment.get("subject") == subject:
                    # Compare year groups
                    existing_year_groups = assignment.get("year_groups", [])
                    # Check if any year group already assigned
                    overlap = [yg for yg in selected_year_groups if yg in existing_year_groups]
                    if overlap:
                        QMessageBox.warning(
                            self, 
                            "Duplicate Assignment", 
                            f"This teacher is already assigned to {subject} for year group(s): {', '.join(overlap)}"
                        )
                        return
            
            # Generate a unique assignment ID
            assignment_id = str(uuid.uuid4())
            
            # Create the assignment in Firebase
            assignment_data = {
                "teacher_id": teacher_id,
                "year_groups": selected_year_groups,
                "subject": subject
            }
            
            self.firebase.create_document("teacher_assignments", assignment_id, assignment_data)
            
            # Refresh the assignments list
            self.load_data()
            
            # Clear the form
            self.clear_form()
            
            QMessageBox.information(self, "Success", "Teacher assigned successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to assign teacher: {str(e)}")
    
    def delete_assignment(self):
        """Delete the selected assignment"""
        selected_indexes = self.assignments_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select an assignment to delete.")
            return
        
        # Get the assignment ID from the selected row
        row = selected_indexes[0].row()
        assignment_id = self.assignment_model.assignments[row].get('id', '')
        
        if not assignment_id:
            return
        
        # Confirm deletion
        teacher_name = self.assignment_model.assignments[row].get('teacher_name', '')
        year_groups = self.assignment_model.assignments[row].get('year_groups', [])
        year_groups_str = ", ".join(year_groups) if year_groups else "None"
        subject = self.assignment_model.assignments[row].get('subject', '')
        
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the assignment of {teacher_name} to {year_groups_str} for {subject}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        try:
            # Delete the assignment using the REST API
            url = f"{self.firebase.base_url}/teacher_assignments/{assignment_id}?key={self.firebase.api_key}"
            headers = {}
            if self.firebase.id_token:
                headers["Authorization"] = f"Bearer {self.firebase.id_token}"
            
            import requests
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            # Refresh the assignments list
            self.load_data()
            
            QMessageBox.information(self, "Success", "Assignment deleted successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete assignment: {str(e)}")
    
    def clear_form(self):
        """Clear the input form"""
        self.teacher_dropdown.setCurrentIndex(0)
        self.subject_dropdown.setCurrentIndex(0)
        
        # Uncheck all year group checkboxes
        for checkbox in self.year_group_checkboxes.values():
            checkbox.setChecked(False)
