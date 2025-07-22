from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from db_connection import test_gcp_postgres_connection, get_connection_info, initialize_database, get_db_connection
from fastapi import HTTPException

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Fitness API",
    description="A simple fitness tracking API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data models
class User(BaseModel):
    id: int
    name: str
    email: str

class Activity(BaseModel):
    id: int
    user_id: int
    type: str
    distance: float
    duration: int
    date: str

# Basic endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Fitness API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/test-connection")
async def test_connection():
    """Test GCP PostgreSQL connection"""
    return test_gcp_postgres_connection()

@app.get("/connection-info")
async def get_db_info():
    """Get database connection information (without testing)"""
    return get_connection_info()

@app.post("/init-database")
async def init_database():
    """Initialize database tables"""
    return initialize_database()

# User endpoints
@app.get("/users", response_model=List[User])
async def get_users():
    """Get all users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users ORDER BY id")
    users = []
    for row in cursor.fetchall():
        users.append(User(id=row[0], name=row[1], email=row[2]))
    cursor.close()
    conn.close()
    return users

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return User(id=row[0], name=row[1], email=row[2])
    return {"error": "User not found"}

@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at",
            (user.name, user.email)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return User(id=row[0], name=row[1], email=row[2])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Activity endpoints
@app.get("/activities", response_model=List[Activity])
async def get_activities(user_id: Optional[int] = None):
    """Get all activities, optionally filtered by user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT id, user_id, type, distance, duration, date FROM activities WHERE user_id = %s ORDER BY date DESC", (user_id,))
    else:
        cursor.execute("SELECT id, user_id, type, distance, duration, date FROM activities ORDER BY date DESC")
    activities = []
    for row in cursor.fetchall():
        activities.append(Activity(id=row[0], user_id=row[1], type=row[2], distance=float(row[3]) if row[3] is not None else None, duration=row[4], date=str(row[5])))
    cursor.close()
    conn.close()
    return activities

@app.get("/activities/{activity_id}", response_model=Activity)
async def get_activity(activity_id: int):
    """Get a specific activity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, type, distance, duration, date FROM activities WHERE id = %s", (activity_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return Activity(id=row[0], user_id=row[1], type=row[2], distance=float(row[3]) if row[3] is not None else None, duration=row[4], date=str(row[5]))
    return {"error": "Activity not found"}

@app.post("/activities", response_model=Activity)
async def create_activity(activity: Activity):
    """Create a new activity in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (user_id, type, distance, duration, date) VALUES (%s, %s, %s, %s, %s) RETURNING id, user_id, type, distance, duration, date, created_at",
            (activity.user_id, activity.type, activity.distance, activity.duration, activity.date)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return Activity(
            id=row[0],
            user_id=row[1],
            type=row[2],
            distance=float(row[3]) if row[3] is not None else None,
            duration=row[4],
            date=str(row[5])
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Simple Strava integration endpoint (placeholder)
@app.get("/strava/connect")
async def connect_strava():
    """Placeholder for Strava connection"""
    return {
        "message": "Strava integration coming soon!",
        "client_id": os.getenv("STRAVA_CLIENT_ID", "not configured")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 