from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTableWidget, QTableWidgetItem, QComboBox, 
                              QPushButton, QDateEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from utils.firebase_client import FirebaseClient

class AttendanceRegisterView(QWidget):
    def __init__(self, id_token=None, user_uid=None):
        super().__init__()
        self.id_token = id_token
        self.user_uid = user_uid
        self.setWindowTitle("Attendance Register")
        self.firebase = FirebaseClient(id_token=self.id_token)
        self.initUI()
        
    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Date selection
        date_label = QLabel("Date:")
        self.date_selector = QDateEdit()
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        
        # Class selection
        class_label = QLabel("Class:")
        self.class_selector = QComboBox()
        self.loadClasses()
        
        header_layout.addWidget(date_label)
        header_layout.addWidget(self.date_selector)
        header_layout.addWidget(class_label)
        header_layout.addWidget(self.class_selector)
        header_layout.addStretch()
        
        # Attendance table
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(3)
        self.attendance_table.setHorizontalHeaderLabels(["Student Name", "Present", "Notes"])
        
        # Button section
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Students")
        self.save_btn = QPushButton("Save Attendance")
        
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.save_btn)
        
        # Connect signals
        self.load_btn.clicked.connect(self.loadStudents)
        self.save_btn.clicked.connect(self.saveAttendance)
        self.class_selector.currentTextChanged.connect(self.onClassChanged)
        
        # Add all components to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.attendance_table)
        main_layout.addLayout(button_layout)
        
    def loadClasses(self):
        # Load classes using authenticated REST API
        self.class_selector.clear()
        try:
            classes = self.firebase.get_collection("classes")
            for class_doc in classes:
                self.class_selector.addItem(class_doc["name"], class_doc["id"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load classes: {str(e)}")
    
    def loadStudents(self):
        # Load students using REST API
        class_id = self.class_selector.currentData()
        if not class_id:
            return
            
        try:
            self.attendance_table.setRowCount(0)
            students = self.firebase.query_collection("students", "class_id", "==", class_id)
            
            for i, student in enumerate(students):
                self.attendance_table.insertRow(i)
                name_item = QTableWidgetItem(student["name"])
                name_item.setData(Qt.UserRole, student["id"])
                
                present_combo = QComboBox()
                present_combo.addItems(["Present", "Absent", "Late"])
                
                notes_item = QTableWidgetItem("")
                
                self.attendance_table.setItem(i, 0, name_item)
                self.attendance_table.setCellWidget(i, 1, present_combo)
                self.attendance_table.setItem(i, 2, notes_item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load students: {str(e)}")
    
    def onClassChanged(self, class_name):
        if class_name:
            self.loadStudents()
    
    def saveAttendance(self):
        # Save attendance using REST API
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        class_id = self.class_selector.currentData()
        
        if not class_id:
            QMessageBox.warning(self, "Warning", "Please select a class first")
            return
            
        try:
            doc_id = f"{class_id}_{selected_date}"
            
            attendance_data = {
                "class_id": class_id,
                "date": selected_date,
                "records": {}
            }
            
            for row in range(self.attendance_table.rowCount()):
                student_id = self.attendance_table.item(row, 0).data(Qt.UserRole)
                status = self.attendance_table.cellWidget(row, 1).currentText()
                notes = self.attendance_table.item(row, 2).text()
                
                attendance_data["records"][student_id] = {
                    "status": status,
                    "notes": notes
                }
            
            self.firebase.create_document("attendance", doc_id, attendance_data)
            QMessageBox.information(self, "Success", "Attendance saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save attendance: {str(e)}")
