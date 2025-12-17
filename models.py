"""
SQLAlchemy Database Models
Defines the structure of all database tables
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class UserRole(enum.Enum):
    """User roles in the system"""
    ADMIN = "admin"
    VOTER = "voter"

class ElectionType(enum.Enum):
    """Types of elections"""
    SECURED = "secured"      # Requires registration
    ANONYMOUS = "anonymous"  # Open to anyone

class User(Base):
    """
    Users table - stores admin and voter accounts
    Admins create elections, voters participate in them
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # Hashed password
    role = Column(Enum(UserRole), default=UserRole.VOTER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    elections = relationship("Election", back_populates="admin", cascade="all, delete-orphan")

class Election(Base):
    """
    Elections table - stores election details
    Each election is created by an admin and has a type (secured or anonymous)
    """
    __tablename__ = "elections"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(ElectionType), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    admin = relationship("User", back_populates="elections")
    positions = relationship("Position", back_populates="election", cascade="all, delete-orphan")
    options = relationship("Option", back_populates="election", cascade="all, delete-orphan")
    registrations = relationship("Registration", back_populates="election", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="election", cascade="all, delete-orphan")

class Position(Base):
    """
    Positions table - stores positions within an election (e.g., President, Vice President)
    Each election can have multiple positions, each with their own candidates/options
    """
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False)
    title = Column(String(255), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    election = relationship("Election", back_populates="positions")
    options = relationship("Option", back_populates="position", cascade="all, delete-orphan")

class Option(Base):
    """
    Options table - stores voting options/candidates for each election
    Each election can have multiple options that voters can choose from
    Options can optionally belong to a position (for multi-position elections)
    """
    __tablename__ = "options"
    
    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)  # Nullable for backward compat
    option_text = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    election = relationship("Election", back_populates="options")
    position = relationship("Position", back_populates="options")

class Registration(Base):
    """
    Registrations table - tracks voters registered for secured elections
    Each registration has a unique token used to generate voting links
    """
    __tablename__ = "registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False)
    voter_email = Column(String(255), nullable=False)
    registration_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    unique_token = Column(String(255), unique=True, nullable=False, index=True)
    has_voted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    election = relationship("Election", back_populates="registrations")

class Vote(Base):
    """
    Votes table - stores all cast votes
    voter_id is nullable to support anonymous voting
    position_id tracks which position this vote is for (multi-position elections)
    """
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)  # Nullable for single-position elections
    voter_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous votes
    choice = Column(String(255), nullable=False)  # The voter's selection
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    election = relationship("Election", back_populates="votes")
    position = relationship("Position")
    voter = relationship("User")