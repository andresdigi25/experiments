"""
FastAPI implementation for the Scrum Master Bot
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Import from our core library
from scrummaster.core import ScrumMaster

# Initialize the FastAPI app
app = FastAPI(
    title="Scrum Master Bot API",
    description="RESTful API for managing daily scrum standups",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the scrum master
scrum_master = ScrumMaster()

# Define Pydantic models for request/response validation
class TeamMember(BaseModel):
    name: str

class StandupInput(BaseModel):
    name: str
    feeling: str
    yesterday: str
    today: str
    blockers: str

class TaskAnalysisInput(BaseModel):
    text: str

class StandupSummary(BaseModel):
    date: str
    members: Dict[str, Any]
    blockers_exist: bool

class TaskList(BaseModel):
    tasks: List[str]

class SentimentScore(BaseModel):
    score: float
    mood: str  # "positive", "neutral", or "negative"

# API routes

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Scrum Master Bot API",
        "version": "1.0.0",
        "endpoints": {
            "GET /team": "Get list of team members",
            "POST /team": "Add a team member",
            "DELETE /team/{name}": "Remove a team member",
            "POST /standup": "Record a standup",
            "GET /standup/summary": "Get summary of today's standup",
            "GET /standup/summary/{date}": "Get summary for a specific date",
            "GET /standup/history/{name}": "Get history for a team member",
            "POST /analyze/tasks": "Extract tasks from text",
            "POST /analyze/sentiment": "Analyze sentiment of text",
        }
    }

# Team management routes
@app.get("/team", response_model=List[str])
async def get_team_members():
    """Get list of all team members"""
    return scrum_master.get_team_members()

@app.post("/team", status_code=201)
async def add_team_member(member: TeamMember):
    """Add a new team member"""
    success = scrum_master.add_team_member(member.name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Team member '{member.name}' already exists")
    return {"message": f"Team member '{member.name}' added successfully"}

@app.delete("/team/{name}")
async def remove_team_member(name: str):
    """Remove a team member"""
    success = scrum_master.remove_team_member(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Team member '{name}' not found")
    return {"message": f"Team member '{name}' removed successfully"}

# Standup routes
@app.post("/standup", status_code=201)
async def record_standup(standup: StandupInput):
    """Record a standup for a team member"""
    if standup.name not in scrum_master.get_team_members():
        raise HTTPException(status_code=404, detail=f"Team member '{standup.name}' not found")
    
    success = scrum_master.record_standup(
        standup.name,
        standup.feeling,
        standup.yesterday,
        standup.today,
        standup.blockers
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to record standup")
    
    return {"message": f"Standup recorded for '{standup.name}'"}

@app.get("/standup/summary", response_model=StandupSummary)
async def get_today_summary():
    """Get summary of today's standup"""
    return scrum_master.get_standup_summary()

@app.get("/standup/summary/{date}", response_model=StandupSummary)
async def get_summary_by_date(date: str):
    """Get summary for a specific date (format: YYYY-MM-DD)"""
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    summary = scrum_master.get_standup_summary(date)
    return summary

@app.get("/standup/history/{name}")
async def get_member_history(name: str):
    """Get standup history for a specific team member"""
    if name not in scrum_master.get_team_members():
        raise HTTPException(status_code=404, detail=f"Team member '{name}' not found")
    
    history = scrum_master.get_member_history(name)
    return history

# Analysis routes
@app.post("/analyze/tasks", response_model=TaskList)
async def analyze_tasks(input_data: TaskAnalysisInput):
    """Extract tasks from text"""
    tasks = scrum_master.extract_tasks(input_data.text)
    return {"tasks": tasks}

@app.post("/analyze/sentiment", response_model=SentimentScore)
async def analyze_sentiment(input_data: TaskAnalysisInput):
    """Analyze sentiment of text"""
    score = scrum_master.analyze_sentiment(input_data.text)
    
    # Determine mood based on score
    if score > 0.2:
        mood = "positive"
    elif score < -0.2:
        mood = "negative"
    else:
        mood = "neutral"
    
    return {"score": score, "mood": mood}

# Bot response routes
@app.get("/bot/greeting")
async def get_greeting():
    """Get a random greeting question"""
    return {"text": scrum_master.get_greeting()}

@app.get("/bot/question/yesterday")
async def get_yesterday_question():
    """Get a random question about yesterday's work"""
    return {"text": scrum_master.get_yesterday_question()}

@app.get("/bot/question/today")
async def get_today_question():
    """Get a random question about today's plan"""
    return {"text": scrum_master.get_today_question()}

@app.get("/bot/question/blockers")
async def get_blocker_question():
    """Get a random question about blockers"""
    return {"text": scrum_master.get_blocker_question()}


def start_api():
    """Function to start the API server with uvicorn"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    start_api()