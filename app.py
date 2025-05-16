import sys
import os
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from frontend.main_window import MainWindow

def main():
    # Load environment variables
    load_dotenv()
    
    # Create the application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("School Management System")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
