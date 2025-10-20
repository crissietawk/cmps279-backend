"""Notes routes - Save and retrieve patient notes"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.dependencies import get_current_doctor
from app.db import get_connection
from app.models import SaveNoteRequest
from datetime import datetime

router = APIRouter()

@router.post("/save")
def save_note(request: SaveNoteRequest, current_doctor: dict = Depends(get_current_doctor)):
    """Save transcription as a patient note (triggers analysis)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get transcription text
        cur.execute("""
            SELECT transcription_text, patient_id
            FROM transcriptions
            WHERE id = %s AND doctor_id = %s
        """, (request.transcription_id, current_doctor["id"]))
        
        transcription = cur.fetchone()
        
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        transcription_text = transcription[0]
        patient_id = str(transcription[1])
        
        # Create note
        cur.execute("""
            INSERT INTO notes (
                patient_id, doctor_id, transcription_id, title, content, note_context
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, content, note_context, created_at
        """, (
            patient_id,
            current_doctor["id"],
            request.transcription_id,
            request.title,
            transcription_text,
            request.note_context or "general"
        ))
        
        note = cur.fetchone()
        note_id = str(note[0])
        
        # Trigger mock analysis
        mock_concerns = ["cardiac related issue", "elevated blood pressure", "shortness of breath"]
        mock_actions = ["ECG (Electrocardiogram)", "Blood pressure monitoring", "Stress test evaluation"]
        mock_keywords = ["cardiac", "chest discomfort", "blood pressure", "ECG", "hypertension"]
        
        cur.execute("""
            INSERT INTO note_analysis (
                note_id, transcription_id, concerns_identified, actions_recommended,
                keywords_extracted, urgency_level, summary, analysis_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            note_id,
            request.transcription_id,
            mock_concerns,
            mock_actions,
            mock_keywords,
            "high",
            "Patient requires immediate cardiac evaluation and monitoring",
            "completed"
        ))
        
        conn.commit()
        
        return {
            "note_id": note_id,
            "title": note[1],
            "content": note[2],
            "note_context": note[3],
            "created_at": note[4],
            "message": "Note saved and analysis completed"
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

@router.get("/patient/{patient_id}/book")
def get_patient_notes_book(
    patient_id: str,
    note_context: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_doctor: dict = Depends(get_current_doctor)
):
    """Get patient's notes book with pagination and filters"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT n.id, n.title, n.content, n.note_context, n.created_at,
                   d.first_name, d.last_name,
                   na.urgency_level, na.summary
            FROM notes n
            JOIN doctors d ON n.doctor_id = d.id
            LEFT JOIN note_analysis na ON n.id = na.note_id
            WHERE n.patient_id = %s
        """
        params = [patient_id]
        
        if note_context:
            query += " AND n.note_context = %s"
            params.append(note_context)
        
        if search:
            query += " AND (n.title ILIKE %s OR n.content ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        query += " ORDER BY n.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        notes = []
        for row in results:
            content = row[2]
            preview = content[:200] + "..." if content and len(content) > 200 else content
            
            notes.append({
                "note_id": str(row[0]),
                "title": row[1],
                "content_preview": preview,
                "note_context": row[3],
                "created_at": row[4],
                "doctor_name": f"{row[5]} {row[6]}",
                "urgency_level": row[7],
                "summary": row[8]
            })
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM notes WHERE patient_id = %s"
        count_params = [patient_id]
        
        if note_context:
            count_query += " AND note_context = %s"
            count_params.append(note_context)
        
        if search:
            count_query += " AND (title ILIKE %s OR content ILIKE %s)"
            count_params.extend([search_param, search_param])
        
        cur.execute(count_query, count_params)
        total_count = cur.fetchone()[0]
        
        return {
            "patient_id": patient_id,
            "notes": notes,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{note_id}")
def get_note_detail(note_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get single note with full transcription and analysis"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT n.id, n.title, n.content, n.note_context, n.created_at,
                   p.id, p.first_name, p.last_name, p.patient_code,
                   d.first_name, d.last_name,
                   t.transcription_text, t.confidence_score,
                   na.concerns_identified, na.actions_recommended, na.keywords_extracted,
                   na.urgency_level, na.summary
            FROM notes n
            JOIN patients p ON n.patient_id = p.id
            JOIN doctors d ON n.doctor_id = d.id
            LEFT JOIN transcriptions t ON n.transcription_id = t.id
            LEFT JOIN note_analysis na ON n.id = na.note_id
            WHERE n.id = %s
        """, (note_id,))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {
            "note_id": str(result[0]),
            "title": result[1],
            "content": result[2],
            "note_context": result[3],
            "created_at": result[4],
            "patient": {
                "id": str(result[5]),
                "name": f"{result[6]} {result[7]}",
                "patient_code": result[8]
            },
            "doctor_name": f"{result[9]} {result[10]}",
            "transcription": {
                "text": result[11],
                "confidence_score": result[12]
            } if result[11] else None,
            "analysis": {
                "concerns": result[13],
                "actions": result[14],
                "keywords": result[15],
                "urgency_level": result[16],
                "summary": result[17]
            } if result[13] else None
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