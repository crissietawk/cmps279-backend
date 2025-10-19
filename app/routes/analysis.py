"""Analysis routes - AI analysis of transcriptions"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_doctor
from app.db import get_connection

router = APIRouter()

@router.get("/{transcription_id}")
def get_transcription_analysis(transcription_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Get AI analysis for a transcription (mock implementation)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if analysis exists
        cur.execute("""
            SELECT na.concerns_identified, na.actions_recommended, na.keywords_extracted,
                   na.urgency_level, na.summary, na.analysis_status, na.created_at
            FROM note_analysis na
            WHERE na.transcription_id = %s
        """, (transcription_id,))
        
        result = cur.fetchone()
        
        if result:
            return {
                "transcription_id": transcription_id,
                "concerns": result[0],
                "actions": result[1],
                "keywords": result[2],
                "urgency": result[3],
                "summary": result[4],
                "status": result[5],
                "analyzed_at": result[6]
            }
        
        # If no analysis exists, return mock analysis
        # In production, this would trigger actual AI processing
        mock_analysis = {
            "transcription_id": transcription_id,
            "concerns": [
                "cardiac related issue",
                "elevated blood pressure (145/95)",
                "shortness of breath during activity",
                "possible cardiovascular stress"
            ],
            "actions": [
                "ECG (Electrocardiogram)",
                "Blood pressure measurement and monitoring",
                "Stress test evaluation",
                "Review current hypertension medication",
                "Schedule follow-up in two weeks"
            ],
            "keywords": [
                "cardiac",
                "chest discomfort",
                "blood pressure",
                "ECG",
                "hypertension",
                "shortness of breath",
                "physical activity"
            ],
            "urgency": "high",
            "summary": "Patient requires immediate cardiac evaluation and monitoring. Presenting symptoms suggest possible cardiovascular stress requiring prompt assessment and intervention.",
            "status": "completed"
        }
        
        return mock_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
