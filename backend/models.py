from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class User:
    uid: str
    email: str
    role: str
    name: str = ""

@dataclass
class Student:
    student_id: str
    name: str
    year_group: str
    subjects: List[str]

@dataclass
class Term:
    term_id: str
    name: str
    start_date: datetime
    end_date: datetime

@dataclass
class AttendanceRecord:
    date: str
    subject: str
    year_group: str
    records: Dict[str, str]  # student_id -> "Present"/"Absent"

@dataclass
class SubjectResult:
    subject: str
    grade: str

@dataclass
class StudentReport:
    student_id: str
    term_id: str
    attendance_percentage: float
    subject_results: List[SubjectResult]
