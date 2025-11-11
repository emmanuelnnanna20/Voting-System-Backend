"""
Pydantic Schemas for Request/Response Validation
Ensures data integrity and provides automatic API documentation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    VOTER = "voter"

class ElectionType(str, Enum):
    SECURED = "secured"
    ANONYMOUS = "anonymous"

# User Schemas
class UserCreate(BaseModel):
    """Schema for creating a new user (signup)"""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    email: Optional[str] = None
    user_id: Optional[int] = None

# Election Schemas
class ElectionCreate(BaseModel):
    """Schema for creating a new election"""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    type: ElectionType
    start_time: datetime
    end_time: datetime

class ElectionResponse(BaseModel):
    """Schema for election data in responses"""
    id: int
    title: str
    description: Optional[str]
    type: ElectionType
    start_time: datetime
    end_time: datetime
    admin_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ElectionWithLinks(ElectionResponse):
    """Schema for election with registration/voting links"""
    registration_link: Optional[str] = None
    voting_link: Optional[str] = None

# Registration Schemas
class VoterRegistration(BaseModel):
    """Schema for voter registration"""
    email: EmailStr

class RegistrationResponse(BaseModel):
    """Schema for registration confirmation"""
    id: int
    election_id: int
    voter_email: str
    registration_time: datetime
    
    class Config:
        from_attributes = True

# Vote Schemas
class VoteCreate(BaseModel):
    """Schema for casting a vote"""
    choice: str = Field(..., min_length=1, max_length=255)

class VoteResponse(BaseModel):
    """Schema for vote confirmation"""
    id: int
    election_id: int
    choice: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Results Schemas
class ElectionResults(BaseModel):
    """Schema for election results"""
    election_id: int
    election_title: str
    total_votes: int
    results: List[dict]  # List of {choice: str, count: int, percentage: float}
    
# Link Generation Schemas
class LinkResponse(BaseModel):
    """Schema for generated links"""
    link: str
    message: str