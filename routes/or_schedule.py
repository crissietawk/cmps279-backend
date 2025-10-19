"""OR Schedule routes - Calendar and booking"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_doctor
from app.db import get_connection
from app.models import ORBookingRequest
from datetime import date, datetime, time, timedelta
import calendar
import json

router = APIRouter()

@router.get("/calendar/month/{year}/{month}")
def get_month_availability(year: int, month: int, current_doctor: dict = Depends(get_current_doctor)):
    """Get available days in a month"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get number of days in month
        num_days = calendar.monthrange(year, month)[1]
        
        # Get days with surgeries
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)
        
        cur.execute("""
            SELECT DISTINCT scheduled_date, COUNT(*) as surgery_count
            FROM surgeries
            WHERE scheduled_date BETWEEN %s AND %s
            GROUP BY scheduled_date
        """, (start_date, end_date))
        
        surgery_counts = {row[0]: row[1] for row in cur.fetchall()}
        
        # Build response
        days = []
        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            surgery_count = surgery_counts.get(current_date, 0)
            
            days.append({
                "date": current_date,
                "day": day,
                "has_surgeries": surgery_count > 0,
                "surgery_count": surgery_count,
                "is_past": current_date < date.today()
            })
        
        return {
            "year": year,
            "month": month,
            "days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/or-schedule/day/{schedule_date}")
def get_day_schedule(schedule_date: date, current_doctor: dict = Depends(get_current_doctor)):
    """Get OR schedule for a specific day with time slots"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get all operating rooms
        cur.execute("SELECT id, room_number, status FROM operating_rooms ORDER BY room_number")
        rooms = cur.fetchall()
        
        # Get all surgeries for this day
        cur.execute("""
            SELECT s.scheduled_time, s.procedure_name, s.status,
                   p.first_name, p.last_name, p.patient_code,
                   o.room_number, s.id
            FROM surgeries s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN operating_rooms o ON s.operating_room_id = o.id
            WHERE s.scheduled_date = %s
            ORDER BY s.scheduled_time
        """, (schedule_date,))
        
        surgeries = cur.fetchall()
        
        # Build time slots (7 AM to 7 PM, hourly)
        slots = []
        for hour in range(7, 20):
            slot_time = time(hour, 0)
            
            # Build OR status for this time slot
            or_rooms = {}
            for room in rooms:
                room_id = str(room[0])
                room_number = room[1]
                
                # Find surgery in this room at this time
                surgery_at_time = None
                for surgery in surgeries:
                    if surgery[6] == room_number and surgery[0] == slot_time:
                        surgery_at_time = surgery
                        break
                
                if surgery_at_time:
                    or_rooms[f"or_{room_number}"] = {
                        "status": "occupied",
                        "patient_name": f"{surgery_at_time[3]} {surgery_at_time[4]}",
                        "patient_code": surgery_at_time[5],
                        "procedure": surgery_at_time[1],
                        "surgery_status": surgery_at_time[2],
                        "surgery_id": str(surgery_at_time[7])
                    }
                else:
                    or_rooms[f"or_{room_number}"] = {
                        "status": "available",
                        "patient_name": None,
                        "patient_code": None,
                        "procedure": None
                    }
            
            slots.append({
                "time": str(slot_time)[:5],  # HH:MM format
                "or_rooms": or_rooms
            })
        
        return {
            "date": schedule_date,
            "time_slots": slots
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.post("/or-schedule/book")
def book_operating_room(booking: ORBookingRequest, current_doctor: dict = Depends(get_current_doctor)):
    """Book an operating room (creates a surgery)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if OR is available at this time
        cur.execute("""
            SELECT id FROM surgeries
            WHERE operating_room_id = %s 
            AND scheduled_date = %s 
            AND scheduled_time = %s
            AND status NOT IN ('cancelled', 'completed')
        """, (booking.operating_room_id, booking.scheduled_date, booking.scheduled_time))
        
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Operating room not available at this time")
        
        # Create surgery
        cur.execute("""
            INSERT INTO surgeries (
                patient_id, doctor_id, operating_room_id, procedure_name,
                scheduled_date, scheduled_time, estimated_duration_minutes,
                status, urgency_level, participants
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, procedure_name, scheduled_date, scheduled_time
        """, (
            booking.patient_id, current_doctor["id"], booking.operating_room_id,
            booking.procedure_name, booking.scheduled_date, booking.scheduled_time,
            booking.estimated_duration_minutes or 60, 'scheduled', booking.urgency_level or 'routine',
            json.dumps(booking.participants) if booking.participants else None
        ))
        
        result = cur.fetchone()
        
        # Update OR status
        cur.execute("""
            UPDATE operating_rooms 
            SET status = 'reserved' 
            WHERE id = %s
        """, (booking.operating_room_id,))
        
        conn.commit()
        
        return {
            "surgery_id": str(result[0]),
            "procedure_name": result[1],
            "scheduled_date": result[2],
            "scheduled_time": str(result[3]),
            "message": "Operating room booked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()