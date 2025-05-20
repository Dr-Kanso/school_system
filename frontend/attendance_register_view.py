from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTableWidget, QTableWidgetItem, QComboBox, 
                              QPushButton, QDateEdit, QMessageBox, QGroupBox,
                              QGridLayout, QHeaderView)
from PySide6.QtCore import Qt, QDate
from utils.firebase_client import FirebaseClient

class AttendanceRegisterView(QWidget):
    def __init__(self, id_token=None, user_uid=None):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.setWindowTitle("Attendance Register")
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.teacher_assignments = []  # Store teacher's subject assignments
        self.standard_year_groups = ["Y7", "Y8", "Y9", "Y10", "Y11"]  # Standard year groups matching student management
        self.initUI()
        
    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Class selection section in a group box
        class_group = QGroupBox("Class Information")
        class_layout = QGridLayout()
        
        # Date selection
        date_label = QLabel("Date:")
        self.date_selector = QDateEdit()
        self.date_selector.setDate(QDate.currentDate())  # This line sets the default date to today
        self.date_selector.setCalendarPopup(True)
        
        # Subject selection
        subject_label = QLabel("Subject:")
        self.subject_selector = QComboBox()
        
        # Year group selection
        year_label = QLabel("Year Group:")
        self.year_group_selector = QComboBox()
        
        # Add widgets to grid layout
        class_layout.addWidget(date_label, 0, 0)
        class_layout.addWidget(self.date_selector, 0, 1)
        class_layout.addWidget(subject_label, 0, 2)
        class_layout.addWidget(self.subject_selector, 0, 3)
        class_layout.addWidget(year_label, 1, 0)
        class_layout.addWidget(self.year_group_selector, 1, 1)
        
        class_group.setLayout(class_layout)
        main_layout.addWidget(class_group)
        
        # Student information section
        student_group = QGroupBox("Student Attendance")
        student_layout = QVBoxLayout()
        
        # Attendance table
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)  # Added column for year group
        self.attendance_table.setHorizontalHeaderLabels(["Student Name", "Year Group", "Present", "Notes"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        student_layout.addWidget(self.attendance_table)
        student_group.setLayout(student_layout)
        main_layout.addWidget(student_group)
        
        # Button section
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Students")
        self.save_btn = QPushButton("Save Attendance")
        
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.save_btn)
        
        # Connect signals
        self.load_btn.clicked.connect(self.loadStudents)
        self.save_btn.clicked.connect(self.saveAttendance)
        self.subject_selector.currentTextChanged.connect(self.onSubjectChanged)
        self.year_group_selector.currentTextChanged.connect(self.onYearGroupChanged)
        
        main_layout.addLayout(button_layout)
        
        # Load teacher's subject assignments
        self.loadTeacherAssignments()
        
    def loadTeacherAssignments(self):
        """Load the subjects and year groups assigned to this teacher"""
        try:
            # Debug message to verify user_uid
            print(f"Loading assignments for teacher ID: {self.user_uid}")
            
            # Use query_collection_with_filters instead for more reliable Firestore queries
            teacher_assignments = self.firebase.query_collection_with_filters(
                "teacher_assignments", 
                [("teacher_id", "==", self.user_uid)]
            )
            
            # Enhanced debugging - print each assignment in detail
            print(f"Found {len(teacher_assignments)} assignments for the teacher")
            for i, assignment in enumerate(teacher_assignments):
                print(f"Assignment {i+1}:")
                print(f"  Subject: {assignment.get('subject')}")
                print(f"  Year Groups (raw): {assignment.get('year_groups')}")
                print(f"  Year Groups (type): {type(assignment.get('year_groups'))}")
            
            self.teacher_assignments = teacher_assignments
            
            # Update the subject selector
            self.updateSubjectSelector()
            
            # Remove auto-selection of first subject
            # if self.subject_selector.count() > 1:
            #     self.subject_selector.setCurrentIndex(1)
                
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
        
        # Auto-select first year group if available
        if self.year_group_selector.count() > 1:
            self.year_group_selector.setCurrentIndex(1)
    
    def onSubjectChanged(self, subject):
        if self.subject_selector.currentData():
            # Update year group selector for this subject
            self.updateYearGroupSelector(subject)
            # Clear any previously loaded students
            self.attendance_table.setRowCount(0)
            # Don't auto-load students anymore
            # if self.year_group_selector.currentData():
            #     self.loadStudents()
    
    def onYearGroupChanged(self, year_group):
        # Don't auto-load students on year group change
        # if self.year_group_selector.currentData():
        #     self.loadStudents()
        pass
    
    def loadStudents(self):
        # Load students based on subject and year group
        subject = self.subject_selector.currentData()
        year_group = self.year_group_selector.currentData()
        
        if not subject or not year_group:
            return
            
        try:
            self.attendance_table.setRowCount(0)
            
            # Standardize year group format for querying
            standardized_year_group = year_group.strip().upper()
            if standardized_year_group not in self.standard_year_groups:
                print(f"Invalid year group format: {year_group}")
                return
                
            # Use exact year group match to ensure consistency with student management
            students = self.firebase.query_collection_with_filters(
                "students", 
                [("year_group", "==", standardized_year_group)]
            )
            
            if not students:
                print(f"No students found for year group: {year_group}")
                QMessageBox.information(self, "No Students", f"No students found for year group {year_group}")
                return
                
            print(f"Found {len(students)} students for year group {year_group}")
            
            # Debug - print each student and their subjects
            for student in students:
                print(f"Student: {student.get('name')}, Year: {student.get('year_group')}, Subjects: {student.get('subjects')}")
            
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
                
                # Print clean subjects for debugging
                print(f"Looking for subject '{subject}' in cleaned subjects: {clean_subjects}")
                
                # Case-insensitive comparison with clean subjects
                if any(s.lower() == subject.lower() for s in clean_subjects):
                    filtered_students.append(student)
            
            print(f"After filtering: {len(filtered_students)} students taking {subject}")
            
            # Format attendance document ID consistently
            attendance_date = self.date_selector.date().toString('yyyy-MM-dd')
            attendance_doc_id = f"{year_group}_{subject}_{attendance_date}"
            
            # Load existing attendance records if any
            existing_attendance = None
            try:
                existing_attendance = self.firebase.get_document("attendance", attendance_doc_id)
            except Exception as e:
                print(f"No existing attendance found: {str(e)}")
            
            existing_records = existing_attendance.get("records", {}) if existing_attendance else {}
            
            for i, student in enumerate(filtered_students):
                self.attendance_table.insertRow(i)
                
                # Build student name from first_name and last_name if available
                first_name = student.get("first_name", "")
                last_name = student.get("last_name", "")
                
                if first_name or last_name:
                    student_name = f"{first_name} {last_name}".strip()
                else:
                    # Fallback to old name field
                    student_name = student.get("name", "")
                
                name_item = QTableWidgetItem(student_name)
                name_item.setData(Qt.UserRole, student.get("id", ""))
                self.attendance_table.setItem(i, 0, name_item)
                
                # Year group - ensure consistent format
                year_group_item = QTableWidgetItem(student.get("year_group", ""))
                self.attendance_table.setItem(i, 1, year_group_item)
                
                # Present/absent dropdown
                present_combo = QComboBox()
                present_combo.addItems(["Present", "Absent", "Late"])
                
                # Set value from existing records if available
                student_id = student.get("id", "")
                if student_id in existing_records:
                    status = existing_records[student_id].get("status", "Present")
                    index = present_combo.findText(status)
                    if index >= 0:
                        present_combo.setCurrentIndex(index)
                
                self.attendance_table.setCellWidget(i, 2, present_combo)
                
                # Notes
                notes_text = ""
                if student_id in existing_records:
                    notes_text = existing_records[student_id].get("notes", "")
                notes_item = QTableWidgetItem(notes_text)
                self.attendance_table.setItem(i, 3, notes_item)
            
            # Resize columns to fit content
            self.attendance_table.resizeColumnsToContents()
            self.attendance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load students: {str(e)}")
            print(f"Exception in loadStudents: {str(e)}, type: {type(e)}")
    
    def saveAttendance(self):
        # Save attendance using REST API
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        subject = self.subject_selector.currentData()
        year_group = self.year_group_selector.currentData()
        
        if not subject or not year_group:
            QMessageBox.warning(self, "Warning", "Please select a subject and year group first")
            return
            
        try:
            # Format document ID consistently with loadStudents
            doc_id = f"{year_group}_{subject}_{selected_date}"
            
            attendance_data = {
                "subject": subject,
                "year_group": year_group,
                "date": selected_date,
                "records": {}
            }
            
            for row in range(self.attendance_table.rowCount()):
                student_id = self.attendance_table.item(row, 0).data(Qt.UserRole)
                status = self.attendance_table.cellWidget(row, 2).currentText()
                notes = self.attendance_table.item(row, 3).text()
                
                attendance_data["records"][student_id] = {
                    "status": status,
                    "notes": notes
                }
            
            self.firebase.create_document("attendance", doc_id, attendance_data)
            QMessageBox.information(self, "Success", "Attendance saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save attendance: {str(e)}")
