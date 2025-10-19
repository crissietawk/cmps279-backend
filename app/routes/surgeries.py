"""Surgery routes - CRUD and status management"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models import SurgeryCreate, SurgeryUpdate, SurgeryResponse, StatusUpdate
from app.dependencies import get_current_doctor
from app.db import get_connection
from datetime import date
import json

router = APIRouter()

@router.get("/", response_model=List[SurgeryResponse])
def get_surgeries(
    status: Optional[str] = Query(None),
    schedule_date: Optional[date] = Query(None),
    doctor_id: Optional[str] = Query(None),
    current_doctor: dict = Depends(get_current_doctor)
):
    """Get surgeries with filters"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT s.id, s.patient_id, s.doctor_id, s.operating_room_id, s.procedure_name,
                   s.scheduled_date, s.scheduled_time, s.estimated_duration_minutes, s.actual_start_time,
                   s.actual_end_time, s.status, s.urgency_level, s.notes, s.participants, s.created_at, s.updated_at
            FROM surgeries s WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if schedule_date:
            query += " AND scheduled_date = %s"
            params.append(schedule_date)
        
        if doctor_id:
            query += " AND doctor_id = %s"
            params.append(doctor_id)
        
        query += " ORDER BY scheduled_date DESC, scheduled_time DESC LIMIT 100"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        surgeries = []
        for row in results:
            surgeries.append({
                "id": str(row[0]), "patient_id": str(row[1]), "doctor_id": str(row[2]),
                "operating_room_id": str(row[3]) if row[3] else None, "procedure_name": row[4],
                "scheduled_date": row[5], "scheduled_time": str(row[6]) if row[6] else None,
                "estimated_duration_minutes": row[7], "actual_start_time": row[8],
                "actual_end_time": row[9], "status": row[10], "urgency_level": row[11],
                "notes": row[12], "participants": row[13], "created_at": row[14], "updated_at": row[15]
            })
        
        return surgeries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{surgery_id}", response_model=SurgeryResponse)
def get_surgery(surgery_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get specific surgery details"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, patient_id, doctor_id, operating_room_id, procedure_name,
                   scheduled_date, scheduled_time, estimated_duration_minutes, actual_start_time,
                   actual_end_time, status, urgency_level, notes, participants, created_at, updated_at
            FROM surgeries WHERE id = %s
        """, (surgery_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        return {
            "id": str(result[0]), "patient_id": str(result[1]), "doctor_id": str(result[2]),
            "operating_room_id": str(result[3]) if result[3] else None, "procedure_name": result[4],
            "scheduled_date": result[5], "scheduled_time": str(result[6]) if result[6] else None,
            "estimated_duration_minutes": result[7], "actual_start_time": result[8],
            "actual_end_time": result[9], "status": result[10], "urgency_level": result[11],
            "notes": result[12], "participants": result[13], "created_at": result[14], "updated_at": result[15]
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

@router.post("/", response_model=SurgeryResponse, status_code=201)
def create_surgery(surgery: SurgeryCreate, current_doctor: dict = Depends(get_current_doctor)):
    """Create a new surgery"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO surgeries (
                patient_id, doctor_id, operating_room_id, procedure_name,
                scheduled_date, scheduled_time, estimated_duration_minutes,
                status, urgency_level, notes, participants
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, patient_id, doctor_id, operating_room_id, procedure_name,
                      scheduled_date, scheduled_time, estimated_duration_minutes, actual_start_time,
                      actual_end_time, status, urgency_level, notes, participants, created_at, updated_at
        """, (
            surgery.patient_id, surgery.doctor_id, surgery.operating_room_id,
            surgery.procedure_name, surgery.scheduled_date, surgery.scheduled_time,
            surgery.estimated_duration_minutes, surgery.status or 'scheduled',
            surgery.urgency_level or 'routine', surgery.notes,
            json.dumps(surgery.participants) if surgery.participants else None
        ))
        
        result = cur.fetchone()
        conn.commit()
        
        return {
            "id": str(result[0]), "patient_id": str(result[1]), "doctor_id": str(result[2]),
            "operating_room_id": str(result[3]) if result[3] else None, "procedure_name": result[4],
            "scheduled_date": result[5], "scheduled_time": str(result[6]) if result[6] else None,
            "estimated_duration_minutes": result[7], "actual_start_time": result[8],
            "actual_end_time": result[9], "status": result[10], "urgency_level": result[11],
            "notes": result[12], "participants": result[13], "created_at": result[14], "updated_at": result[15]
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.put("/{surgery_id}", response_model=SurgeryResponse)
def update_surgery(surgery_id: str, updates: SurgeryUpdate, current_doctor: dict = Depends(get_current_doctor)):
    """Update surgery information"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        update_fields = []
        params = []
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                if field == "participants":
                    update_fields.append(f"{field} = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(surgery_id)
        
        query = f"""
            UPDATE surgeries SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, patient_id, doctor_id, operating_room_id, procedure_name,
                      scheduled_date, scheduled_time, estimated_duration_minutes, actual_start_time,
                      actual_end_time, status, urgency_level, notes, participants, created_at, updated_at
        """
        
        cur.execute(query, params)
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        conn.commit()
        
        return {
            "id": str(result[0]), "patient_id": str(result[1]), "doctor_id": str(result[2]),
            "operating_room_id": str(result[3]) if result[3] else None, "procedure_name": result[4],
            "scheduled_date": result[5], "scheduled_time": str(result[6]) if result[6] else None,
            "estimated_duration_minutes": result[7], "actual_start_time": result[8],
            "actual_end_time": result[9], "status": result[10], "urgency_level": result[11],
            "notes": result[12], "participants": result[13], "created_at": result[14], "updated_at": result[15]
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

@router.patch("/{surgery_id}/status")
def update_surgery_status(surgery_id: str, status_update: StatusUpdate, current_doctor: dict = Depends(get_current_doctor)):
    """Update surgery status"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE surgeries SET status = %s
            WHERE id = %s
            RETURNING id, status
        """, (status_update.status, surgery_id))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        conn.commit()
        
        return {
            "surgery_id": str(result[0]),
            "status": result[1],
            "message": f"Surgery status updated to {result[1]}"
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

@router.post("/{surgery_id}/participants/add")
def add_surgery_participant(surgery_id: str, participant_name: str, current_doctor: dict = Depends(get_current_doctor)):
    """Add participant to surgery (triggers notification)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get current participants
        cur.execute("SELECT participants, doctor_id FROM surgeries WHERE id = %s", (surgery_id,))
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        participants = result[0] or []
        doctor_id = str(result[1])
        
        if participant_name not in participants:
            participants.append(participant_name)
        
        # Update surgery
        cur.execute("""
            UPDATE surgeries SET participants = %s
            WHERE id = %s
        """, (json.dumps(participants), surgery_id))
        
        # Create notification for the doctor
        cur.execute("""
            INSERT INTO notifications (doctor_id, title, message, notification_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            doctor_id,
            "New Surgery Participant",
            f"{participant_name} has been added to the surgery",
            "surgery_update",
            surgery_id
        ))
        
        conn.commit()
        
        return {
            "surgery_id": surgery_id,
            "participants": participants,
            "message": f"{participant_name} added successfully"
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

@router.post("/{surgery_id}/delay")
def delay_surgery(surgery_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Mark surgery as delayed and notify participants"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Update surgery status
        cur.execute("""
            UPDATE surgeries SET status = 'delayed'
            WHERE id = %s
            RETURNING doctor_id, participants, procedure_name
        """, (surgery_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        doctor_id = str(result[0])
        participants = result[1] or []
        procedure_name = result[2]
        
        # Create notification
        cur.execute("""
            INSERT INTO notifications (doctor_id, title, message, notification_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            doctor_id,
            "Surgery Delayed",
            f"Surgery '{procedure_name}' has been delayed",
            "surgery_delayed",
            surgery_id
        ))
        
        conn.commit()
        
        return {
            "surgery_id": surgery_id,
            "status": "delayed",
            "message": "Surgery marked as delayed and participants notified"
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

@router.post("/{surgery_id}/cancel")
def cancel_surgery(surgery_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Cancel surgery and notify participants"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Update surgery status
        cur.execute("""
            UPDATE surgeries SET status = 'cancelled'
            WHERE id = %s
            RETURNING doctor_id, participants, procedure_name, operating_room_id
        """, (surgery_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        doctor_id = str(result[0])
        participants = result[1] or []
        procedure_name = result[2]
        or_id = result[3]
        
        # Free up operating room
        if or_id:
            cur.execute("UPDATE operating_rooms SET status = 'available' WHERE id = %s", (or_id,))
        
        # Create notification
        cur.execute("""
            INSERT INTO notifications (doctor_id, title, message, notification_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            doctor_id,
            "Surgery Cancelled",
            f"Surgery '{procedure_name}' has been cancelled",
            "surgery_cancelled",
            surgery_id
        ))
        
        conn.commit()
        
        return {
            "surgery_id": surgery_id,
            "status": "cancelled",
            "message": "Surgery cancelled and participants notified"
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

@router.post("/{surgery_id}/complete")
def complete_surgery(surgery_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Mark surgery as completed and notify participants"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Update surgery status
        cur.execute("""
            UPDATE surgeries SET status = 'completed', actual_end_time = NOW()
            WHERE id = %s
            RETURNING doctor_id, participants, procedure_name, operating_room_id
        """, (surgery_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Surgery not found")
        
        doctor_id = str(result[0])
        participants = result[1] or []
        procedure_name = result[2]
        or_id = result[3]
        
        # Free up operating room
        if or_id:
            cur.execute("UPDATE operating_rooms SET status = 'available' WHERE id = %s", (or_id,))
        
        # Create notification
        cur.execute("""
            INSERT INTO notifications (doctor_id, title, message, notification_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            doctor_id,
            "Surgery Completed",
            f"Surgery '{procedure_name}' has been completed successfully",
            "surgery_completed",
            surgery_id
        ))
        
        conn.commit()
        
        return {
            "surgery_id": surgery_id,
            "status": "completed",
            "message": "Surgery completed and participants notified"
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
