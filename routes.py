from fastapi import APIRouter, HTTPException
from app.db import get_connection

router = APIRouter()

@router.get("/")
def root():
    """Root endpoint to verify API is running"""
    return {
        "status": "online",
        "message": "FastAPI + Supabase API is running",
        "endpoints": {
            "test_db": "/test-db",
            "health": "/health"
        }
    }

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/test-db")
def test_db():
    """Test database connection and return current timestamp"""
    conn = None
    cur = None
    
    try:
        # Get database connection
        conn = get_connection()
        cur = conn.cursor()
        
        # Execute test query
        cur.execute("SELECT NOW(), version();")
        result = cur.fetchone()
        
        return {
            "status": "success",
            "message": "Database connection successful",
            "timestamp": str(result[0]),
            "database_version": result[1].split()[0:2]  # Just PostgreSQL version
        }
        
    except Exception as e:
        print(f"Error in test_db endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Database connection failed",
                "message": str(e)
            }
        )
    
    finally:
        # Clean up resources
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/tables")
def list_tables():
    """List all tables in the database"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query to get all tables in public schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }
        
    except Exception as e:
        print(f"Error listing tables: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to list tables",
                "message": str(e)
            }
        )
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()