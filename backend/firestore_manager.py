import requests
import json
from services.firebase_service import FirebaseService

class FirestoreManager:
    """Manager for Firestore database operations"""
    
    def __init__(self):
        self.firebase_service = FirebaseService()
    
    def get_user_role(self, id_token, user_uid):
        """
        Get user role from Firestore
        Returns: (role, error_message)
        """
        try:
            headers = {
                "Authorization": f"Bearer {id_token}"
            }
            
            endpoint = self.firebase_service.get_firestore_endpoint(f"users/{user_uid}")
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", {})
                role = fields.get("role", {}).get("stringValue", "")
                return role, ""
            else:
                error_message = f"Error fetching user role: {response.status_code}"
                return "", error_message
                
        except requests.RequestException as e:
            return "", f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return "", "Invalid response from server"
    
    def create_user_profile(self, id_token, user_uid, email, role, name=""):
        """
        Create a new user profile in Firestore
        Returns: (success, error_message)
        """
        try:
            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "fields": {
                    "email": {"stringValue": email},
                    "role": {"stringValue": role},
                    "name": {"stringValue": name}
                }
            }
            
            endpoint = self.firebase_service.get_firestore_endpoint(f"users/{user_uid}")
            response = requests.patch(
                endpoint,
                headers=headers,
                json=payload
            )
            
            if response.status_code in (200, 201):
                return True, ""
            else:
                error_message = f"Error creating user profile: {response.status_code}"
                return False, error_message
                
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, "Invalid response from server"
    
    def get_user_profile(self, id_token, user_uid):
        """
        Get user profile from Firestore
        Returns: (success, profile_data, error_message)
        """
        try:
            headers = {
                "Authorization": f"Bearer {id_token}"
            }
            
            endpoint = self.firebase_service.get_firestore_endpoint(f"users/{user_uid}")
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", {})
                
                profile = {
                    "email": fields.get("email", {}).get("stringValue", ""),
                    "role": fields.get("role", {}).get("stringValue", ""),
                    "name": fields.get("name", {}).get("stringValue", "")
                }
                
                return True, profile, ""
            else:
                error_message = f"Error fetching user profile: {response.status_code}"
                return False, {}, error_message
                
        except requests.RequestException as e:
            return False, {}, f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, {}, "Invalid response from server"
    
    # Additional methods for managing students, terms, attendance, etc.
    def add_student(self, id_token, name, year_group, subjects):
        """
        Add a new student to Firestore
        Returns: (success, student_id, error_message)
        """
        try:
            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "fields": {
                    "name": {"stringValue": name},
                    "year_group": {"stringValue": year_group},
                    "subjects": {"arrayValue": {"values": [{"stringValue": subject} for subject in subjects]}}
                }
            }
            
            endpoint = self.firebase_service.get_firestore_endpoint("students")
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload
            )
            
            if response.status_code in (200, 201):
                data = response.json()
                # Extract student ID from the name field of the response
                document_path = data.get("name", "")
                student_id = document_path.split("/")[-1]
                return True, student_id, ""
            else:
                error_message = f"Error adding student: {response.status_code}"
                return False, "", error_message
                
        except requests.RequestException as e:
            return False, "", f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, "", "Invalid response from server"
    
    def add_term(self, id_token, term_id, name, year):
        """
        Add a new academic term to Firestore
        Returns: (success, error_message)
        """
        try:
            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "fields": {
                    "name": {"stringValue": name},
                    "year": {"stringValue": year}
                    # Removed start_date and end_date fields
                }
            }
            
            endpoint = self.firebase_service.get_firestore_endpoint(f"terms/{term_id}")
            response = requests.patch(
                endpoint,
                headers=headers,
                json=payload
            )
            
            if response.status_code in (200, 201):
                return True, ""
            else:
                error_message = f"Error adding term: {response.status_code}"
                return False, error_message
                
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, "Invalid response from server"
    
    def get_terms(self, id_token, year=None):
        """
        Get all terms or filter by year
        Returns: (success, terms_list, error_message)
        """
        try:
            headers = {
                "Authorization": f"Bearer {id_token}"
            }
            
            endpoint = self.firebase_service.get_firestore_endpoint("terms")
            
            # If year filter is provided, add a query
            if year:
                endpoint += f'?where.field=year&where.op=EQUAL&where.value={year}'
                
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                
                terms = []
                for doc in documents:
                    doc_id = doc.get("name", "").split("/")[-1]
                    fields = doc.get("fields", {})
                    
                    term = {
                        "id": doc_id,
                        "name": fields.get("name", {}).get("stringValue", ""),
                        "year": fields.get("year", {}).get("stringValue", "")
                        # Removed start_date and end_date fields
                    }
                    
                    terms.append(term)
                
                return True, terms, ""
            else:
                error_message = f"Error fetching terms: {response.status_code}"
                return False, [], error_message
                
        except requests.RequestException as e:
            return False, [], f"Network error: {str(e)}"
        except json.JSONDecodeError:
            return False, [], "Invalid response from server"
