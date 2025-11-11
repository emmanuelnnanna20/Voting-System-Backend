"""
Election Routes - Handles election results and public election information
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from models import Election, Vote, Registration
from schemas import ElectionResults, ElectionResponse
from utils.security import get_current_admin
from models import User

router = APIRouter()

@router.get("/{election_id}/results", response_model=ElectionResults)
def get_election_results(election_id: int, db: Session = Depends(get_db)):
    """
    Get results for a specific election
    Shows vote counts and percentages for each choice
    Public endpoint - anyone can view results
    """
    # Find the election
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Get all votes for this election grouped by choice
    vote_counts = db.query(
        Vote.choice,
        func.count(Vote.id).label('count')
    ).filter(
        Vote.election_id == election_id
    ).group_by(Vote.choice).all()
    
    # Calculate total votes
    total_votes = sum(count for _, count in vote_counts)
    
    # Build results with percentages
    results = []
    for choice, count in vote_counts:
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "choice": choice,
            "count": count,
            "percentage": round(percentage, 2)
        })
    
    # Sort results by count (highest first)
    results.sort(key=lambda x: x['count'], reverse=True)
    
    return {
        "election_id": election.id,
        "election_title": election.title,
        "total_votes": total_votes,
        "results": results
    }

@router.get("/{election_id}", response_model=ElectionResponse)
def get_election_public_info(election_id: int, db: Session = Depends(get_db)):
    """
    Get public information about an election
    Does not require authentication
    """
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    return election

@router.get("/{election_id}/stats")
def get_election_stats(election_id: int, db: Session = Depends(get_db)):
    """
    Get statistics about an election
    Includes registration count, vote count, and participation rate
    """
    # Find the election
    election = db.query(Election).filter(Election.id == election_id).first()
    
    if not election:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Election not found"
        )
    
    # Get vote count
    vote_count = db.query(func.count(Vote.id)).filter(
        Vote.election_id == election_id
    ).scalar()
    
    stats = {
        "election_id": election.id,
        "title": election.title,
        "type": election.type.value,
        "total_votes": vote_count,
        "start_time": election.start_time,
        "end_time": election.end_time
    }
    
    # Add registration stats for secured elections
    if election.type.value == "secured":
        registration_count = db.query(func.count(Registration.id)).filter(
            Registration.election_id == election_id
        ).scalar()
        
        voted_count = db.query(func.count(Registration.id)).filter(
            Registration.election_id == election_id,
            Registration.has_voted == True
        ).scalar()
        
        participation_rate = (voted_count / registration_count * 100) if registration_count > 0 else 0
        
        stats.update({
            "total_registered": registration_count,
            "voters_who_voted": voted_count,
            "participation_rate": round(participation_rate, 2)
        })
    
    return stats

@router.get("/", response_model=List[ElectionResponse])
def get_all_elections(db: Session = Depends(get_db)):
    """
    Get list of all elections
    Public endpoint for browsing available elections
    """
    elections = db.query(Election).order_by(Election.created_at.desc()).all()
    return elections