"""
FastAPI Voting System - Main Application Entry Point
Handles CORS, database initialization, and route registration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import admin, voter, election

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Secure Voting System",
    description="A secure voting system with both secured and anonymous voting options",
    version="1.0.0"
)

# Configure CORS - allows React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Register route modules
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(voter.router, prefix="/api/voter", tags=["Voter"])
app.include_router(election.router, prefix="/api/election", tags=["Election"])

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "Voting System API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)