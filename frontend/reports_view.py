from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView,
    QHBoxLayout, QComboBox, QMessageBox, QGroupBox, 
    QHeaderView, QTableWidget, QTableWidgetItem, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from utils.firebase_client import FirebaseClient
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

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
        
        # Report table - change to 2 columns (remove teacher column)
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(2)  # Changed from 3 to 2
        self.report_table.setHorizontalHeaderLabels(["Subject", "Grade"])  # Removed "Teacher"
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        report_display_layout.addWidget(self.report_table)
        
        # Export button - change label to Export to DOCX
        self.export_button = QPushButton("Export to DOCX")
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
                    
                    student_grades.append({
                        'subject': subject,
                        'grade': grade
                    })
            
            # Sort by subject name
            student_grades.sort(key=lambda x: x['subject'])
            
            # Display results in the table
            for i, grade_info in enumerate(student_grades):
                self.report_table.insertRow(i)
                
                # Set table cells - just subject and grade, no teacher column
                self.report_table.setItem(i, 0, QTableWidgetItem(grade_info['subject']))
                self.report_table.setItem(i, 1, QTableWidgetItem(grade_info['grade']))
            
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
    
    def export_report(self):
        """Export the current report to DOCX with enhanced styling"""
        if self.report_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "There is no report data to export.")
            return
            
        try:
            # Get file save location from user
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Report as DOCX", "", "Word Documents (*.docx)"
            )
            
            if not file_path:  # User canceled the dialog
                return
                
            # Add .docx extension if not present
            if not file_path.lower().endswith(".docx"):
                file_path += ".docx"
                
            # Parse the student info from the label text
            student_info = self.student_info_label.text()
            
            # Create a new Word document with custom page margins
            doc = Document()
            sections = doc.sections
            for section in sections:
                section.top_margin = Cm(2)
                section.bottom_margin = Cm(2)
                section.left_margin = Cm(2.5)
                section.right_margin = Cm(2.5)
            
            # Add a title with custom formatting
            title = doc.add_heading('Student Performance Report', level=1)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # Apply custom font size and bold to the title run
            title_run = title.runs[0]
            title_run.font.size = Pt(18)
            title_run.font.color.rgb = RGBColor(0, 51, 102)  # Navy blue color
            
            # Add a horizontal line for visual separation
            self._add_horizontal_line(doc)
            
            # Extract student name, year group, and term from the info text
            student_parts = student_info.replace('<b>', '').replace('</b>', '').split('|')
            student_name = student_parts[0].split(':')[1].strip() if len(student_parts) > 0 else "Unknown"
            year_group = student_parts[1].split(':')[1].strip() if len(student_parts) > 1 else "Unknown"
            term_name = student_parts[2].split(':')[1].strip() if len(student_parts) > 2 else "Unknown"
            
            # Add styled student information
            student_info_para = doc.add_paragraph()
            student_info_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            student_info_para.space_after = Pt(6)
            
            # Add each piece of student info with proper styling
            self._add_styled_text(student_info_para, "Student: ", 'bold')
            self._add_styled_text(student_info_para, f"{student_name}", 'normal')
            student_info_para.add_run(" | ")
            self._add_styled_text(student_info_para, "Year Group: ", 'bold')  
            self._add_styled_text(student_info_para, f"{year_group}", 'normal')
            student_info_para.add_run(" | ")
            self._add_styled_text(student_info_para, "Term: ", 'bold')
            self._add_styled_text(student_info_para, f"{term_name}", 'normal')
            
            # Add spacer
            doc.add_paragraph()
            
            # Add a table for the report data with custom styling
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # Set table width to 80% of page width
            table.autofit = False
            table.width = Inches(6)
            
            # Style the header row with background color
            header_cells = table.rows[0].cells
            for cell in header_cells:
                cell_shading = OxmlElement('w:shd')
                cell_shading.set(qn('w:fill'), "D0E0E3")  # Light blue background
                cell._tc.get_or_add_tcPr().append(cell_shading)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            # Add table headers with bold formatting
            header_cells[0].text = ''  # Clear default text
            header_cells[1].text = ''
            
            # Add styled header text
            header_para0 = header_cells[0].paragraphs[0]
            header_para0.alignment = WD_ALIGN_PARAGRAPH.CENTER
            header_run0 = header_para0.add_run('Subject')
            header_run0.bold = True
            header_run0.font.size = Pt(12)
            
            header_para1 = header_cells[1].paragraphs[0]
            header_para1.alignment = WD_ALIGN_PARAGRAPH.CENTER
            header_run1 = header_para1.add_run('Grade')
            header_run1.bold = True
            header_run1.font.size = Pt(12)
            
            # Add data rows
            for row in range(self.report_table.rowCount()):
                cells = table.add_row().cells
                
                # Get cell values
                subject = self.report_table.item(row, 0).text()
                grade = self.report_table.item(row, 1).text()
                
                # Clear default cell text
                cells[0].text = ''
                cells[1].text = ''
                
                # Add styled subject text
                subject_para = cells[0].paragraphs[0]
                subject_run = subject_para.add_run(subject)
                subject_run.font.size = Pt(11)
                
                # Add styled grade text with centered alignment
                grade_para = cells[1].paragraphs[0]
                grade_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                grade_run = grade_para.add_run(grade)
                grade_run.font.size = Pt(11)
                grade_run.bold = True
                
                # Add different background colors based on grade value
                # This is an example - you can customize the coloring logic
                try:
                    grade_value = int(grade)
                    cell_shading = OxmlElement('w:shd')
                    
                    # Color coding by grade
                    if grade_value >= 7:
                        cell_shading.set(qn('w:fill'), "C6E0B4")  # Light green for high grades
                    elif grade_value >= 4:
                        cell_shading.set(qn('w:fill'), "FFFFFF")  # White for medium grades
                    else:
                        cell_shading.set(qn('w:fill'), "F8CBAD")  # Light red for low grades
                        
                    cells[1]._tc.get_or_add_tcPr().append(cell_shading)
                except (ValueError, TypeError):
                    # For non-numeric grades, don't add special coloring
                    pass
            
            # Apply alternating row colors to improve readability
            for i, row in enumerate(table.rows):
                if i > 0 and i % 2 == 0:  # Skip header row and apply to every other row
                    for cell in row.cells:
                        cell_shading = OxmlElement('w:shd')
                        cell_shading.set(qn('w:fill'), "F5F5F5")  # Light gray background
                        cell._tc.get_or_add_tcPr().append(cell_shading)
            
            # Add spacing before the generated date
            doc.add_paragraph()
            
            # Add generated date with proper italic formatting
            current_date = QDate.currentDate().toString("ddd MMM d yyyy")
            date_paragraph = doc.add_paragraph()
            date_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            date_run = date_paragraph.add_run(f"Generated on {current_date}")
            date_run.italic = True
            date_run.font.size = Pt(9)
            date_run.font.color.rgb = RGBColor(128, 128, 128)  # Gray text
            
            # Save the document
            doc.save(file_path)
            
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Report has been exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report: {str(e)}")
            print(f"Error during export: {str(e)}")

    def _add_horizontal_line(self, doc):
        """Add a horizontal line to the document"""
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_break()
        
        # Add a horizontal line using a border on a paragraph
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_fmt = p.paragraph_format
        p_fmt.space_before = Pt(0)
        p_fmt.space_after = Pt(12)
        
        # Add bottom border to this paragraph
        border = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '4')
        bottom.set(qn('w:space'), '0')
        bottom.set(qn('w:color'), '4F81BD')  # Blue line
        border.append(bottom)
        p._p.get_or_add_pPr().append(border)

    def _add_styled_text(self, paragraph, text, style):
        """Add text with the specified style to a paragraph"""
        run = paragraph.add_run(text)
        
        if style == 'bold':
            run.bold = True
            run.font.size = Pt(11)
        elif style == 'normal':
            run.font.size = Pt(11)
        
        return run
