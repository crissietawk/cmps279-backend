"""Doctor routes - Profile, surgeries, patients, stats"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_doctor
from app.db import get_connection
from datetime import date

router = APIRouter()

@router.get("/{doctor_id}")
def get_doctor_basic(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get basic doctor information"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, doctor_code, first_name, last_name, specialization, email, phone,
                   license_number, profile_image_url, status
            FROM doctors WHERE id = %s
        """, (doctor_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        return {
            "id": str(result[0]),
            "doctor_code": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "specialization": result[4],
            "email": result[5],
            "phone": result[6],
            "license_number": result[7],
            "profile_image_url": result[8],
            "status": result[9]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/details")
def get_doctor_details(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get full doctor details including statistics"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Basic info
        cur.execute("""
            SELECT id, doctor_code, first_name, last_name, specialization, email, phone,
                   license_number, profile_image_url, status, created_at
            FROM doctors WHERE id = %s
        """, (doctor_id,))
        
        doctor = cur.fetchone()
        
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Total surgeries
        cur.execute("SELECT COUNT(*) FROM surgeries WHERE doctor_id = %s", (doctor_id,))
        total_surgeries = cur.fetchone()[0]
        
        # Total patients
        cur.execute("SELECT COUNT(DISTINCT patient_id) FROM notes WHERE doctor_id = %s", (doctor_id,))
        total_patients = cur.fetchone()[0]
        
        # Total notes
        cur.execute("SELECT COUNT(*) FROM notes WHERE doctor_id = %s", (doctor_id,))
        total_notes = cur.fetchone()[0]
        
        # Upcoming surgeries
        cur.execute("""
            SELECT COUNT(*) FROM surgeries 
            WHERE doctor_id = %s AND scheduled_date >= %s AND status = 'scheduled'
        """, (doctor_id, date.today()))
        upcoming_surgeries = cur.fetchone()[0]
        
        return {
            "id": str(doctor[0]),
            "doctor_code": doctor[1],
            "first_name": doctor[2],
            "last_name": doctor[3],
            "specialization": doctor[4],
            "email": doctor[5],
            "phone": doctor[6],
            "license_number": doctor[7],
            "profile_image_url": doctor[8],
            "status": doctor[9],
            "created_at": doctor[10],
            "statistics": {
                "total_surgeries": total_surgeries,
                "total_patients": total_patients,
                "total_notes": total_notes,
                "upcoming_surgeries": upcoming_surgeries
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/surgeries/upcoming")
def get_doctor_upcoming_surgeries(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get upcoming surgeries for doctor"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.procedure_name, s.scheduled_date, s.scheduled_time, s.urgency_level,
                   p.first_name, p.last_name, p.patient_code,
                   o.room_number
            FROM surgeries s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN operating_rooms o ON s.operating_room_id = o.id
            WHERE s.doctor_id = %s AND s.scheduled_date >= %s AND s.status = 'scheduled'
            ORDER BY s.scheduled_date, s.scheduled_time
        """, (doctor_id, date.today()))
        
        results = cur.fetchall()
        
        surgeries = []
        for row in results:
            surgeries.append({
                "id": str(row[0]),
                "procedure_name": row[1],
                "scheduled_date": row[2],
                "scheduled_time": str(row[3]),
                "urgency_level": row[4],
                "patient_name": f"{row[5]} {row[6]}",
                "patient_code": row[7],
                "room_number": row[8]
            })
        
        return surgeries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/surgeries/cancelled")
def get_doctor_cancelled_surgeries(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get cancelled surgeries for doctor"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.procedure_name, s.scheduled_date, s.scheduled_time,
                   p.first_name, p.last_name, p.patient_code, s.updated_at
            FROM surgeries s
            JOIN patients p ON s.patient_id = p.id
            WHERE s.doctor_id = %s AND s.status = 'cancelled'
            ORDER BY s.updated_at DESC
        """, (doctor_id,))
        
        results = cur.fetchall()
        
        surgeries = []
        for row in results:
            surgeries.append({
                "id": str(row[0]),
                "procedure_name": row[1],
                "scheduled_date": row[2],
                "scheduled_time": str(row[3]),
                "patient_name": f"{row[4]} {row[5]}",
                "patient_code": row[6],
                "cancelled_at": row[7]
            })
        
        return surgeries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/surgeries/delayed")
def get_doctor_delayed_surgeries(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get delayed surgeries for doctor"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.procedure_name, s.scheduled_date, s.scheduled_time,
                   p.first_name, p.last_name, p.patient_code, s.updated_at
            FROM surgeries s
            JOIN patients p ON s.patient_id = p.id
            WHERE s.doctor_id = %s AND s.status = 'delayed'
            ORDER BY s.scheduled_date, s.scheduled_time
        """, (doctor_id,))
        
        results = cur.fetchall()
        
        surgeries = []
        for row in results:
            surgeries.append({
                "id": str(row[0]),
                "procedure_name": row[1],
                "scheduled_date": row[2],
                "scheduled_time": str(row[3]),
                "patient_name": f"{row[4]} {row[5]}",
                "patient_code": row[6],
                "delayed_at": row[7]
            })
        
        return surgeries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/surgeries/all")
def get_doctor_all_surgeries(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get all surgeries for doctor"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.procedure_name, s.scheduled_date, s.scheduled_time, s.status,
                   s.urgency_level, p.first_name, p.last_name, p.patient_code,
                   o.room_number
            FROM surgeries s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN operating_rooms o ON s.operating_room_id = o.id
            WHERE s.doctor_id = %s
            ORDER BY s.scheduled_date DESC, s.scheduled_time DESC
        """, (doctor_id,))
        
        results = cur.fetchall()
        
        surgeries = []
        for row in results:
            surgeries.append({
                "id": str(row[0]),
                "procedure_name": row[1],
                "scheduled_date": row[2],
                "scheduled_time": str(row[3]),
                "status": row[4],
                "urgency_level": row[5],
                "patient_name": f"{row[6]} {row[7]}",
                "patient_code": row[8],
                "room_number": row[9]
            })
        
        return surgeries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/patients/with-notes")
def get_doctor_patients_with_notes(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get patients with their latest notes (for carousel)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT ON (p.id)
                p.id, p.patient_code, p.first_name, p.last_name, p.profile_image_url,
                n.id as note_id, n.title, n.content, n.created_at
            FROM patients p
            JOIN notes n ON p.id = n.patient_id
            WHERE n.doctor_id = %s
            ORDER BY p.id, n.created_at DESC
            LIMIT 10
        """, (doctor_id,))
        
        results = cur.fetchall()
        
        patients = []
        for row in results:
            content = row[7]
            summary = content[:150] + "..." if content and len(content) > 150 else content
            
            patients.append({
                "patient_id": str(row[0]),
                "patient_code": row[1],
                "patient_name": f"{row[2]} {row[3]}",
                "profile_image_url": row[4],
                "latest_note": {
                    "note_id": str(row[5]),
                    "title": row[6],
                    "summary": summary,
                    "created_at": row[8]
                }
            })
        
        return patients
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{doctor_id}/stats")
def get_doctor_stats(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get doctor statistics summary"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Total surgeries by status
        cur.execute("""
            SELECT status, COUNT(*) 
            FROM surgeries 
            WHERE doctor_id = %s 
            GROUP BY status
        """, (doctor_id,))
        
        surgery_stats = {row[0]: row[1] for row in cur.fetchall()}
        
        # Total patients
        cur.execute("""
            SELECT COUNT(DISTINCT patient_id) FROM notes WHERE doctor_id = %s
        """, (doctor_id,))
        total_patients = cur.fetchone()[0]
        
        # Total notes
        cur.execute("SELECT COUNT(*) FROM notes WHERE doctor_id = %s", (doctor_id,))
        total_notes = cur.fetchone()[0]
        
        # Total recordings
        cur.execute("SELECT COUNT(*) FROM transcriptions WHERE doctor_id = %s", (doctor_id,))
        total_recordings = cur.fetchone()[0]
        
        return {
            "doctor_id": doctor_id,
            "total_patients": total_patients,
            "total_notes": total_notes,
            "total_recordings": total_recordings,
            "surgeries_by_status": surgery_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()