import requests
import json
from services.firebase_service import FirebaseService

class AuthManager:
    """Manager for Firebase Authentication operations"""
    
    def __init__(self):
        self.firebase_service = FirebaseService()
        self.id_token = None
        self.user_uid = None
    
    def sign_in(self, email, password):
        """
        Sign in a user with email and password
        Returns: (success, id_token, user_uid, error_message)
        """
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(
                self.firebase_service.get_auth_endpoint("signin"),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.id_token = data.get("idToken")
                self.user_uid = data.get("localId")
                return True, self.id_token, self.user_uid, ""
            else:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                return False, None, None, error_message
                
        except requests.RequestException as e:
            return False, None, None, f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, None, None, "Invalid response from server"
    
    def sign_up(self, email, password, role="teacher"):
        """
        Sign up a new user with email and password
        Returns: (success, id_token, user_uid, error_message)
        """
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(
                self.firebase_service.get_auth_endpoint("signup"),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.id_token = data.get("idToken")
                self.user_uid = data.get("localId")
                return True, self.id_token, self.user_uid, ""
            else:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                return False, None, None, error_message
                
        except requests.RequestException as e:
            return False, None, None, f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, None, None, "Invalid response from server"
    
    def clear_auth_state(self):
        """Clear the authentication state"""
        self.id_token = None
        self.user_uid = None
        return True
