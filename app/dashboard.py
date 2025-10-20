"""Dashboard routes - Hospital and doctor metrics"""
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_doctor
from app.db import get_connection
from datetime import date, datetime, timedelta

router = APIRouter()

@router.get("/hospital-metrics")
def get_hospital_metrics():
    """Get hospital-wide metrics for dashboard"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        today = date.today()
        
        # Get or create today's metrics
        cur.execute("""
            SELECT or_utilization_percentage, total_patients_count, total_surgeries_count,
                   completed_surgeries_count, avg_wait_time_minutes
            FROM dashboard_metrics
            WHERE metric_date = %s
        """, (today,))
        
        result = cur.fetchone()
        
        if result:
            return {
                "or_utilization_percentage": float(result[0]) if result[0] else 0,
                "total_patients_today": result[1],
                "total_surgeries_today": result[2],
                "completed_surgeries": result[3],
                "avg_wait_time_minutes": result[4],
                "date": today
            }
        
        # Calculate metrics if not exists
        cur.execute("SELECT COUNT(*) FROM patients WHERE status = 'active'")
        total_patients = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM surgeries WHERE scheduled_date = %s", (today,))
        total_surgeries = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM surgeries WHERE scheduled_date = %s AND status = 'completed'", (today,))
        completed = cur.fetchone()[0]
        
        # Calculate OR utilization
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'in_use' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100
            FROM operating_rooms
        """)
        or_util = cur.fetchone()[0] or 0
        
        return {
            "or_utilization_percentage": round(float(or_util), 2),
            "total_patients_today": total_patients,
            "total_surgeries_today": total_surgeries,
            "completed_surgeries": completed,
            "avg_wait_time_minutes": 17,
            "date": today
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/doctor-metrics")
def get_doctor_metrics(current_doctor: dict = Depends(get_current_doctor)):
    """Get current doctor's usage statistics"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        doctor_id = current_doctor["id"]
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        # Notes taken today
        cur.execute("""
            SELECT COUNT(*) FROM notes 
            WHERE doctor_id = %s AND DATE(created_at) = %s
        """, (doctor_id, today))
        notes_today = cur.fetchone()[0]
        
        # Notes taken this week
        cur.execute("""
            SELECT COUNT(*) FROM notes 
            WHERE doctor_id = %s AND DATE(created_at) >= %s
        """, (doctor_id, week_ago))
        notes_week = cur.fetchone()[0]
        
        # Patients seen today
        cur.execute("""
            SELECT COUNT(DISTINCT patient_id) FROM notes 
            WHERE doctor_id = %s AND DATE(created_at) = %s
        """, (doctor_id, today))
        patients_today = cur.fetchone()[0]
        
        # Upcoming surgeries
        cur.execute("""
            SELECT COUNT(*) FROM surgeries 
            WHERE doctor_id = %s AND scheduled_date >= %s AND status = 'scheduled'
        """, (doctor_id, today))
        upcoming = cur.fetchone()[0]
        
        # Total recordings
        cur.execute("""
            SELECT COUNT(*) FROM transcriptions 
            WHERE doctor_id = %s
        """, (doctor_id,))
        total_recordings = cur.fetchone()[0]
        
        return {
            "doctor_id": doctor_id,
            "notes_taken_today": notes_today,
            "notes_taken_this_week": notes_week,
            "patients_seen_today": patients_today,
            "upcoming_surgeries": upcoming,
            "total_recordings": total_recordings,
            "date": today
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()