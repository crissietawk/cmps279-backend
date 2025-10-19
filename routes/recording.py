"""Recording routes - Start/stop recording and transcription"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_doctor
from app.db import get_connection
from app.models import StartRecordingRequest
from datetime import datetime

router = APIRouter()

@router.post("/start")
def start_recording(request: StartRecordingRequest, current_doctor: dict = Depends(get_current_doctor)):
    """Start a new recording session"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Create transcription record
        cur.execute("""
            INSERT INTO transcriptions (
                doctor_id, patient_id, audio_file_url, transcription_text,
                confidence_score, recording_duration_seconds, transcription_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, transcription_status, created_at
        """, (
            current_doctor["id"],
            request.patient_id,
            None,  # Will be set when recording stops
            None,  # Will be set when recording stops
            None,
            0,
            "recording"
        ))
        
        result = cur.fetchone()
        conn.commit()
        
        return {
            "transcription_id": str(result[0]),
            "status": result[1],
            "started_at": result[2],
            "message": "Recording started successfully"
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

@router.post("/{transcription_id}/stop")
def stop_recording(transcription_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Stop recording and generate mock transcription"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Mock transcription text
        transcription_text = """Patient presents with cardiac related issue and possible concerns. 
Patient reports chest discomfort and shortness of breath during physical activity. 
Vital signs show elevated blood pressure at 145/95. Heart rate is 88 bpm.
Recommend ECG and blood pressure measurement. Consider stress test if symptoms persist.
Patient has history of hypertension, currently on medication.
Follow-up appointment scheduled in two weeks."""
        
        confidence_score = 95.5
        mock_audio_url = f"recordings/audio_{transcription_id}.wav"
        
        # Update transcription
        cur.execute("""
            UPDATE transcriptions 
            SET transcription_text = %s,
                confidence_score = %s,
                audio_file_url = %s,
                recording_duration_seconds = %s,
                transcription_status = %s
            WHERE id = %s AND doctor_id = %s
            RETURNING id, transcription_text, confidence_score, transcription_status
        """, (
            transcription_text,
            confidence_score,
            mock_audio_url,
            125,  # ~2 minutes
            "completed",
            transcription_id,
            current_doctor["id"]
        ))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Transcription not found or access denied")
        
        conn.commit()
        
        return {
            "transcription_id": str(result[0]),
            "transcription_text": result[1],
            "confidence_score": result[2],
            "status": result[3],
            "message": "Recording stopped and transcribed successfully"
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

@router.get("/{transcription_id}/status")
def get_transcription_status(transcription_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get transcription status (for polling)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, transcription_status, confidence_score, recording_duration_seconds,
                   transcription_text, created_at
            FROM transcriptions
            WHERE id = %s AND doctor_id = %s
        """, (transcription_id, current_doctor["id"]))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        return {
            "transcription_id": str(result[0]),
            "status": result[1],
            "confidence_score": result[2],
            "duration_seconds": result[3],
            "has_text": result[4] is not None,
            "created_at": result[5]
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

@router.delete("/{transcription_id}")
def discard_recording(transcription_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Discard a recording/transcription"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM transcriptions
            WHERE id = %s AND doctor_id = %s
            RETURNING id
        """, (transcription_id, current_doctor["id"]))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Transcription not found or access denied")
        
        conn.commit()
        
        return {"message": "Recording discarded successfully"}
        
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