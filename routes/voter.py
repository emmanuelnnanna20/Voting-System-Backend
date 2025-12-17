"""
Voter Routes - Handles voter registration and voting
Supports both secured and anonymous voting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Election, Registration, Vote, Option, ElectionType, Position
from schemas import VoterRegistration, RegistrationResponse, VoteCreate, VoteResponse, MultiVoteResponse
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
    Returns election info and available voting options (grouped by position if multi-position)
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
    
    # Check if this is a multi-position election
    positions = db.query(Position).filter(Position.election_id == election.id).order_by(Position.order).all()
    
    if positions:
        # Multi-position election: return positions with their options
        positions_data = []
        for pos in positions:
            options = db.query(Option).filter(Option.position_id == pos.id).all()
            positions_data.append({
                "id": pos.id,
                "title": pos.title,
                "options": [{"id": opt.id, "text": opt.option_text} for opt in options]
            })
        
        return {
            "election_id": election.id,
            "title": election.title,
            "description": election.description,
            "start_time": election.start_time,
            "end_time": election.end_time,
            "voter_email": registration.voter_email,
            "is_multi_position": True,
            "positions": positions_data
        }
    else:
        # Single-position election: return flat options (backward compatible)
        options = db.query(Option).filter(Option.election_id == election.id).all()
        
        return {
            "election_id": election.id,
            "title": election.title,
            "description": election.description,
            "start_time": election.start_time,
            "end_time": election.end_time,
            "voter_email": registration.voter_email,
            "is_multi_position": False,
            "options": [{"id": opt.id, "text": opt.option_text} for opt in options]
        }

@router.post("/vote/{token}")
def cast_secured_vote(
    token: str,
    vote_data: VoteCreate,
    db: Session = Depends(get_db)
):
    """
    Cast a vote using a one-time voting token (secured voting)
    Supports both single-position and multi-position elections
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
    
    # Handle multi-position voting
    if vote_data.votes:
        votes_cast = []
        for position_vote in vote_data.votes:
            # Verify the position exists and belongs to this election
            position = db.query(Position).filter(
                Position.id == position_vote.position_id,
                Position.election_id == election.id
            ).first()
            
            if not position:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid position ID: {position_vote.position_id}"
                )
            
            # Verify the choice is valid for this position
            valid_option = db.query(Option).filter(
                Option.position_id == position.id,
                Option.option_text == position_vote.choice
            ).first()
            
            if not valid_option:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid option '{position_vote.choice}' for position '{position.title}'"
                )
            
            # Create vote record
            new_vote = Vote(
                election_id=election.id,
                position_id=position.id,
                voter_id=None,
                choice=position_vote.choice
            )
            db.add(new_vote)
            votes_cast.append(new_vote)
        
        # Mark registration as voted
        registration.has_voted = True
        db.commit()
        
        return MultiVoteResponse(
            message="Votes submitted successfully",
            election_id=election.id,
            votes_cast=len(votes_cast)
        )
    
    # Handle single-position voting (backward compatible)
    elif vote_data.choice:
        # Verify the choice is valid
        valid_option = db.query(Option).filter(
            Option.election_id == election.id,
            Option.option_text == vote_data.choice
        ).first()
        
        if not valid_option:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid voting option"
            )
        
        # Create vote record (voter_id is None for privacy)
        new_vote = Vote(
            election_id=election.id,
            position_id=None,
            voter_id=None,
            choice=vote_data.choice
        )
        
        # Mark registration as voted
        registration.has_voted = True
        
        db.add(new_vote)
        db.commit()
        db.refresh(new_vote)
        
        return new_vote
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No vote data provided"
        )

@router.get("/anonymous-vote-info/{election_id}")
def get_anonymous_vote_info(election_id: int, db: Session = Depends(get_db)):
    """
    Get election information for anonymous voting
    Anyone can access this without registration
    Returns election info and available voting options (grouped by position if multi-position)
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
    
    # Check if this is a multi-position election
    positions = db.query(Position).filter(Position.election_id == election.id).order_by(Position.order).all()
    
    if positions:
        # Multi-position election: return positions with their options
        positions_data = []
        for pos in positions:
            options = db.query(Option).filter(Option.position_id == pos.id).all()
            positions_data.append({
                "id": pos.id,
                "title": pos.title,
                "options": [{"id": opt.id, "text": opt.option_text} for opt in options]
            })
        
        return {
            "election_id": election.id,
            "title": election.title,
            "description": election.description,
            "start_time": election.start_time,
            "end_time": election.end_time,
            "is_multi_position": True,
            "positions": positions_data
        }
    else:
        # Single-position election: return flat options (backward compatible)
        options = db.query(Option).filter(Option.election_id == election.id).all()
        
        return {
            "election_id": election.id,
            "title": election.title,
            "description": election.description,
            "start_time": election.start_time,
            "end_time": election.end_time,
            "is_multi_position": False,
            "options": [{"id": opt.id, "text": opt.option_text} for opt in options]
        }

@router.post("/vote/anonymous/{election_id}")
def cast_anonymous_vote(
    election_id: int,
    vote_data: VoteCreate,
    db: Session = Depends(get_db)
):
    """
    Cast an anonymous vote (no registration required)
    Supports both single-position and multi-position elections
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
    
    # Handle multi-position voting
    if vote_data.votes:
        votes_cast = []
        for position_vote in vote_data.votes:
            # Verify the position exists and belongs to this election
            position = db.query(Position).filter(
                Position.id == position_vote.position_id,
                Position.election_id == election.id
            ).first()
            
            if not position:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid position ID: {position_vote.position_id}"
                )
            
            # Verify the choice is valid for this position
            valid_option = db.query(Option).filter(
                Option.position_id == position.id,
                Option.option_text == position_vote.choice
            ).first()
            
            if not valid_option:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid option '{position_vote.choice}' for position '{position.title}'"
                )
            
            # Create vote record
            new_vote = Vote(
                election_id=election.id,
                position_id=position.id,
                voter_id=None,
                choice=position_vote.choice
            )
            db.add(new_vote)
            votes_cast.append(new_vote)
        
        db.commit()
        
        return MultiVoteResponse(
            message="Votes submitted successfully",
            election_id=election.id,
            votes_cast=len(votes_cast)
        )
    
    # Handle single-position voting (backward compatible)
    elif vote_data.choice:
        # Verify the choice is valid
        valid_option = db.query(Option).filter(
            Option.election_id == election.id,
            Option.option_text == vote_data.choice
        ).first()
        
        if not valid_option:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid voting option"
            )
        
        # Create anonymous vote record
        new_vote = Vote(
            election_id=election_id,
            position_id=None,
            voter_id=None,
            choice=vote_data.choice
        )
        
        db.add(new_vote)
        db.commit()
        db.refresh(new_vote)
        
        return new_vote
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No vote data provided"
        )