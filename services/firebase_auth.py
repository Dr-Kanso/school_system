from backend.auth_manager import AuthManager

class FirebaseAuth:
    """
    Wrapper class for Firebase Authentication operations.
    Provides methods for user authentication and registration.
    """
    
    def __init__(self):
        self.auth_manager = AuthManager()
    
    def sign_in(self, email, password):
        """
        Sign in a user with email and password
        Returns: (success, id_token, user_uid, error_message)
        """
        return self.auth_manager.sign_in(email, password)
    
    def sign_up(self, email, password):
        """
        Sign up a new user with email and password
        Returns: (success, id_token, user_uid, error_message)
        """
        return self.auth_manager.sign_up(email, password)
    
    def get_current_token(self):
        """
        Get the current authentication token
        Returns: id_token or None if not authenticated
        """
        return self.auth_manager.id_token
    
    def get_current_user_uid(self):
        """
        Get the current user UID
        Returns: user_uid or None if not authenticated
        """
        return self.auth_manager.user_uid
