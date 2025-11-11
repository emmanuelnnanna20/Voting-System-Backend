"""
Admin Routes - Handles admin authentication and election management
Admins can signup, login, create elections, and generate registration links
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import os
from database import get_db
from models import User, Election, Registration, UserRole, ElectionType
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    ElectionCreate, ElectionResponse, ElectionWithLinks, LinkResponse
)
from utils.security import (
    hash_password, verify_password, create_access_token,
    get_current_admin, generate_unique_token
)

router = APIRouter()

# Get frontend URL from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new admin account
    Checks if email already exists before creating user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(user_data.password),
        role=UserRole.ADMIN  # Set role as admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def admin_login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate an admin and return JWT token
    Verifies credentials and admin role
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    # Verify user exists, password is correct, and user is admin
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_admin_info(current_admin: User = Depends(get_current_admin)):
    """
    Get current admin's information
    Protected route - requires valid JWT token
    """
    return current_admin

@router.post("/elections", response_model=ElectionWithLinks, status_code=status.HTTP_201_CREATED)
def create_election(
    election_data: ElectionCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new election
    Validates dates and generates appropriate links based on election type
    """
    # Validate election dates
    if election_data.start_time >= election_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Create election
    new_election = Election(
        title=election_data.title,
        description=election_data.description,
        type=election_data.type,
        start_time=election_data.start_time,
        end_time=election_data.end_time,
        admin_id=current_admin.id
    )
    
    db.add(new_election)
    db.commit()
    db.refresh(new_election)
    
    # Generate links based on election type
    response = ElectionWithLinks.model_validate(new_election)
    
    if new_election.type == ElectionType.SECURED:
        # For secured elections, provide registration link
        response.registration_link = f"{FRONTEND_URL}/register/{new_election.id}"
    else:
        # For anonymous elections, provide direct voting link
        response.voting_link = f"{FRONTEND_URL}/vote/anonymous/{new_election.id}"
    
    return response

@router.get("/elections", response_model=List[ElectionResponse])
def get_admin_elections(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all elections created by the current admin
    Returns list of elections with their details
    """
    elections = db.query(Election).filter(Election.admin_id == current_admin.id).all()
    return elections

@router.get("/elections/{election_id}", response_model=ElectionWithLinks)
def get_election_details(
    election_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific election
    Includes registration/voting links
    """
    # Find election and verify ownership
    election = db.query(Election).filter(
        Election.id == election_id,
        Election.admin_id == current_admin.id
    ).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Build response with links
    response = ElectionWithLinks.model_validate(election)
    
    if election.type == ElectionType.SECURED:
        response.registration_link = f"{FRONTEND_URL}/register/{election.id}"
    else:
        response.voting_link = f"{FRONTEND_URL}/vote/anonymous/{election.id}"
    
    return response

@router.post("/elections/{election_id}/send-voting-links", response_model=dict)
def send_voting_links(
    election_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Send voting links to all registered voters for a secured election
    Should be called when the election starts
    """
    from utils.email_utils import send_bulk_voting_links
    
    # Find election and verify ownership
    election = db.query(Election).filter(
        Election.id == election_id,
        Election.admin_id == current_admin.id
    ).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    if election.type != ElectionType.SECURED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This feature is only for secured elections"
        )
    
    # Get all registered voters who haven't voted yet
    registrations = db.query(Registration).filter(
        Registration.election_id == election_id,
        Registration.has_voted == False
    ).all()
    
    if not registrations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered voters found"
        )
    
    # Prepare email data
    recipients_tokens = [(reg.voter_email, reg.unique_token) for reg in registrations]
    
    # Send emails
    results = send_bulk_voting_links(recipients_tokens, election.title)
    
    return {
        "message": "Voting links sent",
        "total_sent": results["success"],
        "failed": results["failed"],
        "failed_emails": results["failed_emails"]
    }

@router.get("/elections/{election_id}/registrations", response_model=List[dict])
def get_election_registrations(
    election_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of all registered voters for a secured election
    Shows voting status for each voter
    """
    # Verify election exists and belongs to admin
    election = db.query(Election).filter(
        Election.id == election_id,
        Election.admin_id == current_admin.id
    ).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Get all registrations
    registrations = db.query(Registration).filter(
        Registration.election_id == election_id
    ).all()
    
    return [
        {
            "id": reg.id,
            "voter_email": reg.voter_email,
            "registration_time": reg.registration_time,
            "has_voted": reg.has_voted
        }
        for reg in registrations
    ]