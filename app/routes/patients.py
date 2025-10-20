"""Patient routes - CRUD and related data"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models import PatientCreate, PatientUpdate, PatientResponse
from app.dependencies import get_current_doctor
from app.db import get_connection
import json

router = APIRouter()

@router.post("/", response_model=PatientResponse, status_code=201)
def create_patient(patient: PatientCreate, current_doctor: dict = Depends(get_current_doctor)):
    """Create a new patient"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO patients (patient_code, first_name, last_name, date_of_birth, gender, email, phone,
                                address, emergency_contact_name, emergency_contact_phone, blood_type,
                                allergies, medical_history, insurance_info, profile_image_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, patient_code, first_name, last_name, date_of_birth, gender, email, phone,
                      address, emergency_contact_name, emergency_contact_phone, blood_type,
                      allergies, medical_history, insurance_info, profile_image_url, status, created_at, updated_at
        """, (
            patient.patient_code, patient.first_name, patient.last_name, patient.date_of_birth,
            patient.gender, patient.email, patient.phone, patient.address,
            patient.emergency_contact_name, patient.emergency_contact_phone, patient.blood_type,
            patient.allergies, patient.medical_history, 
            json.dumps(patient.insurance_info) if patient.insurance_info else None,
            patient.profile_image_url, patient.status
        ))
        
        result = cur.fetchone()
        conn.commit()
        
        return {
            "id": str(result[0]), "patient_code": result[1], "first_name": result[2],
            "last_name": result[3], "date_of_birth": result[4], "gender": result[5],
            "email": result[6], "phone": result[7], "address": result[8],
            "emergency_contact_name": result[9], "emergency_contact_phone": result[10],
            "blood_type": result[11], "allergies": result[12], "medical_history": result[13],
            "insurance_info": result[14], "profile_image_url": result[15],
            "status": result[16], "created_at": result[17], "updated_at": result[18]
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

@router.get("/", response_model=List[PatientResponse])
def get_all_patients(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_doctor: dict = Depends(get_current_doctor)
):
    """Get all patients with filters"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT id, patient_code, first_name, last_name, date_of_birth, gender, email, phone,
                   address, emergency_contact_name, emergency_contact_phone, blood_type,
                   allergies, medical_history, insurance_info, profile_image_url, status, created_at, updated_at
            FROM patients WHERE 1=1
        """
        params = []
        
        if search:
            query += """ AND (first_name ILIKE %s OR last_name ILIKE %s OR patient_code ILIKE %s)"""
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        patients = []
        for row in results:
            patients.append({
                "id": str(row[0]), "patient_code": row[1], "first_name": row[2],
                "last_name": row[3], "date_of_birth": row[4], "gender": row[5],
                "email": row[6], "phone": row[7], "address": row[8],
                "emergency_contact_name": row[9], "emergency_contact_phone": row[10],
                "blood_type": row[11], "allergies": row[12], "medical_history": row[13],
                "insurance_info": row[14], "profile_image_url": row[15],
                "status": row[16], "created_at": row[17], "updated_at": row[18]
            })
        
        return patients
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get a specific patient"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, patient_code, first_name, last_name, date_of_birth, gender, email, phone,
                   address, emergency_contact_name, emergency_contact_phone, blood_type,
                   allergies, medical_history, insurance_info, profile_image_url, status, created_at, updated_at
            FROM patients WHERE id = %s
        """, (patient_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "id": str(result[0]), "patient_code": result[1], "first_name": result[2],
            "last_name": result[3], "date_of_birth": result[4], "gender": result[5],
            "email": result[6], "phone": result[7], "address": result[8],
            "emergency_contact_name": result[9], "emergency_contact_phone": result[10],
            "blood_type": result[11], "allergies": result[12], "medical_history": result[13],
            "insurance_info": result[14], "profile_image_url": result[15],
            "status": result[16], "created_at": result[17], "updated_at": result[18]
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

@router.get("/{patient_id}/surgeries")
def get_patient_surgeries(patient_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get all surgeries for a patient"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.procedure_name, s.scheduled_date, s.scheduled_time, s.status, s.urgency_level,
                   d.first_name, d.last_name, o.room_number
            FROM surgeries s
            JOIN doctors d ON s.doctor_id = d.id
            LEFT JOIN operating_rooms o ON s.operating_room_id = o.id
            WHERE s.patient_id = %s
            ORDER BY s.scheduled_date DESC, s.scheduled_time DESC
        """, (patient_id,))
        
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
                "doctor_name": f"{row[6]} {row[7]}",
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

@router.get("/{patient_id}/latest-note")
def get_patient_latest_note(patient_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get latest note summary for patient"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT n.id, n.title, n.content, n.note_context, n.created_at,
                   d.first_name, d.last_name
            FROM notes n
            JOIN doctors d ON n.doctor_id = d.id
            WHERE n.patient_id = %s
            ORDER BY n.created_at DESC
            LIMIT 1
        """, (patient_id,))
        
        result = cur.fetchone()
        
        if not result:
            return None
        
        summary = result[2][:200] + "..." if result[2] and len(result[2]) > 200 else result[2]
        
        return {
            "note_id": str(result[0]),
            "title": result[1],
            "summary": summary,
            "note_context": result[3],
            "created_at": result[4],
            "doctor_name": f"{result[5]} {result[6]}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, updates: PatientUpdate, current_doctor: dict = Depends(get_current_doctor)):
    """Update patient information"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        update_fields = []
        params = []
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                if field == "insurance_info":
                    update_fields.append(f"{field} = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(patient_id)
        
        query = f"""
            UPDATE patients SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, patient_code, first_name, last_name, date_of_birth, gender, email, phone,
                      address, emergency_contact_name, emergency_contact_phone, blood_type,
                      allergies, medical_history, insurance_info, profile_image_url, status, created_at, updated_at
        """
        
        cur.execute(query, params)
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        conn.commit()
        
        return {
            "id": str(result[0]), "patient_code": result[1], "first_name": result[2],
            "last_name": result[3], "date_of_birth": result[4], "gender": result[5],
            "email": result[6], "phone": result[7], "address": result[8],
            "emergency_contact_name": result[9], "emergency_contact_phone": result[10],
            "blood_type": result[11], "allergies": result[12], "medical_history": result[13],
            "insurance_info": result[14], "profile_image_url": result[15],
            "status": result[16], "created_at": result[17], "updated_at": result[18]
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

@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Delete a patient"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM patients WHERE id = %s RETURNING id", (patient_id,))
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        conn.commit()
        return None
        
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