import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

# Lambda environment setup
sys.path.append('/opt/python')
sys.path.append('.')

# Set environment variables for Lambda
os.environ.setdefault('REDIS_URL', 'redis://cura-genesis-redis.9pj0z8.ng.0001.use1.cache.amazonaws.com:6379')
os.environ.setdefault('DATABASE_URL', 'postgresql://crmuser:CuraGenesis2024%21SecurePassword@cura-genesis-crm-db.c6ds4c4qok1n.us-east-1.rds.amazonaws.com:5432/cura_genesis_crm')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mangum import Mangum
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum as SQLEnum
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session, relationship
    from sqlalchemy.sql import func
    from pydantic import BaseModel, EmailStr
    from passlib.context import CryptContext
    from jose import JWTError, jwt
    from enum import Enum
    import redis
    
    # Import CRM modules (simplified for Lambda)
    Base = declarative_base()
    
    # User Roles Enum
    class UserRole(str, Enum):
        ADMIN = "admin"
        MANAGER = "manager" 
        AGENT = "agent"
    
    class LeadStatus(str, Enum):
        NEW = "NEW"
        CONTACTED = "CONTACTED"
        QUALIFIED = "QUALIFIED"
        CLOSED_WON = "CLOSED_WON"
        CLOSED_LOST = "CLOSED_LOST"
    
    # Database Models
    class User(Base):
        __tablename__ = "users"
        
        id = Column(Integer, primary_key=True, index=True)
        username = Column(String, unique=True, index=True, nullable=False)
        email = Column(String, unique=True, index=True, nullable=False)
        full_name = Column(String, nullable=True)
        hashed_password = Column(String, nullable=False)
        role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.AGENT)
        manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        
        # Relationships
        managed_users = relationship("User", backref="manager", remote_side=[id])
        assigned_leads = relationship("Lead", back_populates="assigned_user")

    class Lead(Base):
        __tablename__ = "leads"
        
        id = Column(Integer, primary_key=True, index=True)
        practice_name = Column(String, nullable=False)
        owner_name = Column(String, nullable=True) 
        practice_phone = Column(String, nullable=True)
        owner_phone = Column(String, nullable=True)
        address = Column(String, nullable=True)
        city = Column(String, nullable=True)
        state = Column(String, nullable=True)
        zip_code = Column(String, nullable=True)
        npi = Column(String, nullable=True)
        specialty = Column(String, nullable=True)
        score = Column(Float, default=0.0)
        priority = Column(String, default="B")
        status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
        assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
        
        # Relationships  
        assigned_user = relationship("User", back_populates="assigned_leads")

    # Pydantic Models
    class UserResponse(BaseModel):
        id: int
        username: str
        email: str
        full_name: Optional[str]
        role: UserRole
        manager_id: Optional[int]
        is_active: bool
        created_at: datetime
        
        class Config:
            from_attributes = True

    class CreateUserRequest(BaseModel):
        username: str
        email: EmailStr
        full_name: str
        password: str
        role: UserRole = UserRole.AGENT
        manager_id: Optional[int] = None

    class LeadResponse(BaseModel):
        id: int
        practice_name: str
        owner_name: Optional[str]
        practice_phone: Optional[str] 
        owner_phone: Optional[str]
        address: Optional[str]
        city: Optional[str]
        state: Optional[str]
        zip_code: Optional[str]
        npi: Optional[str]
        specialty: Optional[str]
        score: float
        priority: str
        status: LeadStatus
        assigned_user_id: Optional[int]
        created_at: datetime
        updated_at: datetime
        
        class Config:
            from_attributes = True

    class Token(BaseModel):
        access_token: str
        token_type: str

    class UserLogin(BaseModel):
        username: str
        password: str

    # Authentication
    SECRET_KEY = "cura-genesis-super-secret-key-production-lambda-2025"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    class AuthService:
        @staticmethod
        def get_password_hash(password: str) -> str:
            return pwd_context.hash(password)
        
        @staticmethod
        def verify_password(plain_password: str, hashed_password: str) -> bool:
            return pwd_context.verify(plain_password, hashed_password)
        
        @staticmethod
        def create_access_token(data: dict):
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
            return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Database setup
    engine = create_engine(os.environ['DATABASE_URL'])
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_current_user(request: Request, db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise credentials_exception
                
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
            
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        return user

    def get_current_active_user(current_user: User = Depends(get_current_user)):
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    # FastAPI App
    app = FastAPI(
        title="Cura Genesis CRM - Full Production",
        description="Complete CRM System with Admin User Management",
        version="2.0.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True, 
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    @app.get("/health")
    async def health_check():
        try:
            db = SessionLocal()
            total_leads = db.query(Lead).count()
            total_users = db.query(User).count()
            active_agents = db.query(User).filter(User.role == UserRole.AGENT, User.is_active == True).count()
            db.close()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "service": "Cura Genesis CRM - Full Production with Admin Management",
                "database": "connected",
                "database_stats": {
                    "total_leads": total_leads,
                    "total_users": total_users,
                    "active_agents": active_agents
                },
                "features": {
                    "admin_user_management": True,
                    "team_creation": True,
                    "role_based_access": True,
                    "lead_management": True,
                    "full_analytics": True
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    @app.post("/api/v1/auth/login", response_model=Token)
    async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
        user = db.query(User).filter(User.username == user_credentials.username).first()
        
        if not user or not AuthService.verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = AuthService.create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

    @app.get("/api/v1/auth/me", response_model=UserResponse)
    async def read_users_me(current_user: User = Depends(get_current_active_user)):
        return current_user

    @app.get("/api/v1/leads", response_model=List[LeadResponse])
    async def get_leads(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if current_user.role == UserRole.AGENT:
            # Agents can only see their assigned leads
            leads = db.query(Lead).filter(Lead.assigned_user_id == current_user.id).all()
        else:
            # Managers and admins can see all leads
            leads = db.query(Lead).all()
        
        return leads

    @app.post("/api/v1/team/create-user", response_model=UserResponse)
    async def create_team_member(
        user_data: CreateUserRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a new team member (Manager can create agents, Admin can create anyone)"""
        
        # Permission checks
        if current_user.role == UserRole.AGENT:
            raise HTTPException(status_code=403, detail="Agents cannot create users")
        elif current_user.role == UserRole.MANAGER:
            # Managers can only create agents under themselves
            if user_data.role != UserRole.AGENT:
                raise HTTPException(status_code=403, detail="Managers can only create agents")
            user_data.manager_id = current_user.id
        elif current_user.role == UserRole.ADMIN:
            # Admins can create anyone, but if creating an agent and manager_id not set, ask for it
            if user_data.role == UserRole.AGENT and user_data.manager_id is None:
                raise HTTPException(status_code=400, detail="Please specify a manager for this agent")
        
        # Check if username already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Validate manager exists if specified
        if user_data.manager_id:
            manager = db.query(User).filter(User.id == user_data.manager_id).first()
            if not manager:
                raise HTTPException(status_code=400, detail="Specified manager does not exist")
            if manager.role != UserRole.MANAGER:
                raise HTTPException(status_code=400, detail="Specified user is not a manager")
        
        # Create new user
        hashed_password = AuthService.get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            manager_id=user_data.manager_id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ New {user_data.role} created: {user_data.username} by {current_user.username}")
        return new_user

    @app.get("/api/v1/team/members", response_model=List[UserResponse])
    async def get_team_members(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get team members based on current user's role"""
        
        if current_user.role == UserRole.ADMIN:
            # Admins can see all users
            members = db.query(User).all()
        elif current_user.role == UserRole.MANAGER:
            # Managers can see their direct reports
            members = db.query(User).filter(User.manager_id == current_user.id).all()
        else:
            # Agents can only see themselves
            members = [current_user]
        
        return members

    @app.get("/api/v1/team/all-managers", response_model=List[UserResponse])
    async def get_all_managers(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get all managers (for admin use when creating agents)"""
        
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can view all managers")
        
        managers = db.query(User).filter(User.role == UserRole.MANAGER).all()
        return managers

    # Initialize database and create admin user
    def init_database():
        try:
            Base.metadata.create_all(bind=engine)
            
            db = SessionLocal()
            try:
                # Check if admin user exists
                admin_user = db.query(User).filter(User.username == "admin").first()
                if not admin_user:
                    # Create default admin user
                    admin_user = User(
                        username="admin",
                        email="admin@curagenesis.com",
                        full_name="System Administrator",
                        hashed_password=AuthService.get_password_hash("admin123"),
                        role=UserRole.ADMIN,
                        is_active=True
                    )
                    db.add(admin_user)
                    db.commit()
                    logger.info("✅ Default admin user created")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    # Initialize on import
    init_database()

    # Create Mangum handler for Lambda
    handler = Mangum(app)

except ImportError as e:
    logger.error(f"Import error: {e}")
    # Fallback minimal handler
    def handler(event, context):
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Import failed', 'details': str(e)})
        }

except Exception as e:
    logger.error(f"General error: {e}")
    # Fallback minimal handler
    def handler(event, context):
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Initialization failed', 'details': str(e)})
        } 