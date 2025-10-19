"""
FastAPI dependencies for authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import verify_token
from app.db import get_connection
from typing import Optional

security = HTTPBearer()

def get_current_doctor(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    doctor_id = payload.get("sub")
    if doctor_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, first_name, last_name, email, specialization, status
            FROM doctors
            WHERE id = %s AND status = 'active'
        """, (doctor_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Doctor not found or inactive")
        return {
            "id": str(result[0]),
            "first_name": result[1],
            "last_name": result[2],
            "email": result[3],
            "specialization": result[4],
            "status": result[5]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_current_doctor_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    try:
        return get_current_doctor(credentials)
    except HTTPException:
        return None
