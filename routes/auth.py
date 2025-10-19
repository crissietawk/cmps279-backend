"""
Authentication routes - Login, refresh, profile
"""
from fastapi import APIRouter, HTTPException, Depends, status
from app.models import LoginRequest, LoginResponse, RefreshRequest, TokenResponse, DoctorUpdate
from app.auth import verify_password, create_access_token, create_refresh_token, verify_token, get_password_hash
from app.dependencies import get_current_doctor
from app.db import get_connection
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """Login with email and password"""
    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, first_name, last_name, email, password_hash, specialization, status
            FROM doctors
            WHERE email = %s
        """, (credentials.email,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        doctor_id, first_name, last_name, email, password_hash, specialization, status_val = result
        if status_val != 'active':
            raise HTTPException(status_code=403, detail="Account is inactive")
        if not password_hash or not verify_password(credentials.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        access_token = create_access_token(data={"sub": str(doctor_id), "email": email})
        refresh_token = create_refresh_token(data={"sub": str(doctor_id)})
        expires_at = datetime.utcnow() + timedelta(days=7)
        cur.execute("""
            INSERT INTO refresh_tokens (doctor_id, token, expires_at)
            VALUES (%s, %s, %s)
        """, (str(doctor_id), refresh_token, expires_at))
        conn.commit()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "doctor": {
                "id": str(doctor_id),
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "specialization": specialization
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur: cur.close()
        if conn: conn.close()

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token"""
    conn = cur = None
    try:
        payload = verify_token(request.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        doctor_id = payload.get("sub")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT expires_at FROM refresh_tokens
            WHERE doctor_id = %s AND token = %s AND expires_at > NOW()
        """, (doctor_id, request.refresh_token))
        if not cur.fetchone():
            raise HTTPException(status_code=401, detail="Refresh token expired or invalid")
        cur.execute("SELECT email FROM doctors WHERE id = %s", (doctor_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Doctor not found")
        access_token = create_access_token(data={"sub": doctor_id, "email": result[0]})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur: cur.close()
        if conn: conn.close()

@router.post("/logout")
def logout(current_doctor: dict = Depends(get_current_doctor)):
    """Logout - invalidate refresh tokens"""
    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM refresh_tokens WHERE doctor_id = %s", (current_doctor["id"],))
        conn.commit()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur: cur.close()
        if conn: conn.close()

@router.get("/me")
def get_current_user(current_doctor: dict = Depends(get_current_doctor)):
    """Get current logged-in doctor info"""
    return current_doctor

@router.put("/profile")
def update_profile(updates: DoctorUpdate, current_doctor: dict = Depends(get_current_doctor)):
    """Update current doctor's profile"""
    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        update_fields, params = [], []
        if updates.first_name:
            update_fields.append("first_name = %s")
            params.append(updates.first_name)
        if updates.last_name:
            update_fields.append("last_name = %s")
            params.append(updates.last_name)
        if updates.email:
            update_fields.append("email = %s")
            params.append(updates.email)
        if updates.phone:
            update_fields.append("phone = %s")
            params.append(updates.phone)
        if updates.specialization:
            update_fields.append("specialization = %s")
            params.append(updates.specialization)
        if updates.profile_image_url:
            update_fields.append("profile_image_url = %s")
            params.append(updates.profile_image_url)
        if updates.password:
            update_fields.append("password_hash = %s")
            params.append(get_password_hash(updates.password))
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        params.append(current_doctor["id"])
        query = f"""
            UPDATE doctors 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, first_name, last_name, email, phone, specialization, profile_image_url
        """
        cur.execute(query, params)
        result = cur.fetchone()
        conn.commit()
        return {
            "id": str(result[0]),
            "first_name": result[1],
            "last_name": result[2],
            "email": result[3],
            "phone": result[4],
            "specialization": result[5],
            "profile_image_url": result[6]
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur: cur.close()
        if conn: conn.close()
