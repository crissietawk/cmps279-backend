import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError

# Load environment variables from .env file
load_dotenv()

def get_connection():
    """
    Create and return a PostgreSQL database connection.
    Raises an exception if connection fails.
    """
    try:
        db_url = os.getenv("DB_URL")
        
        if not db_url:
            raise ValueError("DB_URL environment variable is not set. Check your .env file.")
        
        print(f"Attempting to connect to database...")
        
        # Create connection with timeout
        conn = psycopg2.connect(db_url, connect_timeout=10)
        
        print("✓ Database connection successful!")
        return conn
        
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        raise
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise

def test_connection():
    """
    Test the database connection by executing a simple query.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"Database version: {db_version[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
