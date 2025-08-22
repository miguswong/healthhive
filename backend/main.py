from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from db_connection import test_gcp_postgres_connection, get_connection_info, initialize_database, get_db_connection
from fastapi import HTTPException
import csv
import io
from datetime import datetime

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

from fastapi import FastAPI
from db_connection import get_db_connection

app = FastAPI()
@app.on_event("startup")
def _log_db_target():
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("select current_database(), inet_server_addr()")
            db, ip = cur.fetchone()
            print(f"[DB] connected to '{db}' on {ip}")
    except Exception as e:
        print("[DB] startup check failed:", e)


# Simple data models
class User(BaseModel):
    id: int
    name: str
    email: str

class Activity(BaseModel):
    activity_id: Optional[int] = None
    user_id: int
    activity_type: str
    distance: Optional[float] = None
    distance_units: Optional[str] = None
    time: Optional[float] = None
    time_units: Optional[str] = None
    speed: Optional[float] = None
    speed_units: Optional[str] = None
    calories_burned: Optional[int] = None
    activity_date: str

class Biometrics(BaseModel):
    biometric_id: Optional[int] = None
    user_id: int
    date: str
    weight: Optional[float] = None
    avg_hr: Optional[int] = None
    high_hr: Optional[int] = None
    low_hr: Optional[int] = None
    notes: Optional[str] = None

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
        cursor.execute("""
            SELECT activity_id, user_id, activity_type, distance, distance_units, 
                   time, time_units, speed, speed_units, calories_burned, activity_date 
            FROM activities WHERE user_id = %s ORDER BY activity_date DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT activity_id, user_id, activity_type, distance, distance_units, 
                   time, time_units, speed, speed_units, calories_burned, activity_date 
            FROM activities ORDER BY activity_date DESC
        """)
    activities = []
    for row in cursor.fetchall():
        activities.append(Activity(
            activity_id=row[0],
            user_id=row[1],
            activity_type=row[2],
            distance=float(row[3]) if row[3] is not None else None,
            distance_units=row[4],
            time=float(row[5]) if row[5] is not None else None,
            time_units=row[6],
            speed=float(row[7]) if row[7] is not None else None,
            speed_units=row[8],
            calories_burned=row[9],
            activity_date=str(row[10])
        ))
    cursor.close()
    conn.close()
    return activities

@app.get("/activities/{activity_id}", response_model=Activity)
async def get_activity(activity_id: int):
    """Get a specific activity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT activity_id, user_id, activity_type, distance, distance_units, 
               time, time_units, speed, speed_units, calories_burned, activity_date 
        FROM activities WHERE activity_id = %s
    """, (activity_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return Activity(
            activity_id=row[0],
            user_id=row[1],
            activity_type=row[2],
            distance=float(row[3]) if row[3] is not None else None,
            distance_units=row[4],
            time=float(row[5]) if row[5] is not None else None,
            time_units=row[6],
            speed=float(row[7]) if row[7] is not None else None,
            speed_units=row[8],
            calories_burned=row[9],
            activity_date=str(row[10])
        )
    return {"error": "Activity not found"}

@app.post("/activities", response_model=Activity)
async def create_activity(activity: Activity):
    """Create a new activity in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activities (user_id, activity_type, distance, distance_units, 
                                  time, time_units, speed, speed_units, calories_burned, activity_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING activity_id, user_id, activity_type, distance, distance_units, 
                     time, time_units, speed, speed_units, calories_burned, activity_date
        """, (
            activity.user_id, activity.activity_type, activity.distance, activity.distance_units,
            activity.time, activity.time_units, activity.speed, activity.speed_units, 
            activity.calories_burned, activity.activity_date
        ))
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return Activity(
            activity_id=row[0],
            user_id=row[1],
            activity_type=row[2],
            distance=float(row[3]) if row[3] is not None else None,
            distance_units=row[4],
            time=float(row[5]) if row[5] is not None else None,
            time_units=row[6],
            speed=float(row[7]) if row[7] is not None else None,
            speed_units=row[8],
            calories_burned=row[9],
            activity_date=str(row[10])
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Biometrics endpoints
@app.get("/biometrics", response_model=List[Biometrics])
async def get_biometrics(user_id: Optional[int] = None):
    """Get all biometrics, optionally filtered by user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes 
            FROM biometrics WHERE user_id = %s ORDER BY date DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes 
            FROM biometrics ORDER BY date DESC
        """)
    biometrics = []
    for row in cursor.fetchall():
        biometrics.append(Biometrics(
            biometric_id=row[0],
            user_id=row[1],
            date=str(row[2]),
            weight=float(row[3]) if row[3] is not None else None,
            avg_hr=row[4],
            high_hr=row[5],
            low_hr=row[6],
            notes=row[7]
        ))
    cursor.close()
    conn.close()
    return biometrics

@app.get("/biometrics/{biometric_id}", response_model=Biometrics)
async def get_biometric(biometric_id: int):
    """Get a specific biometric entry"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes 
        FROM biometrics WHERE biometric_id = %s
    """, (biometric_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return Biometrics(
            biometric_id=row[0],
            user_id=row[1],
            date=str(row[2]),
            weight=float(row[3]) if row[3] is not None else None,
            avg_hr=row[4],
            high_hr=row[5],
            low_hr=row[6],
            notes=row[7]
        )
    return {"error": "Biometric entry not found"}

@app.post("/biometrics", response_model=Biometrics)
async def create_biometric(biometric: Biometrics):
    """Create or update a biometric entry in the database (one per user per day)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if an entry already exists for this user and date
        cursor.execute("""
            SELECT biometric_id FROM biometrics 
            WHERE user_id = %s AND date = %s
        """, (biometric.user_id, biometric.date))
        
        existing_entry = cursor.fetchone()
        
        if existing_entry:
            # Update existing entry
            cursor.execute("""
                UPDATE biometrics 
                SET weight = %s, avg_hr = %s, high_hr = %s, low_hr = %s, notes = %s
                WHERE user_id = %s AND date = %s
                RETURNING biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes
            """, (
                biometric.weight, biometric.avg_hr, biometric.high_hr, biometric.low_hr, biometric.notes,
                biometric.user_id, biometric.date
            ))
        else:
            # Insert new entry
            cursor.execute("""
                INSERT INTO biometrics (user_id, date, weight, avg_hr, high_hr, low_hr, notes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) 
                RETURNING biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes
            """, (
                biometric.user_id, biometric.date, biometric.weight, biometric.avg_hr,
                biometric.high_hr, biometric.low_hr, biometric.notes
            ))
        
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return Biometrics(
            biometric_id=row[0],
            user_id=row[1],
            date=str(row[2]),
            weight=float(row[3]) if row[3] is not None else None,
            avg_hr=row[4],
            high_hr=row[5],
            low_hr=row[6],
            notes=row[7]
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

@app.post("/load-activity-data")
async def load_activity_data():
    """Load activity data from CSV file into the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read CSV file
        csv_file_path = "fakeData/activityData.csv"
        activities_loaded = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Skip if activity_id already exists
                cursor.execute("SELECT activity_id FROM activities WHERE activity_id = %s", (int(row['activity_id']),))
                if cursor.fetchone():
                    continue
                
                # Parse date
                activity_date = datetime.strptime(row['activity_date'], '%m/%d/%Y').date()
                
                # Insert activity using the user_id from CSV
                cursor.execute("""
                    INSERT INTO activities (
                        activity_id, user_id, activity_date, activity_type, 
                        distance, distance_units, time, time_units, 
                        speed, speed_units, calories_burned
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    int(row['activity_id']),
                    int(row['user_id']),
                    activity_date,
                    row['activity_type'],
                    float(row['distance']) if row['distance'] else None,
                    row['distance_units'],
                    float(row['time']) if row['time'] else None,
                    row['time_units'],
                    float(row['speed']) if row['speed'] else None,
                    row['speed_units'],
                    int(row['calories_burned']) if row['calories_burned'] else None
                ))
                activities_loaded += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully loaded {activities_loaded} activities",
            "activities_loaded": activities_loaded
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/load-biometric-data")
async def load_biometric_data():
    """Load biometric data from CSV file into the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read CSV file
        csv_file_path = "fakeData/biometricData.csv"
        biometrics_loaded = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Skip if biometric_id already exists
                cursor.execute("SELECT biometric_id FROM biometrics WHERE biometric_id = %s", (int(row['biometric_id']),))
                if cursor.fetchone():
                    continue
                
                # Parse date
                biometric_date = datetime.strptime(row['date'], '%m/%d/%Y').date()
                
                # Insert biometric using the user_id from CSV
                cursor.execute("""
                    INSERT INTO biometrics (
                        biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    int(row['biometric_id']),
                    int(row['user_id']),
                    biometric_date,
                    float(row['weight']) if row['weight'] else None,
                    int(row['avg_hr']) if row['avg_hr'] else None,
                    int(row['high_hr']) if row['high_hr'] else None,
                    int(row['low_hr']) if row['low_hr'] else None,
                    row['notes']
                ))
                biometrics_loaded += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully loaded {biometrics_loaded} biometric entries",
            "biometrics_loaded": biometrics_loaded
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/load-all-data")
async def load_all_data():
    """Load all data from CSV files into the database (users, activities, biometrics)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = {
            "users_loaded": 0,
            "activities_loaded": 0,
            "biometrics_loaded": 0,
            "errors": []
        }
        
        # Load users first (since activities and biometrics reference user_id)
        try:
            csv_file_path = "fakeData/userData.csv"
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Skip if user already exists
                    cursor.execute("SELECT id FROM users WHERE id = %s", (int(row['id']),))
                    if cursor.fetchone():
                        continue
                    
                    # Insert user
                    cursor.execute("""
                        INSERT INTO users (id, name, email) 
                        VALUES (%s, %s, %s)
                    """, (
                        int(row['id']),
                        row['name'],
                        row['email']
                    ))
                    results["users_loaded"] += 1
        except FileNotFoundError:
            results["errors"].append("userData.csv not found")
        except Exception as e:
            results["errors"].append(f"Error loading users: {str(e)}")
        
        # Load activities
        try:
            csv_file_path = "fakeData/activityData.csv"
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Skip if activity_id already exists
                    cursor.execute("SELECT activity_id FROM activities WHERE activity_id = %s", (int(row['activity_id']),))
                    if cursor.fetchone():
                        continue
                    
                    # Parse date
                    activity_date = datetime.strptime(row['activity_date'], '%m/%d/%Y').date()
                    
                    # Insert activity
                    cursor.execute("""
                        INSERT INTO activities (
                            activity_id, user_id, activity_date, activity_type, 
                            distance, distance_units, time, time_units, 
                            speed, speed_units, calories_burned
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        int(row['activity_id']),
                        int(row['user_id']),
                        activity_date,
                        row['activity_type'],
                        float(row['distance']) if row['distance'] else None,
                        row['distance_units'],
                        float(row['time']) if row['time'] else None,
                        row['time_units'],
                        float(row['speed']) if row['speed'] else None,
                        row['speed_units'],
                        int(row['calories_burned']) if row['calories_burned'] else None
                    ))
                    results["activities_loaded"] += 1
        except FileNotFoundError:
            results["errors"].append("activityData.csv not found")
        except Exception as e:
            results["errors"].append(f"Error loading activities: {str(e)}")
        
        # Load biometrics
        try:
            csv_file_path = "fakeData/biometricData.csv"
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Skip if biometric_id already exists
                    cursor.execute("SELECT biometric_id FROM biometrics WHERE biometric_id = %s", (int(row['biometric_id']),))
                    if cursor.fetchone():
                        continue
                    
                    # Parse date
                    biometric_date = datetime.strptime(row['date'], '%m/%d/%Y').date()
                    
                    # Insert biometric
                    cursor.execute("""
                        INSERT INTO biometrics (
                            biometric_id, user_id, date, weight, avg_hr, high_hr, low_hr, notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        int(row['biometric_id']),
                        int(row['user_id']),
                        biometric_date,
                        float(row['weight']) if row['weight'] else None,
                        int(row['avg_hr']) if row['avg_hr'] else None,
                        int(row['high_hr']) if row['high_hr'] else None,
                        int(row['low_hr']) if row['low_hr'] else None,
                        row['notes']
                    ))
                    results["biometrics_loaded"] += 1
        except FileNotFoundError:
            results["errors"].append("biometricData.csv not found")
        except Exception as e:
            results["errors"].append(f"Error loading biometrics: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Determine success status
        total_loaded = results["users_loaded"] + results["activities_loaded"] + results["biometrics_loaded"]
        success = len(results["errors"]) == 0
        
        return {
            "success": success,
            "message": f"Loaded {total_loaded} total records",
            "details": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 