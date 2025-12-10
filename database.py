from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./apsara.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True) # For Telegram users
    email = Column(String, unique=True, index=True, nullable=True)   # For Email users
    hashed_password = Column(String, nullable=True) # Only for Email users
    telegram_id = Column(Integer, unique=True, nullable=True)
    full_name = Column(String, default="Apsara Member")
    is_premium = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True) # Profile Picture
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Telegram Credentials
    api_id = Column(String, nullable=True) # Storing as String to be safe, though ID is int
    api_hash = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Security & RBAC
    role = Column(String, default="user") # 'super_admin', 'admin', 'user'
    two_factor_secret = Column(String, nullable=True) # Base32 secret for TOTP
    is_active = Column(Boolean, default=True)
    
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
