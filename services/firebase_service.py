import os
from dotenv import load_dotenv

load_dotenv()

class FirebaseService:
    """Service class for Firebase configuration and endpoints"""
    
    def __init__(self):
        self.api_key = os.getenv("FIREBASE_API_KEY")
        self.project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        if not self.api_key or not self.project_id:
            raise ValueError("Firebase configuration missing in environment variables")
        
        # Firebase Auth REST API endpoints
        self.auth_base_url = "https://identitytoolkit.googleapis.com/v1"
        self.signin_endpoint = f"{self.auth_base_url}/accounts:signInWithPassword?key={self.api_key}"
        self.signup_endpoint = f"{self.auth_base_url}/accounts:signUp?key={self.api_key}"
        
        # Firestore REST API endpoints
        self.firestore_base_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"

    def get_auth_endpoint(self, operation):
        """Get the appropriate authentication endpoint"""
        if operation == "signin":
            return self.signin_endpoint
        elif operation == "signup":
            return self.signup_endpoint
        else:
            raise ValueError(f"Unknown authentication operation: {operation}")
    
    def get_firestore_endpoint(self, path=""):
        """Get Firestore endpoint for a specific path"""
        return f"{self.firestore_base_url}/{path}"
