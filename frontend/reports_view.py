from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QComboBox, QMessageBox, QGroupBox, 
    QHeaderView, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from utils.firebase_client import FirebaseClient

class ReportsView(QWidget):
    """View for generating and viewing student performance reports"""
    
    def __init__(self, id_token, user_uid, is_admin=False):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.is_admin = is_admin
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.standard_year_groups = ["Y7", "Y8", "Y9", "Y10", "Y11"]
        self.students_by_year = {}  # Cache students by year group
        self.setup_ui()
        self.load_terms()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Student Performance Report")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Report selection group
        selection_group = QGroupBox("Report Parameters")
        selection_layout = QVBoxLayout()
        
        # Report filters
        filters_layout = QHBoxLayout()
        
        # Year group filter
        filters_layout.addWidget(QLabel("Year Group:"))
        self.year_group_filter = QComboBox()
        self.year_group_filter.addItem("-- Select Year Group --")
        self.year_group_filter.addItems(self.standard_year_groups)
        self.year_group_filter.currentTextChanged.connect(self.on_year_group_changed)
        filters_layout.addWidget(self.year_group_filter)
        
        # Student filter - will be populated when year group is selected
        filters_layout.addWidget(QLabel("Student:"))
        self.student_filter = QComboBox()
        self.student_filter.addItem("-- Select Student --")
        self.student_filter.setEnabled(False)
        filters_layout.addWidget(self.student_filter)
        
        # Term filter
        filters_layout.addWidget(QLabel("Term:"))
        self.term_filter = QComboBox()
        self.term_filter.addItem("-- Select Term --")
        filters_layout.addWidget(self.term_filter)
        
        selection_layout.addLayout(filters_layout)
        
        # Generate report button
        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_report)
        selection_layout.addWidget(self.generate_report_button)
        
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)
        
        # Report display area
        report_display_group = QGroupBox("Performance Summary")
        report_display_layout = QVBoxLayout()
        
        # Student info header
        self.student_info_label = QLabel("")
        report_display_layout.addWidget(self.student_info_label)
        
        # Report table
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(3)
        self.report_table.setHorizontalHeaderLabels(["Subject", "Grade", "Teacher"])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        report_display_layout.addWidget(self.report_table)
        
        # Export button
        self.export_button = QPushButton("Export to PDF")
        self.export_button.clicked.connect(self.export_report)
        report_display_layout.addWidget(self.export_button)
        
        report_display_group.setLayout(report_display_layout)
        main_layout.addWidget(report_display_group)
        
        self.setLayout(main_layout)
    
    def load_terms(self):
        """Load available academic terms"""
        try:
            terms = self.firebase.get_collection("terms")
            
            self.term_filter.clear()
            self.term_filter.addItem("-- Select Term --", "")
            
            for term in terms:
                term_id = term.get('id', '')
                term_name = term.get('name', '')
                term_year = term.get('year', '')
                display_text = f"{term_name} {term_year}"
                self.term_filter.addItem(display_text, term_id)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load terms: {str(e)}")
    
    def on_year_group_changed(self, year_group):
        """Handle year group selection change"""
        if year_group == "-- Select Year Group --":
            self.student_filter.clear()
            self.student_filter.addItem("-- Select Student --")
            self.student_filter.setEnabled(False)
            return
            
        # Load students for the selected year group
        self.load_students_by_year_group(year_group)
    
    def load_students_by_year_group(self, year_group):
        """Load students for the selected year group"""
        try:
            # Check if we already have this year group's students cached
            if year_group in self.students_by_year:
                self.update_student_selector(self.students_by_year[year_group])
                return
                
            # Query students by year group
            students = self.firebase.query_collection_with_filters(
                "students", 
                [("year_group", "==", year_group)]
            )
            
            # Cache the results
            self.students_by_year[year_group] = students
            
            # Update the student selector
            self.update_student_selector(students)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load students: {str(e)}")
    
    def update_student_selector(self, students):
        """Update the student selector dropdown with the provided students"""
        self.student_filter.clear()
        self.student_filter.addItem("-- Select Student --", "")
        
        if not students:
            self.student_filter.setEnabled(False)
            return
            
        # Enable the selector and populate it
        self.student_filter.setEnabled(True)
        
        # Sort students by name for easier selection
        sorted_students = sorted(
            students, 
            key=lambda s: f"{s.get('first_name', '')} {s.get('last_name', '')}"
        )
        
        for student in sorted_students:
            student_id = student.get('id', '')
            first_name = student.get('first_name', '')
            last_name = student.get('last_name', '')
            
            # Use both first and last name if available
            if first_name or last_name:
                display_name = f"{first_name} {last_name}".strip()
            else:
                # Fallback to name field for backward compatibility
                display_name = student.get('name', 'Unknown')
                
            self.student_filter.addItem(display_name, student_id)
    
    def generate_report(self):
        """Generate student performance report"""
        # Get selected values
        year_group = self.year_group_filter.currentText()
        student_id = self.student_filter.currentData()
        term_id = self.term_filter.currentData()
        
        # Input validation
        if year_group == "-- Select Year Group --" or not student_id or not term_id:
            QMessageBox.warning(
                self, 
                "Selection Error", 
                "Please select a year group, student, and term."
            )
            return
            
        try:
            # Show loading indicator
            self.setCursor(Qt.WaitCursor)
            
            # Get the student details for display
            student_name = self.student_filter.currentText()
            term_name = self.term_filter.currentText()
            
            # Update the student info display
            self.student_info_label.setText(
                f"<b>Student:</b> {student_name} | <b>Year Group:</b> {year_group} | <b>Term:</b> {term_name}"
            )
            
            # Query Firestore for all results matching this term
            results = self.firebase.query_collection_with_filters(
                "results", 
                [("term_id", "==", term_id)]
            )
            
            # Clear existing table data
            self.report_table.setRowCount(0)
            
            # Process results
            if not results:
                QMessageBox.information(self, "No Data", f"No results found for {term_name}")
                self.setCursor(Qt.ArrowCursor)
                return
                
            # Find all subjects this student has grades for
            student_grades = []
            
            for result in results:
                # Check if this document contains results for our student
                student_results = result.get('student_results', {})
                if student_id in student_results:
                    subject = result.get('subject', 'Unknown')
                    grade = student_results[student_id]
                    teacher_id = result.get('teacher_id', '')
                    teacher_name = self.get_teacher_name(teacher_id)
                    
                    student_grades.append({
                        'subject': subject,
                        'grade': grade,
                        'teacher': teacher_name
                    })
            
            # Sort by subject name
            student_grades.sort(key=lambda x: x['subject'])
            
            # Display results in the table
            for i, grade_info in enumerate(student_grades):
                self.report_table.insertRow(i)
                
                # Set table cells
                self.report_table.setItem(i, 0, QTableWidgetItem(grade_info['subject']))
                self.report_table.setItem(i, 1, QTableWidgetItem(grade_info['grade']))
                self.report_table.setItem(i, 2, QTableWidgetItem(grade_info['teacher']))
            
            # Optionally, fetch attendance data as well if we want to show percentage
            self.load_attendance_data(student_id, year_group, term_id)
            
            self.setCursor(Qt.ArrowCursor)
            
        except Exception as e:
            self.setCursor(Qt.ArrowCursor)
            QMessageBox.warning(self, "Error", f"Failed to generate report: {str(e)}")
            print(f"Error generating report: {str(e)}")

    def load_attendance_data(self, student_id, year_group, term_id):
        """Load attendance data for the student"""
        try:
            # This would need to analyze attendance records from the attendance collection
            # and calculate attendance percentages
            # For now, let's just show a placeholder message about attendance
            
            # Get the term to find its start and end dates
            term_data = self.firebase.get_document("terms", term_id)
            
            if not term_data:
                print(f"Term data not found for ID: {term_id}")
                return
                
            # In a real implementation, we would:
            # 1. Find all attendance records for this student within the term date range
            # 2. Calculate the attendance percentage
            # 3. Display the percentage in a dedicated label or table row
            
        except Exception as e:
            print(f"Error loading attendance data: {str(e)}")
    
    def get_teacher_name(self, teacher_id):
        """Get teacher name from user ID"""
        if not teacher_id:
            return "Unknown"
        
        try:
            # Cache teacher names to avoid repeated lookups
            if not hasattr(self, 'teacher_cache'):
                self.teacher_cache = {}
                
            if teacher_id in self.teacher_cache:
                return self.teacher_cache[teacher_id]
                
            # Look up teacher in users collection
            teacher = self.firebase.get_document("users", teacher_id)
            
            if teacher and 'name' in teacher:
                name = teacher['name']
                self.teacher_cache[teacher_id] = name
                return name
            else:
                return "Unknown"
                
        except Exception as e:
            print(f"Error getting teacher name: {str(e)}")
            return "Unknown"
    
    def export_report(self):
        """Export the current report to PDF"""
        if self.report_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "There is no report data to export.")
            return
            
        # For now, just show a message
        QMessageBox.information(
            self,
            "Export Feature", 
            "PDF export will be implemented in the next version."
        )
        
        # Full implementation would use a PDF library like reportlab or QtPrintSupport
