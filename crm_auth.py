#!/usr/bin/env python3
"""
Cura Genesis CRM - Authentication Module
JWT-based authentication with role-based access control
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator
import secrets
import re
import enum
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# ===================================================================
# DATABASE MODELS
# ===================================================================

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager" 
    AGENT = "agent"

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.AGENT)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    territory_id = Column(Integer, ForeignKey("territories.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255))
    reset_token = Column(String(255))
    reset_token_expires = Column(DateTime)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    assigned_leads = relationship("Lead", back_populates="assigned_agent")
    activities = relationship("Activity", back_populates="user")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def is_manager(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# ===================================================================
# PYDANTIC MODELS
# ===================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str = "agent"
    territory_id: Optional[int] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'manager', 'agent']:
            raise ValueError('Role must be admin, manager, or agent')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    territory_id: Optional[int] = None
    status: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str]
    role: str
    status: str
    territory_id: Optional[int]
    created_at: datetime
    last_login: Optional[datetime]
    is_verified: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        return UserCreate.validate_password(v)

# ===================================================================
# AUTHENTICATION SERVICE
# ===================================================================

class AuthService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        
        # Token expiration times
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.reset_token_expire_hours = 24
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_verification_token(self) -> str:
        """Create email verification token"""
        return secrets.token_urlsafe(32)
    
    def create_reset_token(self) -> str:
        """Create password reset token"""
        return secrets.token_urlsafe(32)
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            db.commit()
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.status = UserStatus.SUSPENDED
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account locked due to too many failed login attempts"
                )
            
            return None
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        db_user = User(
            email=user_data.email,
            password_hash=self.get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=UserRole(user_data.role),
            territory_id=user_data.territory_id,
            verification_token=self.create_verification_token()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created: {db_user.email} (ID: {db_user.id})")
        return db_user
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> User:
        """Update user information"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'role':
                value = UserRole(value)
            elif field == 'status':
                value = UserStatus(value)
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.email} (ID: {user.id})")
        return user
    
    def create_user_session(self, db: Session, user: User, ip_address: str = None, user_agent: str = None) -> UserSession:
        """Create user session"""
        # Generate tokens
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        # Store session
        session = UserSession(
            user_id=user.id,
            token_hash=self.get_password_hash(access_token),
            expires_at=datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session)
        db.commit()
        
        return session
    
    def revoke_user_session(self, db: Session, token: str):
        """Revoke user session"""
        try:
            payload = self.verify_token(token)
            user_id = int(payload.get("sub"))
            
            # Find and delete session
            session = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                db.delete(session)
                db.commit()
                
        except Exception as e:
            logger.warning(f"Failed to revoke session: {e}")
    
    def cleanup_expired_sessions(self, db: Session):
        """Clean up expired sessions"""
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        )
        
        count = expired_sessions.count()
        expired_sessions.delete()
        db.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")

# ===================================================================
# ROLE-BASED ACCESS CONTROL
# ===================================================================

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(lambda: None)):
        if current_user.role.value not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

# Role decorators
require_admin = RoleChecker(["admin"])
require_manager = RoleChecker(["admin", "manager"])
require_agent = RoleChecker(["admin", "manager", "agent"])

# ===================================================================
# DEPENDENCY INJECTION
# ===================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(lambda: None),  # Will be injected
    auth_service: AuthService = Depends(lambda: None)  # Will be injected
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = auth_service.get_user_by_id(db, int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# ===================================================================
# PERMISSION UTILITIES
# ===================================================================

def check_lead_access(user: User, lead_user_id: Optional[int] = None) -> bool:
    """Check if user can access lead"""
    if user.is_admin:
        return True
    
    if user.is_manager:
        # Managers can access leads in their territory
        # TODO: Implement territory-based access
        return True
    
    # Agents can only access their own leads
    return lead_user_id == user.id

def check_territory_access(user: User, territory_id: Optional[int] = None) -> bool:
    """Check if user can access territory"""
    if user.is_admin:
        return True
    
    if user.is_manager:
        # Managers can access their own territory
        return user.territory_id == territory_id
    
    # Agents can only access their own territory
    return user.territory_id == territory_id

# ===================================================================
# PASSWORD UTILITIES
# ===================================================================

def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password"""
    import string
    import secrets
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure password meets requirements
    if (any(c.islower() for c in password) and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*" for c in password)):
        return password
    else:
        return generate_secure_password(length)

def validate_password_strength(password: str) -> Dict[str, bool]:
    """Validate password strength and return detailed results"""
    return {
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r'[A-Z]', password)),
        "lowercase": bool(re.search(r'[a-z]', password)),
        "numbers": bool(re.search(r'\d', password)),
        "special_chars": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        "no_common_patterns": not any(pattern in password.lower() for pattern in 
                                    ['password', '123456', 'qwerty', 'admin']),
    }

# ===================================================================
# EMAIL VERIFICATION
# ===================================================================

async def send_verification_email(user: User, verification_url: str):
    """Send email verification (placeholder)"""
    # TODO: Implement email sending
    logger.info(f"Verification email would be sent to {user.email}: {verification_url}")

async def send_password_reset_email(user: User, reset_url: str):
    """Send password reset email (placeholder)"""
    # TODO: Implement email sending
    logger.info(f"Password reset email would be sent to {user.email}: {reset_url}")

# ===================================================================
# AUDIT LOGGING
# ===================================================================

def log_security_event(event_type: str, user_id: Optional[int] = None, details: Dict[str, Any] = None):
    """Log security events for audit purposes"""
    logger.info(f"Security event: {event_type}", extra={
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    })

# Export main components
__all__ = [
    "AuthService",
    "User", 
    "UserSession",
    "UserCreate",
    "UserLogin", 
    "UserUpdate",
    "UserResponse",
    "Token",
    "get_current_user",
    "get_current_active_user", 
    "get_current_admin_user",
    "require_admin",
    "require_manager", 
    "require_agent",
    "check_lead_access",
    "check_territory_access"
] 