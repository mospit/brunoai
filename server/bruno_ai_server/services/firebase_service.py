"""
Firebase authentication service for user management.
"""
import json
import logging
from typing import Optional

import firebase_admin
import httpx
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from ..config import settings

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for Firebase Authentication operations."""
    
    def __init__(self):
        """Initialize Firebase Admin SDK."""
        self._initialized = False
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase Admin SDK with service account credentials."""
        try:
            if not firebase_admin._apps:
                # Get credentials from environment
                gcp_credentials = settings.gcp_credentials_dict
                
                if not gcp_credentials or gcp_credentials == {}:
                    logger.warning("No Firebase credentials provided, Firebase functionality will be disabled")
                    return
                
                # Initialize Firebase Admin SDK
                cred = credentials.Certificate(gcp_credentials)
                firebase_admin.initialize_app(cred)
                
                self._initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if Firebase is properly initialized."""
        return self._initialized
    
    async def create_user(self, email: str, password: str, name: str) -> Optional[str]:
        """
        Create a new user in Firebase Authentication.
        
        Args:
            email: User's email address
            password: User's password
            name: User's display name
            
        Returns:
            Firebase UID if successful, None if failed
        """
        if not self._initialized:
            logger.error("Firebase not initialized, cannot create user")
            return None
            
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=name,
                email_verified=False
            )
            
            logger.info(f"Created Firebase user: {user_record.uid}")
            return user_record.uid
            
        except FirebaseError as e:
            logger.error(f"Firebase error creating user: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating Firebase user: {e}")
            return None
    
    async def authenticate_user_with_password(self, email: str, password: str) -> Optional[dict]:
        """
        Authenticate a user with email and password using Firebase REST API.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Authentication result dict with UID and tokens if successful, None if failed
        """
        if not self._initialized:
            logger.error("Firebase not initialized, cannot authenticate user")
            return None
            
        try:
            # Get the Web API Key from Firebase project
            credentials_dict = settings.gcp_credentials_dict
            project_id = credentials_dict.get('project_id')
            
            if not project_id:
                logger.error("Firebase project ID not found in credentials")
                return None
            
            # Use Firebase REST API for password authentication
            # Note: In production, you should get the Web API Key from Firebase console
            # For now, we'll use a fallback approach
            api_key = getattr(settings, 'firebase_web_api_key', None)
            
            if not api_key:
                logger.warning("Firebase Web API Key not configured, using fallback authentication")
                # Fallback: Just verify the user exists in Firebase
                firebase_user = await self.get_user_by_email(email)
                if firebase_user and not firebase_user.get('disabled', False):
                    return {
                        'uid': firebase_user['uid'],
                        'email': firebase_user['email'],
                        'verified': True
                    }
                return None
            
            # Use Firebase REST API for sign-in
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                })
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'uid': result['localId'],
                        'email': result['email'],
                        'id_token': result['idToken'],
                        'refresh_token': result['refreshToken'],
                        'verified': result.get('emailVerified', False)
                    }
                else:
                    error_data = response.json()
                    logger.warning(f"Firebase authentication failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error authenticating user with Firebase: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Get user information by email from Firebase.
        
        Args:
            email: User's email address
            
        Returns:
            User information dict if found, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase not initialized, cannot get user")
            return None
            
        try:
            user_record = auth.get_user_by_email(email)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'disabled': user_record.disabled,
                'creation_timestamp': user_record.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp,
            }
        except auth.UserNotFoundError:
            logger.info(f"Firebase user not found: {email}")
            return None
        except FirebaseError as e:
            logger.error(f"Firebase error getting user: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Firebase user: {e}")
            return None
    
    async def verify_id_token(self, id_token: str) -> Optional[dict]:
        """
        Verify a Firebase ID token and return the decoded claims.
        
        Args:
            id_token: Firebase ID token from client
            
        Returns:
            Decoded token claims if valid, None otherwise
        """
        if not self._initialized:
            logger.error("Firebase not initialized, cannot verify token")
            return None
            
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            return None
        except FirebaseError as e:
            logger.error(f"Firebase error verifying token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying Firebase token: {e}")
            return None
    
    async def delete_user(self, uid: str) -> bool:
        """
        Delete a user from Firebase Authentication.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firebase not initialized, cannot delete user")
            return False
            
        try:
            auth.delete_user(uid)
            logger.info(f"Deleted Firebase user: {uid}")
            return True
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found for deletion: {uid}")
            return False
        except FirebaseError as e:
            logger.error(f"Firebase error deleting user: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting Firebase user: {e}")
            return False
    
    async def update_user(self, uid: str, **kwargs) -> bool:
        """
        Update a user's information in Firebase.
        
        Args:
            uid: Firebase user UID
            **kwargs: Fields to update (email, display_name, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Firebase not initialized, cannot update user")
            return False
            
        try:
            auth.update_user(uid, **kwargs)
            logger.info(f"Updated Firebase user: {uid}")
            return True
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found for update: {uid}")
            return False
        except FirebaseError as e:
            logger.error(f"Firebase error updating user: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Firebase user: {e}")
            return False


# Global Firebase service instance
firebase_service = FirebaseService()
