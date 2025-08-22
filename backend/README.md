# Fitness API - Simple Backend

Before this can be used, you must create a .env file.
DB_HOST={public IP address of SQL database}
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres


A basic FastAPI backend for fitness tracking. This is a minimal implementation that we'll build upon.

## Features

- Basic user management
- Activity tracking
- Simple in-memory storage
- RESTful API endpoints
- Auto-generated API documentation
- GCP SQL Server connection testing

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment (optional):**
   ```bash
   cp env_example.txt .env
   # Edit .env with your GCP SQL Server credentials
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## API Endpoints

### Database Connection
- `GET /test-connection` - Test GCP SQL Server connection
- `GET /connection-info` - Get database connection info (without testing)

### Users
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get specific user
- `POST /users` - Create new user

### Activities
- `GET /activities` - Get all activities
- `GET /activities?user_id={user_id}` - Get activities for specific user
- `GET /activities/{activity_id}` - Get specific activity
- `POST /activities` - Create new activity

### Other
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /strava/connect` - Strava integration placeholder

## Database Connection Setup

To test your GCP SQL Server connection:

1. **Update your `.env` file with your GCP SQL Server credentials:**
   ```env
   DB_HOST=your-gcp-sql-server-host
   DB_PORT=1433
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```

2. **Test the connection:**
   ```bash
   curl http://localhost:8000/test-connection
   ```

3. **Check connection info:**
   ```bash
   curl http://localhost:8000/connection-info
   ```

## Example Usage

### Test database connection:
```bash
curl http://localhost:8000/test-connection
```

### Create a user:
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"id": 3, "name": "Bob Wilson", "email": "bob@example.com"}'
```

### Create an activity:
```bash
curl -X POST "http://localhost:8000/activities" \
  -H "Content-Type: application/json" \
  -d '{"id": 4, "user_id": 1, "type": "running", "distance": 3.5, "duration": 1200, "date": "2024-01-17"}'
```

### Get activities for user 1:
```bash
curl "http://localhost:8000/activities?user_id=1"
```

## Prerequisites for Database Connection

- **ODBC Driver 17 for SQL Server** must be installed on your system
- **GCP SQL Server instance** must be running and accessible
- **Network connectivity** to your GCP SQL Server instance

### Installing ODBC Driver (if needed):

**Windows:**
- Download from Microsoft's website
- Or use: `pip install pyodbc`

**macOS:**
```bash
brew install microsoft/mssql-release/mssql-tools
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

## Next Steps

This is a minimal implementation. We can add:

1. **Database integration** (replace in-memory storage with SQL Server)
2. **Authentication & authorization**
3. **Strava API integration**
4. **More complex data models**
5. **Background tasks**
6. **Testing**

Let me know what you'd like to add next! 
