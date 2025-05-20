from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QComboBox, QMessageBox, QFormLayout, QSpinBox,
    QGridLayout, QGroupBox, QHeaderView, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from utils.firebase_client import FirebaseClient

class GradeDelegate(QStyledItemDelegate):
    """Delegate for grade columns in results table to provide dropdowns"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grades = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    
    def createEditor(self, parent, option, index):
        """Create dropdown editor for grade columns"""
        if index.column() >= 3 and index.column() <= 7:  # All grade columns
            editor = QComboBox(parent)
            editor.addItems(self.grades)
            return editor
        return super().createEditor(parent, option, index)
    
    def setEditorData(self, editor, index):
        """Set the editor data based on the model"""
        if index.column() >= 3 and index.column() <= 7 and isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.DisplayRole)
            if value in self.grades:
                idx = self.grades.index(value)
                editor.setCurrentIndex(idx)
            else:
                editor.setCurrentIndex(0)
        else:
            super().setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        """Update the model with data from the editor"""
        if index.column() >= 3 and index.column() <= 7 and isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)

class ResultsTableModel(QAbstractTableModel):
    """Table model for student results"""
    
    def __init__(self, students=None):
        super().__init__()
        self.students = students or []
        self.headers = ["ID", "Name", "Year Group", "Current Grade", "Target Grade", "Homework", "Behaviour", "Punctuality"]
        self.grades = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]  # Numeric grades
        
        # Clear all previous results to avoid data from previous subjects interfering
        self.results = {}
        
        # Initialize default grade of "1" for every student for all categories
        categories = ["current_grade", "target_grade", "homework", "behaviour", "punctuality"]
        for student in self.students:
            student_id = student.get('id', '')
            if student_id:
                self.results[student_id] = {category: "1" for category in categories}
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.students)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()
        student = self.students[row]
        
        if role == Qt.DisplayRole:
            if col == 0:
                return student.get('id', '')
            elif col == 1:
                # Build student name from first_name and last_name if available
                first_name = student.get('first_name', '')
                last_name = student.get('last_name', '')
                
                if first_name or last_name:
                    return f"{first_name} {last_name}".strip()
                else:
                    # Fallback to old name field
                    return student.get('name', '')
            elif col == 2:
                return student.get('year_group', '')
            elif col >= 3 and col <= 7:  # Grade columns
                student_id = student.get('id', '')
                if student_id in self.results:
                    category = self._get_category_for_column(col)
                    return self.results[student_id].get(category, "1")
                return "1"  # Default grade
                
        # Store student ID in user role for reference
        if role == Qt.UserRole:
            return student.get('id', '')
            
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or index.column() < 3 or index.column() > 7:
            return False
            
        if role == Qt.EditRole:
            student_id = self.students[index.row()].get('id', '')
            category = self._get_category_for_column(index.column())
            
            # Initialize student record if it doesn't exist
            if student_id not in self.results:
                self.results[student_id] = {}
                
            # Set the value for the specific category
            self.results[student_id][category] = value
            self.dataChanged.emit(index, index)
            return True
            
        return False
    
    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
            
        # Make only the grade columns editable
        if index.column() >= 3 and index.column() <= 7:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
            
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def update_students(self, students):
        """Update the model with student data and set default grade of 1"""
        self.beginResetModel()
        self.students = students
        
        # Clear all previous results to avoid data from previous subjects interfering
        self.results = {}
        
        # Initialize default grade of "1" for every student for all categories
        categories = ["current_grade", "target_grade", "homework", "behaviour", "punctuality"]
        for student in self.students:
            student_id = student.get('id', '')
            if student_id:
                self.results[student_id] = {category: "1" for category in categories}
                
        self.endResetModel()
    
    def set_existing_results(self, results_data):
        """Load existing results data and reset missing grades to 1"""
        # Initialize with defaults for all students
        categories = ["current_grade", "target_grade", "homework", "behaviour", "punctuality"]
        self.results = {}
        
        for student in self.students:
            student_id = student.get('id', '')
            if student_id:
                # Initialize with default grades
                self.results[student_id] = {category: "1" for category in categories}
                
                # Update with existing data if available
                if student_id in results_data:
                    student_results = results_data[student_id]
                    # Handle both the old format (string) and new format (dict)
                    if isinstance(student_results, str):
                        # Legacy format - just the achievement/current_grade
                        self.results[student_id]["current_grade"] = student_results
                    elif isinstance(student_results, dict):
                        # New format - copy all available categories
                        # Handle legacy category names
                        if "achievement" in student_results:
                            self.results[student_id]["current_grade"] = student_results["achievement"]
                        if "target" in student_results:
                            self.results[student_id]["target_grade"] = student_results["target"]
                        
                        # Also handle current naming if present
                        for category in categories:
                            if category in student_results:
                                self.results[student_id][category] = student_results[category]
                
        self.dataChanged.emit(
            self.index(0, 3), 
            self.index(self.rowCount()-1, 7)
        )
    
    def get_results(self):
        """Return the current results dictionary"""
        return self.results
    
    def _get_category_for_column(self, column):
        """Map column index to category name"""
        if column == 3:
            return "current_grade"  # Changed from "achievement"
        elif column == 4:
            return "target_grade"   # Changed from "target"
        elif column == 5:
            return "homework"
        elif column == 6:
            return "behaviour"
        elif column == 7:
            return "punctuality"
        return None

class InputResultsView(QWidget):
    """View for inputting student results"""
    
    def __init__(self, id_token, user_uid):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.teacher_assignments = []  # Store teacher's subject assignments
        self.standard_year_groups = ["Y7", "Y8", "Y9", "Y10", "Y11"]  # Standard year groups matching student management
        self.terms = []  # Store available terms
        self.setup_ui()
        self.loadTeacherAssignments()
        self.loadTerms()  # Load terms from Firebase
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Input Student Results")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Selection controls - now using a GroupBox like in attendance register
        class_group = QGroupBox("Class Information")
        class_layout = QGridLayout()
        
        # Subject selection
        subject_label = QLabel("Subject:")
        self.subject_selector = QComboBox()
        
        # Year group selection
        year_label = QLabel("Year Group:")
        self.year_group_selector = QComboBox()
        
        # Term selection (formerly assessment)
        term_label = QLabel("Term:")
        self.term_dropdown = QComboBox()
        # We'll populate this from the database instead of hardcoding
        
        # Add widgets to grid layout
        class_layout.addWidget(subject_label, 0, 0)
        class_layout.addWidget(self.subject_selector, 0, 1)
        class_layout.addWidget(year_label, 0, 2)
        class_layout.addWidget(self.year_group_selector, 0, 3)
        class_layout.addWidget(term_label, 1, 0)
        class_layout.addWidget(self.term_dropdown, 1, 1)
        
        class_group.setLayout(class_layout)
        main_layout.addWidget(class_group)
        
        # Load students button
        self.load_button = QPushButton("Load Students")
        self.load_button.clicked.connect(self.load_students)
        main_layout.addWidget(self.load_button)
        
        # Results table
        self.results_table = QTableView()
        self.results_model = ResultsTableModel()
        self.results_table.setModel(self.results_model)
        
        # Set up table view properties
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableView.SelectRows)
        
        # Add the grade delegate for all grade columns
        grade_delegate = GradeDelegate(self.results_table)
        for col in range(3, 8):  # Columns 3-7 are grade columns
            self.results_table.setItemDelegateForColumn(col, grade_delegate)
        
        # Make the table wider to accommodate more columns
        self.results_table.setMinimumWidth(800)
        
        main_layout.addWidget(self.results_table)
        
        # Save button
        self.save_button = QPushButton("Save Results")
        self.save_button.clicked.connect(self.save_results)
        main_layout.addWidget(self.save_button)
        
        self.setLayout(main_layout)
        
        # Connect signals for subject, year group, and term changes
        self.subject_selector.currentTextChanged.connect(self.onSubjectChanged)
        self.year_group_selector.currentTextChanged.connect(self.onYearGroupChanged)
        self.term_dropdown.currentIndexChanged.connect(self.onTermChanged)
    
    def loadTerms(self):
        """Load academic terms from Firebase"""
        try:
            # Get terms from Firebase
            self.terms = self.firebase.get_collection("terms")
            print(f"Loaded {len(self.terms)} terms from database")
            
            # Clear and populate the dropdown
            self.term_dropdown.clear()
            self.term_dropdown.addItem("-- Select Term --", "")
            
            # Sort terms by year (recent first)
            sorted_terms = sorted(self.terms, key=lambda x: (x.get('year', ''), x.get('name', '')), reverse=True)
            
            # Add each term to the dropdown
            for term in sorted_terms:
                term_id = term.get('id', '')
                term_name = term.get('name', '')
                term_year = term.get('year', '')
                display_text = f"{term_name} {term_year}"
                self.term_dropdown.addItem(display_text, term_id)
                
            # Auto-select the first term if available
            if self.term_dropdown.count() > 1:
                self.term_dropdown.setCurrentIndex(1)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load terms: {str(e)}")
            print(f"Exception in loadTerms: {str(e)}")
    
    def loadTeacherAssignments(self):
        """Load the subjects and year groups assigned to this teacher"""
        try:
            # Debug message to verify user_uid
            print(f"Loading assignments for teacher ID: {self.user_uid}")
            
            # Use query_collection_with_filters to get assignments
            teacher_assignments = self.firebase.query_collection_with_filters(
                "teacher_assignments", 
                [("teacher_id", "==", self.user_uid)]
            )
            
            # Debug - print found assignments
            print(f"Found {len(teacher_assignments)} assignments for the teacher")
            for i, assignment in enumerate(teacher_assignments):
                print(f"Assignment {i+1}:")
                print(f"  Subject: {assignment.get('subject')}")
                print(f"  Year Groups (raw): {assignment.get('year_groups')}")
                print(f"  Year Groups (type): {type(assignment.get('year_groups'))}")
            
            self.teacher_assignments = teacher_assignments
            
            # Update the subject selector
            self.updateSubjectSelector()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load teacher assignments: {str(e)}")
            print(f"Exception in loadTeacherAssignments: {str(e)}")
    
    def updateSubjectSelector(self):
        """Update subject selector with teacher's assigned subjects"""
        self.subject_selector.clear()
        
        # Add a default prompt
        self.subject_selector.addItem("-- Select a subject --", "")
        
        # Get unique subjects from teacher's assignments
        unique_subjects = set()
        for assignment in self.teacher_assignments:
            subject = assignment.get("subject")
            if subject:
                unique_subjects.add(subject)
                
        # Add subjects to the dropdown
        for subject in sorted(unique_subjects):
            self.subject_selector.addItem(subject, subject)
    
    def updateYearGroupSelector(self, subject):
        """Update year group selector based on selected subject"""
        self.year_group_selector.clear()
        
        # Add a default prompt
        self.year_group_selector.addItem("-- Select Year Group --", "")
        
        # Find all year groups for this subject in teacher's assignments
        assigned_year_groups = set()
        print(f"\nUpdating year groups for subject: '{subject}'")
        
        for assignment in self.teacher_assignments:
            print(f"Checking assignment with subject: '{assignment.get('subject')}'")
            
            # Check subject match with case insensitive comparison
            if assignment.get("subject", "").lower() == subject.lower():
                print(f"  Subject match found!")
                # Get year_groups from assignment and ensure consistent format
                year_groups = assignment.get("year_groups", [])
                print(f"  Raw year_groups: {year_groups} (type: {type(year_groups)})")
                
                # Handle different possible formats of year_groups
                if isinstance(year_groups, str):
                    try:
                        import ast
                        year_groups = ast.literal_eval(year_groups)
                        print(f"  Parsed from string: {year_groups}")
                    except Exception as e:
                        print(f"  Failed to parse year_groups string: {e}")
                        year_groups = [year_groups]
                elif not isinstance(year_groups, list):
                    year_groups = [str(year_groups)]
                
                print(f"  Processed year_groups: {year_groups}")
                
                # Add to our set of assigned year groups (standardized format)
                for year_group in year_groups:
                    year_group_str = str(year_group).strip().upper()
                    # Only add if it's a valid standard year group
                    if year_group_str in self.standard_year_groups:
                        assigned_year_groups.add(year_group_str)
                        print(f"  Added year group: {year_group_str}")
                    else:
                        print(f"  Skipped invalid year group: {year_group_str}")
                        
        print(f"Final assigned year groups: {assigned_year_groups}")
        
        # Add all assigned year groups to dropdown in standard order
        for year_group in self.standard_year_groups:
            if year_group in assigned_year_groups:
                self.year_group_selector.addItem(year_group, year_group)
    
    def onSubjectChanged(self, subject):
        """Handle subject selection change"""
        if self.subject_selector.currentData():
            # Update year group selector for this subject
            self.updateYearGroupSelector(subject)
            # Clear any previously loaded students
            self.results_model.update_students([])
            
            # Try to load students immediately if a year group is already selected
            if self.year_group_selector.currentData() and self.term_dropdown.currentData():
                self.load_students(auto_triggered=True)

    def onYearGroupChanged(self, year_group):
        """Handle year group selection change"""
        # If a year group is selected and a subject is selected, load students
        if (self.year_group_selector.currentData() and self.subject_selector.currentData() 
            and self.term_dropdown.currentData()):
            self.load_students(auto_triggered=True)

    def onTermChanged(self, index):
        """Handle term selection change"""
        # Skip if no valid selection or if required fields aren't selected
        if index <= 0 or not self.subject_selector.currentData() or not self.year_group_selector.currentData():
            return
            
        subject = self.subject_selector.currentData()
        year_group = self.year_group_selector.currentData()
        term_id = self.term_dropdown.currentData()
        term_name = self.term_dropdown.currentText()
        
        # Check if results already exist for this combination
        existing_results = self.check_existing_results(subject, year_group, term_id)
        
        if existing_results:
            # Inform user that results exist and will be loaded
            QMessageBox.information(
                self,
                "Existing Results Found",
                f"Results have already been saved for {subject} {year_group} in {term_name}. "
                "These will be loaded for viewing or updating."
            )
            
            # Update the model with the existing results
            if self.results_model.students:
                self.results_model.set_existing_results(existing_results)
        else:
            # Reset all grades to "1" since no existing results
            self.results_model.results = {}  # Clear any existing results
            
            # Initialize with default grade "1" for each student
            for student in self.results_model.students:
                student_id = student.get('id', '')
                if student_id:
                    self.results_model.results[student_id] = {
                        category: "1" for category in [
                            "current_grade", "target_grade", "homework", "behaviour", "punctuality"
                        ]
                    }
                    
            # Refresh the table display
            if self.results_model.students:
                self.results_model.dataChanged.emit(
                    self.results_model.index(0, 3),
                    self.results_model.index(self.results_model.rowCount()-1, 7)
                )
    
    def check_existing_results(self, subject, year_group, term_id):
        """Check if results exist for the given subject, year group and term"""
        if not subject or not year_group or not term_id:
            return None
            
        try:
            # Format a document ID for results using the same format as in save_results
            results_doc_id = f"{term_id}_{year_group}_{subject}"
            results_data = self.firebase.get_document("results", results_doc_id)
            
            if results_data and "student_results" in results_data:
                return results_data["student_results"]
                
        except Exception as e:
            print(f"Error checking existing results: {str(e)}")
            
        return None
    
    def load_students(self, auto_triggered=False):
        """Handle loading students for selected subject and year group"""
        subject = self.subject_selector.currentData()
        year_group = self.year_group_selector.currentData()
        
        if not subject or subject == "":
            if not auto_triggered:  # Only show warnings when user explicitly clicks the button
                QMessageBox.warning(self, "Selection Error", "Please select a subject.")
            return
            
        if not year_group or year_group == "":
            if not auto_triggered:  # Only show warnings when user explicitly clicks the button
                QMessageBox.warning(self, "Selection Error", "Please select a year group.")
            return
            
        # Note: term is not required for loading students, only for saving results
        term_id = self.term_dropdown.currentData()
        term_display = self.term_dropdown.currentText()
        
        try:
            # Standardize year group format for querying
            standardized_year_group = year_group.strip().upper()
            if standardized_year_group not in self.standard_year_groups:
                print(f"Invalid year group format: {year_group}")
                return
                
            students = self.firebase.query_collection_with_filters(
                "students", 
                [("year_group", "==", standardized_year_group)]
            )
            
            if not students:
                print(f"No students found for year group: {year_group}")
                if not auto_triggered:
                    QMessageBox.information(self, "No Students", f"No students found for year group {year_group}")
                return
                
            print(f"Found {len(students)} students for year group {year_group}")
            
            # Filter students by subject
            filtered_students = []
            for student in students:
                student_subjects = student.get("subjects", [])
                
                # Enhanced handling of different subject formats
                clean_subjects = []
                
                # Case 1: It's already a clean list of strings
                if isinstance(student_subjects, list):
                    clean_subjects = [str(s).strip() for s in student_subjects]
                    
                # Case 2: It's a string representation of a list
                elif isinstance(student_subjects, str):
                    # Check if it looks like a Python list representation
                    if student_subjects.startswith('[') and student_subjects.endswith(']'):
                        try:
                            import ast
                            # Use ast.literal_eval to safely parse the string to a list
                            parsed_subjects = ast.literal_eval(student_subjects)
                            if isinstance(parsed_subjects, list):
                                clean_subjects = [str(s).strip() for s in parsed_subjects]
                            else:
                                clean_subjects = [student_subjects.strip()]
                        except Exception as e:
                            print(f"Error parsing subjects: {e}")
                            # If parsing fails, treat as a single string
                            clean_subjects = [s.strip() for s in student_subjects.split(",")]
                    else:
                        # It's a regular comma-separated string
                        clean_subjects = [s.strip() for s in student_subjects.split(",")]
                
                # Case-insensitive comparison with clean subjects
                if any(s.lower() == subject.lower() for s in clean_subjects):
                    filtered_students.append(student)
            
            print(f"After filtering: {len(filtered_students)} students taking {subject}")
            
            if not filtered_students:
                if not auto_triggered:
                    QMessageBox.information(self, "No Students", f"No students found in {year_group} taking {subject}")
                return
                
            # Check for existing results using our helper method
            existing_results = self.check_existing_results(subject, year_group, term_id)
            
            # Update the results model with the filtered students
            self.results_model.update_students(filtered_students)
            
            # Load existing results if available
            if existing_results:
                self.results_model.set_existing_results(existing_results)
                # Inform the user we're loading saved results, but only if not auto-triggered
                if not auto_triggered:
                    QMessageBox.information(
                        self, 
                        "Existing Results Loaded", 
                        f"Previously saved results for {subject}, {year_group} in {term_display} have been loaded."
                    )
            else:
                # Otherwise, the update_students method will have set default grade "1"
                if not auto_triggered:  # Only show message when explicitly clicked
                    QMessageBox.information(
                        self, 
                        "Students Loaded", 
                        f"Loaded {len(filtered_students)} students for {subject}, {year_group}.\n\n"
                        f"No existing results found for {term_display if term_id else 'the selected term'}.\n\n"
                        "Default grades of '1' have been applied. Adjust as needed and save."
                    )
            
        except Exception as e:
            if not auto_triggered:  # Only show errors for explicit user actions
                QMessageBox.warning(self, "Error", f"Failed to load students: {str(e)}")
            print(f"Exception in load_students: {str(e)}, type: {type(e)}")
    
    def save_results(self):
        """Handle saving student results"""
        subject = self.subject_selector.currentData()
        year_group = self.year_group_selector.currentData()
        term_id = self.term_dropdown.currentData()
        term_display = self.term_dropdown.currentText()
        
        # Input validation
        if not subject or not year_group or not term_id:
            QMessageBox.warning(self, "Selection Error", "Please select subject, year group and term.")
            return
        
        # Get results from the model
        results_data = self.results_model.get_results()
        
        if not results_data:
            QMessageBox.warning(self, "No Results", "No grades have been entered yet.")
            return
            
        try:
            # Format a document ID for results - using a consistent format for easy retrieval
            results_doc_id = f"{term_id}_{year_group}_{subject}"
            
            # Prepare data to save
            data_to_save = {
                "term_id": term_id,
                "year_group": year_group,
                "subject": subject,
                "teacher_id": self.user_uid,
                "student_results": results_data,
                "timestamp": self.firebase.get_server_timestamp(),
                "term_name": self.term_dropdown.currentText()
            }
            
            # Save to Firebase
            self.firebase.create_document("results", results_doc_id, data_to_save)
            
            # Show success message with details
            QMessageBox.information(
                self, 
                "Success", 
                f"Grades saved successfully!\n\nSubject: {subject}\nYear Group: {year_group}\nTerm: {term_display}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save results: {str(e)}")
            print(f"Exception in save_results: {str(e)}")
