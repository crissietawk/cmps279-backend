"""Notifications routes - CRUD and triggers"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.dependencies import get_current_doctor
from app.db import get_connection
from app.models import NotificationCreate

router = APIRouter()

@router.get("/")
def get_notifications(current_doctor: dict = Depends(get_current_doctor)):
    """Get all notifications for current doctor"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, title, message, notification_type, is_read, related_entity_id, created_at
            FROM notifications
            WHERE doctor_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (current_doctor["id"],))
        
        results = cur.fetchall()
        
        notifications = []
        for row in results:
            notifications.append({
                "id": str(row[0]),
                "title": row[1],
                "message": row[2],
                "notification_type": row[3],
                "is_read": row[4],
                "related_entity_id": str(row[5]) if row[5] else None,
                "created_at": row[6]
            })
        
        return notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/unread")
def get_unread_count(current_doctor: dict = Depends(get_current_doctor)):
    """Get count of unread notifications"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE doctor_id = %s AND is_read = FALSE
        """, (current_doctor["id"],))
        
        count = cur.fetchone()[0]
        
        return {
            "doctor_id": current_doctor["id"],
            "unread_count": count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: str, current_doctor: dict = Depends(get_current_doctor)):
    """Mark notification as read"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = %s AND doctor_id = %s
            RETURNING id, is_read
        """, (notification_id, current_doctor["id"]))
        
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        conn.commit()
        
        return {
            "notification_id": str(result[0]),
            "is_read": result[1],
            "message": "Notification marked as read"
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

@router.post("/trigger")
def create_notification(notification: NotificationCreate, current_doctor: dict = Depends(get_current_doctor)):
    """Internal: Create a notification (used by other routes)"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO notifications (doctor_id, title, message, notification_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, title, message, notification_type, is_read, created_at
        """, (
            notification.doctor_id,
            notification.title,
            notification.message,
            notification.notification_type,
            notification.related_entity_id
        ))
        
        result = cur.fetchone()
        conn.commit()
        
        return {
            "id": str(result[0]),
            "title": result[1],
            "message": result[2],
            "notification_type": result[3],
            "is_read": result[4],
            "created_at": result[5]
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