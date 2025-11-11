"""
Voter Routes - Handles voter registration and voting
Supports both secured and anonymous voting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Election, Registration, Vote, ElectionType
from schemas import VoterRegistration, RegistrationResponse, VoteCreate, VoteResponse
from utils.security import generate_unique_token

router = APIRouter()

@router.post("/register/{election_id}", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_for_election(
    election_id: int,
    registration_data: VoterRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a voter for a secured election
    Generates a unique token for the voter and sends confirmation email
    """
    # Find the election
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Verify it's a secured election
    if election.type != ElectionType.SECURED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is only for secured elections"
        )
    
    # Check if voter already registered
    existing_registration = db.query(Registration).filter(
        Registration.election_id == election_id,
        Registration.voter_email == registration_data.email
    ).first()
    
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for this election"
        )
    
    # Create new registration with unique token
    new_registration = Registration(
        election_id=election_id,
        voter_email=registration_data.email,
        unique_token=generate_unique_token(),
        has_voted=False
    )
    
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)
    
    # Send confirmation email
    from utils.email_utils import send_registration_confirmation
    send_registration_confirmation(registration_data.email, election.title)
    
    return new_registration

@router.get("/vote-info/{token}")
def get_vote_info(token: str, db: Session = Depends(get_db)):
    """
    Get election information using voting token
    Used to display election details before voter casts their vote
    """
    # Find registration by token
    registration = db.query(Registration).filter(
        Registration.unique_token == token
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid voting link"
        )
    
    # Check if already voted
    if registration.has_voted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This voting link has already been used"
        )
    
    # Get election details
    election = db.query(Election).filter(Election.id == registration.election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Check if election is active
    now = datetime.utcnow()
    if now < election.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has not started yet"
        )
    
    if now > election.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has ended"
        )
    
    return {
        "election_id": election.id,
        "title": election.title,
        "description": election.description,
        "start_time": election.start_time,
        "end_time": election.end_time,
        "voter_email": registration.voter_email
    }

@router.post("/vote/{token}", response_model=VoteResponse)
def cast_secured_vote(
    token: str,
    vote_data: VoteCreate,
    db: Session = Depends(get_db)
):
    """
    Cast a vote using a one-time voting token (secured voting)
    Marks the token as used after voting
    """
    # Find registration by token
    registration = db.query(Registration).filter(
        Registration.unique_token == token
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid voting link"
        )
    
    # Check if already voted
    if registration.has_voted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already voted. Each link can only be used once."
        )
    
    # Get election
    election = db.query(Election).filter(Election.id == registration.election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Check election timeline
    now = datetime.utcnow()
    if now < election.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has not started yet"
        )
    
    if now > election.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has ended"
        )
    
    # Create vote record (voter_id is None for privacy)
    new_vote = Vote(
        election_id=election.id,
        voter_id=None,  # Keep voter identity anonymous
        choice=vote_data.choice
    )
    
    # Mark registration as voted
    registration.has_voted = True
    
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    
    return new_vote

@router.get("/anonymous-vote-info/{election_id}")
def get_anonymous_vote_info(election_id: int, db: Session = Depends(get_db)):
    """
    Get election information for anonymous voting
    Anyone can access this without registration
    """
    # Find the election
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Verify it's an anonymous election
    if election.type != ElectionType.ANONYMOUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is not an anonymous election"
        )
    
    # Check if election is active
    now = datetime.utcnow()
    if now < election.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has not started yet"
        )
    
    if now > election.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has ended"
        )
    
    return {
        "election_id": election.id,
        "title": election.title,
        "description": election.description,
        "start_time": election.start_time,
        "end_time": election.end_time
    }

@router.post("/vote/anonymous/{election_id}", response_model=VoteResponse)
def cast_anonymous_vote(
    election_id: int,
    vote_data: VoteCreate,
    db: Session = Depends(get_db)
):
    """
    Cast an anonymous vote (no registration required)
    Note: In production, implement additional measures to prevent duplicate voting
    (e.g., IP tracking, browser fingerprinting, or CAPTCHA)
    """
    # Find the election
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Verify it's an anonymous election
    if election.type != ElectionType.ANONYMOUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This election requires registration"
        )
    
    # Check election timeline
    now = datetime.utcnow()
    if now < election.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has not started yet"
        )
    
    if now > election.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Election has ended"
        )
    
    # Create anonymous vote record
    new_vote = Vote(
        election_id=election_id,
        voter_id=None,  # No voter ID for anonymous votes
        choice=vote_data.choice
    )
    
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    
    return new_vote