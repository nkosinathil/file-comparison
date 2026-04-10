"""
Authentication and SSO (Single Sign-On) Module
Supports OAuth2, SAML, and JWT token authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import jwt
import hashlib
import json
import secrets
import logging
import os
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# ==================== Pydantic Models ====================

class User(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "user"  # user, admin, investigator
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# ==================== Authentication Manager ====================

class AuthManager:
    """
    Manages authentication including local users, OAuth2, and SAML SSO
    """
    
    def __init__(self, users_db_path: str = "users.json"):
        self.users_db_path = Path(users_db_path)
        self.users_db: Dict[str, UserInDB] = {}
        self.oauth_states: Dict[str, Dict[str, Any]] = {}
        self.load_users()
        
        # Create default admin user if no users exist
        if not self.users_db:
            self.create_user(
                username="admin",
                email="admin@aurex.local",
                password="admin123",  # Change in production!
                full_name="System Administrator",
                role="admin"
            )
            logger.warning("Created default admin user with password 'admin123'. CHANGE THIS IN PRODUCTION!")
    
    def load_users(self):
        """Load users from JSON file"""
        if self.users_db_path.exists():
            try:
                with open(self.users_db_path, 'r') as f:
                    data = json.load(f)
                    self.users_db = {
                        username: UserInDB(**user_data)
                        for username, user_data in data.items()
                    }
                logger.info(f"Loaded {len(self.users_db)} users from database")
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                self.users_db = {}
        else:
            logger.info("No existing users database found")
    
    def save_users(self):
        """Save users to JSON file"""
        try:
            data = {
                username: user.dict()
                for username, user in self.users_db.items()
            }
            with open(self.users_db_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.users_db)} users to database")
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        return self.users_db.get(username)
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str = "user"
    ) -> bool:
        """Create a new user"""
        if username in self.users_db:
            return False
        
        user = UserInDB(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            disabled=False,
            hashed_password=self.get_password_hash(password)
        )
        
        self.users_db[username] = user
        self.save_users()
        logger.info(f"Created new user: {username}")
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = self.get_user(username)
        if not user:
            logger.warning(f"Authentication failed: user {username} not found")
            return None
        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password for {username}")
            return None
        logger.info(f"User {username} authenticated successfully")
        return User(**user.dict())
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if username is None:
                return None
            return TokenData(username=username, role=role)
        except jwt.PyJWTError as e:
            logger.error(f"Token decode error: {e}")
            return None
    
    # ==================== OAuth2 SSO Methods ====================
    
    def initiate_oauth_flow(
        self,
        client_id: str,
        redirect_uri: str,
        response_type: str = "code",
        scope: str = "openid profile email"
    ) -> str:
        """
        Initiate OAuth2 authorization flow
        Returns authorization URL for redirect
        """
        state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self.oauth_states[state] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "timestamp": datetime.now().isoformat()
        }
        
        # In production, this would redirect to actual OAuth provider
        # For now, return a simulated authorization URL
        oauth_provider_url = os.getenv("OAUTH_PROVIDER_URL", "https://oauth.provider.com/authorize")
        auth_url = (
            f"{oauth_provider_url}"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type={response_type}"
            f"&scope={scope}"
            f"&state={state}"
        )
        
        logger.info(f"OAuth flow initiated with state: {state}")
        return auth_url
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth2 callback and exchange code for token
        """
        # Validate state
        if state not in self.oauth_states:
            raise ValueError("Invalid state parameter")
        
        oauth_data = self.oauth_states.pop(state)
        
        # In production, exchange code for access token with OAuth provider
        # For now, simulate successful authentication
        
        # Simulate user data from OAuth provider
        user_data = {
            "username": "oauth_user",
            "email": "user@oauth.provider.com",
            "full_name": "OAuth User",
            "role": "user"
        }
        
        # Create or update user in local database
        if user_data["username"] not in self.users_db:
            # Create user with random password (they'll use OAuth)
            self.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=secrets.token_urlsafe(32),
                full_name=user_data["full_name"],
                role=user_data["role"]
            )
        
        # Generate access token
        access_token = self.create_access_token(
            data={"sub": user_data["username"], "role": user_data["role"]}
        )
        
        logger.info(f"OAuth callback successful for user: {user_data['username']}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
    
    # ==================== SAML SSO Methods ====================
    
    def process_saml_response(self, saml_response: str) -> Dict[str, Any]:
        """
        Process SAML 2.0 response and extract user information
        """
        try:
            # In production, use python3-saml library to parse and validate
            # For now, simulate SAML response processing
            
            # Decode and parse SAML response (simplified)
            import base64
            try:
                decoded = base64.b64decode(saml_response)
                # In production, parse XML and validate signature
                logger.info("SAML response received and decoded")
            except Exception as e:
                logger.error(f"Error decoding SAML response: {e}")
                raise ValueError("Invalid SAML response format")
            
            # Simulate extracted user data from SAML assertion
            user_data = {
                "username": "saml_user",
                "email": "user@saml.provider.com",
                "full_name": "SAML User",
                "role": "user"
            }
            
            # Create or update user in local database
            if user_data["username"] not in self.users_db:
                self.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=secrets.token_urlsafe(32),
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
            
            logger.info(f"SAML authentication successful for user: {user_data['username']}")
            return user_data
            
        except Exception as e:
            logger.error(f"SAML processing error: {e}")
            raise ValueError(f"SAML authentication failed: {str(e)}")


# ==================== Dependency Functions ====================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get current user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Use global auth_manager (set in main.py)
    from api.main import auth_manager
    
    token_data = auth_manager.decode_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception
    
    user = auth_manager.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return User(**user.dict())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get current active (non-disabled) user
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to require admin role
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
