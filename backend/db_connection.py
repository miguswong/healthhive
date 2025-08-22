import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

# Load environment variables
load_dotenv()

# def get_db_connection():
#     """
#     Get a database connection
#     """
#     host = os.getenv('DB_HOST')
#     port = os.getenv('DB_PORT', '5432')
#     database = os.getenv('DB_NAME')
#     username = os.getenv('DB_USER')
#     password = os.getenv('DB_PASSWORD')
    
#     return psycopg2.connect(
#         host=host,
#         port=port,
#         database=database,
#         user=username,
#         password=password
#     )

def get_db_connection():
    """
    Open a psycopg2 connection.
    Prefers DATABASE_URL (full DSN), falls back to DB_* env vars.
    """
    url = os.getenv("DATABASE_URL")
    sslmode = None

    if url:
        # Parse DATABASE_URL like: postgresql://user:pass@host:5432/dbname?sslmode=require
        parsed = urlparse(url)
        if parsed.scheme not in ("postgres", "postgresql"):
            raise ValueError(f"Unsupported DB scheme: {parsed.scheme}")

        q = parse_qs(parsed.query)
        sslmode = (q.get("sslmode", [None])[0]) or os.getenv("DB_SSLMODE")

        dbname = parsed.path.lstrip("/")
        if not dbname:
            raise ValueError("DATABASE_URL is missing the database name (path).")

        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            dbname=dbname,
            user=parsed.username,
            password=parsed.password,
            sslmode=sslmode or "prefer",
        )
        return conn

    # Fallback to individual env vars
    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    sslmode = os.getenv("DB_SSLMODE") or "prefer"  # use "require" if your server enforces TLS

    missing = [k for k, v in [
        ("DB_HOST", host), ("DB_NAME", dbname), ("DB_USER", user), ("DB_PASSWORD", password)
    ] if not v]
    if missing:
        raise RuntimeError(f"Missing database env vars: {', '.join(missing)}")

    return psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password, sslmode=sslmode
    )


def initialize_database():
    """
    Initialize the database by creating users and activities tables
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                activity_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                activity_date DATE NOT NULL,
                activity_type VARCHAR(100) NOT NULL,
                distance DECIMAL(10,2),
                distance_units VARCHAR(20),
                time DECIMAL(10,3),
                time_units VARCHAR(20),
                speed DECIMAL(10,2),
                speed_units VARCHAR(20),
                calories_burned INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create biometrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS biometrics (
                biometric_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                date DATE NOT NULL,
                weight DECIMAL(5,2),
                avg_hr INTEGER,
                high_hr INTEGER,
                low_hr INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Commit the changes
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': 'Database initialized successfully',
            'tables_created': ['users', 'activities', 'biometrics']
        }
        
    except psycopg2.Error as e:
        return {
            'success': False,
            'error': f'Database initialization failed: {str(e)}',
            'error_code': e.pgcode if hasattr(e, 'pgcode') else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def test_gcp_postgres_connection():
    """
    Test connection to GCP PostgreSQL
    Returns a dictionary with connection status and details
    """
    try:
        # Get database connection parameters from environment
        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME')
        username = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        
        # Check if required parameters are set
        if not all([host, database, username, password]):
            return {
                'success': False,
                'error': 'Missing database connection parameters',
                'missing_params': [param for param, value in [
                    ('DB_HOST', host), ('DB_NAME', database), 
                    ('DB_USER', username), ('DB_PASSWORD', password)
                ] if not value]
            }
        
        # Test connection
        print(f"Attempting to connect to {host}:{port}/{database}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # Get list of databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = [row[0] for row in cursor.fetchall()]
        
        # Close connection
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': 'Successfully connected to GCP PostgreSQL',
            'server_info': {
                'host': host,
                'port': port,
                'database': database,
                'version': version,
                'available_databases': databases
            }
        }
        
    except psycopg2.Error as e:
        return {
            'success': False,
            'error': f'Database connection failed: {str(e)}',
            'error_code': e.pgcode if hasattr(e, 'pgcode') else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def get_connection_info():
    """
    Get database connection information without testing the connection
    """
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password_set': bool(os.getenv('DB_PASSWORD'))
    } 
    
    def with_conn(fn, max_retries=2):
        for i in range(max_retries + 1):
            try:
                with get_db_connection() as conn, conn.cursor() as cur:
                    return fn(conn, cur)
            except OperationalError:
                if i == max_retries: raise
                time.sleep(0.5 * (i + 1))