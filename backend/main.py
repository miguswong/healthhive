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
    weight_units: Optional[str] = None
    avg_hr: Optional[int] = None
    high_hr: Optional[int] = None
    low_hr: Optional[int] = None
    notes: Optional[str] = None

class ExerciseDefinition(BaseModel):
    exercise_id: Optional[int] = None
    exercise_name: str
    avg_met_value: float

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
    """Create a new activity in the database with automatic calorie calculation"""
    try:
        # Calculate calories burned automatically
        calculated_calories = None
        if activity.time and activity.activity_type:
            # Get user's weight in kg
            weight_kg = get_user_weight_kg(activity.user_id, activity.activity_date)
            
            # Convert time to hours
            time_hours = 0.0
            if activity.time_units:
                if activity.time_units.lower() in ['minutes', 'min']:
                    time_hours = activity.time / 60.0
                elif activity.time_units.lower() in ['hours', 'hr']:
                    time_hours = activity.time
                elif activity.time_units.lower() in ['seconds', 'sec']:
                    time_hours = activity.time / 3600.0
                else:
                    time_hours = activity.time / 60.0  # Default to minutes
            
            # Calculate calories burned
            calculated_calories = calculate_calories_burned(activity.activity_type, weight_kg, time_hours)
        
        # Use calculated calories if available, otherwise use provided calories
        final_calories = calculated_calories if calculated_calories is not None else activity.calories_burned
        
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
            final_calories, activity.activity_date
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
            SELECT biometric_id, user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes 
            FROM biometrics WHERE user_id = %s ORDER BY date DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT biometric_id, user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes 
            FROM biometrics ORDER BY date DESC
        """)
    biometrics = []
    for row in cursor.fetchall():
        biometrics.append(Biometrics(
            biometric_id=row[0],
            user_id=row[1],
            date=str(row[2]),
            weight=float(row[3]) if row[3] is not None else None,
            weight_units=row[4],
            avg_hr=row[5],
            high_hr=row[6],
            low_hr=row[7],
            notes=row[8]
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
        SELECT biometric_id, user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes 
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
            weight_units=row[4],
            avg_hr=row[5],
            high_hr=row[6],
            low_hr=row[7],
            notes=row[8]
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
                SET weight = %s, weight_units = %s, avg_hr = %s, high_hr = %s, low_hr = %s, notes = %s
                WHERE user_id = %s AND date = %s
                RETURNING biometric_id, user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes
            """, (
                biometric.weight, biometric.weight_units, biometric.avg_hr, biometric.high_hr, biometric.low_hr, biometric.notes,
                biometric.user_id, biometric.date
            ))
        else:
            # Insert new entry
            cursor.execute("""
                INSERT INTO biometrics (user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING biometric_id, user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes
            """, (
                biometric.user_id, biometric.date, biometric.weight, biometric.weight_units, biometric.avg_hr,
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
            weight_units=row[4],
            avg_hr=row[5],
            high_hr=row[6],
            low_hr=row[7],
            notes=row[8]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def calculate_calories_burned(activity_type: str, weight_kg: float, time_hours: float) -> int:
    """Calculate calories burned using MET values and user weight"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get MET value for the activity type
        cursor.execute("""
            SELECT avg_met_value FROM exercise_definitions 
            WHERE LOWER(exercise_name) = LOWER(%s)
        """, (activity_type,))
        
        met_row = cursor.fetchone()
        if met_row:
            met_value = float(met_row[0])
        else:
            # Default to Miscellaneous if no match found
            cursor.execute("SELECT avg_met_value FROM exercise_definitions WHERE exercise_name = 'Miscellaneous'")
            met_row = cursor.fetchone()
            met_value = float(met_row[0]) if met_row else 2.0
        
        cursor.close()
        conn.close()
        
        # Calculate calories: MET × weight (kg) × time (hours)
        calories = int(met_value * weight_kg * time_hours)
        return calories
        
    except Exception as e:
        # Fallback calculation if database lookup fails
        return int(2.0 * weight_kg * time_hours)  # Default MET of 2.0

def get_user_weight_kg(user_id: int, activity_date: str) -> float:
    """Get user's weight in kg for a given date"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the most recent weight entry for the user on or before the activity date
        cursor.execute("""
            SELECT weight, weight_units FROM biometrics 
            WHERE user_id = %s AND date <= %s 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id, activity_date))
        
        weight_row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if weight_row and weight_row[0]:
            weight = float(weight_row[0])
            weight_units = weight_row[1] if weight_row[1] else 'lbs'
            
            # Convert to kg if needed
            if weight_units.lower() in ['lbs', 'lb', 'pounds']:
                return weight * 0.453592  # Convert lbs to kg
            elif weight_units.lower() in ['kg', 'kilograms']:
                return weight
            else:
                return weight  # Assume kg if units unknown
        
        return 70.0  # Default weight in kg if no data found
        
    except Exception as e:
        return 70.0  # Default weight in kg if error occurs

# Exercise Definitions endpoints
@app.get("/exercise-definitions", response_model=List[ExerciseDefinition])
async def get_exercise_definitions():
    """Get all exercise definitions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT exercise_id, exercise_name, avg_met_value 
        FROM exercise_definitions ORDER BY exercise_id
    """)
    exercise_definitions = []
    for row in cursor.fetchall():
        exercise_definitions.append(ExerciseDefinition(
            exercise_id=row[0],
            exercise_name=row[1],
            avg_met_value=float(row[2])
        ))
    cursor.close()
    conn.close()
    return exercise_definitions

@app.get("/exercise-definitions/{exercise_id}", response_model=ExerciseDefinition)
async def get_exercise_definition(exercise_id: int):
    """Get a specific exercise definition"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT exercise_id, exercise_name, avg_met_value 
        FROM exercise_definitions WHERE exercise_id = %s
    """, (exercise_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return ExerciseDefinition(
            exercise_id=row[0],
            exercise_name=row[1],
            avg_met_value=float(row[2])
        )
    return {"error": "Exercise definition not found"}

@app.post("/exercise-definitions", response_model=ExerciseDefinition)
async def create_exercise_definition(exercise_definition: ExerciseDefinition):
    """Create a new exercise definition in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO exercise_definitions (exercise_name, avg_met_value) 
            VALUES (%s, %s) 
            RETURNING exercise_id, exercise_name, avg_met_value
        """, (
            exercise_definition.exercise_name,
            exercise_definition.avg_met_value
        ))
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return ExerciseDefinition(
            exercise_id=row[0],
            exercise_name=row[1],
            avg_met_value=float(row[2])
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
    """Load sample activity data from CSV file into the database. This endpoint loads sample/demo fitness activity data for testing and development purposes."""
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
            "message": f"Successfully loaded {activities_loaded} sample activities",
            "activities_loaded": activities_loaded,
            "note": "This is sample/demo data for testing purposes"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/load-user-data")
async def load_user_data():
    """Load sample user data from CSV file into the database. This endpoint loads sample/demo user data for testing and development purposes."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read CSV file
        csv_file_path = "fakeData/userData.csv"
        users_loaded = 0
        
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
                users_loaded += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully loaded {users_loaded} sample users",
            "users_loaded": users_loaded,
            "note": "This is sample/demo data for testing purposes"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/load-biometric-data")
async def load_biometric_data():
    """Load sample biometric data from CSV file into the database. This endpoint loads sample/demo health metrics data for testing and development purposes."""
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
            "message": f"Successfully loaded {biometrics_loaded} sample biometric entries",
            "biometrics_loaded": biometrics_loaded,
            "note": "This is sample/demo data for testing purposes"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/load-all-data")
async def load_all_data():
    """Load all sample data from CSV files into the database (users, activities, biometrics). This endpoint loads sample/demo data for testing and development purposes."""
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
                            biometric_id, user_id, date, weight, weight_units, avg_hr, high_hr, low_hr, notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        int(row['biometric_id']),
                        int(row['user_id']),
                        biometric_date,
                        float(row['weight']) if row['weight'] else None,
                        row['weight_units'],
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
            "message": f"Loaded {total_loaded} total sample records",
            "details": results,
            "note": "This is sample/demo data for testing purposes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/load-exercise-definitions")
async def load_exercise_definitions():
    """Load exercise definitions from CSV file into the database. This endpoint loads exercise types and their MET values for calorie calculations."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read CSV file
        csv_file_path = "fakeData/exerciseDefinitions.csv"
        definitions_loaded = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Skip if exercise_id already exists
                cursor.execute("SELECT exercise_id FROM exercise_definitions WHERE exercise_id = %s", (int(row['exercise_id']),))
                if cursor.fetchone():
                    continue
                
                # Insert exercise definition
                cursor.execute("""
                    INSERT INTO exercise_definitions (
                        exercise_id, exercise_name, avg_met_value
                    ) VALUES (%s, %s, %s)
                """, (
                    int(row['exercise_id']),
                    row['exercise_name'],
                    float(row['avg_met_value'])
                ))
                definitions_loaded += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully loaded {definitions_loaded} exercise definitions",
            "definitions_loaded": definitions_loaded,
            "note": "Exercise definitions loaded for calorie calculations"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 