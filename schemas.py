"""
Pydantic Schemas for Request/Response Validation
Ensures data integrity and provides automatic API documentation
"""
from pydantic import BaseModel, EmailStr, Field, model_validator
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

# Position Schemas (for multi-position elections)
class PositionCreate(BaseModel):
    """Schema for creating a position within an election"""
    title: str = Field(..., min_length=1, max_length=255)
    options: List[str] = Field(..., min_length=2, description="Candidates for this position (minimum 2)")

# Election Schemas
class ElectionCreate(BaseModel):
    """
    Schema for creating a new election
    Supports both single-position (backward compatible) and multi-position elections
    """
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    type: ElectionType
    start_time: datetime
    end_time: datetime
    # Single position mode (backward compatible)
    options: Optional[List[str]] = Field(None, description="Simple options for single-position elections")
    # Multi-position mode
    positions: Optional[List[PositionCreate]] = Field(None, description="Multiple positions with their candidates")
    
    @model_validator(mode='after')
    def validate_options_or_positions(self):
        """Ensure either options or positions is provided, not both"""
        if self.options and self.positions:
            raise ValueError("Provide either 'options' (single-position) or 'positions' (multi-position), not both")
        if not self.options and not self.positions:
            raise ValueError("Either 'options' or 'positions' must be provided")
        if self.options and len(self.options) < 2:
            raise ValueError("At least 2 voting options are required")
        return self


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
class PositionVote(BaseModel):
    """Schema for voting on a single position in multi-position elections"""
    position_id: int
    choice: str = Field(..., min_length=1, max_length=255)

class VoteCreate(BaseModel):
    """
    Schema for casting votes
    Supports both single-position (backward compatible) and multi-position elections
    """
    # Single position mode (backward compatible)
    choice: Optional[str] = Field(None, min_length=1, max_length=255)
    # Multi-position mode
    votes: Optional[List[PositionVote]] = Field(None, description="Votes for each position")
    
    @model_validator(mode='after')
    def validate_choice_or_votes(self):
        """Ensure either choice or votes is provided for voting"""
        if self.choice and self.votes:
            raise ValueError("Provide either 'choice' (single-position) or 'votes' (multi-position), not both")
        if not self.choice and not self.votes:
            raise ValueError("Either 'choice' or 'votes' must be provided")
        return self

class VoteResponse(BaseModel):
    """Schema for vote confirmation"""
    id: int
    election_id: int
    choice: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MultiVoteResponse(BaseModel):
    """Schema for multi-position vote confirmation"""
    message: str
    election_id: int
    votes_cast: int
    
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