"""
Pydantic models for request/response validation
Complete models for all endpoints
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from decimal import Decimal

# ============================================
# AUTHENTICATION MODELS
# ============================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    doctor: Dict[str, Any]

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ============================================
# DOCTOR MODELS
# ============================================

class DoctorBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    profile_image_url: Optional[str] = None
    status: Optional[str] = Field("active", pattern="^(active|inactive|on_leave)$")

class DoctorCreate(DoctorBase):
    password: str = Field(..., min_length=8)

class DoctorUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    specialization: Optional[str] = Field(None, max_length=100)
    profile_image_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

class DoctorResponse(DoctorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# PATIENT MODELS
# ============================================

class PatientBase(BaseModel):
    patient_code: str = Field(..., max_length=20)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    blood_type: Optional[str] = Field(None, max_length=5)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    profile_image_url: Optional[str] = None
    status: Optional[str] = Field("active", pattern="^(active|inactive|deceased)$")

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    patient_code: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    profile_image_url: Optional[str] = None
    status: Optional[str] = None

class PatientResponse(PatientBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# OPERATING ROOM MODELS
# ============================================

class OperatingRoomBase(BaseModel):
    room_number: str = Field(..., max_length=20)
    room_name: Optional[str] = Field(None, max_length=100)
    capacity: Optional[int] = Field(1, ge=1)
    status: Optional[str] = Field("available", pattern="^(available|in_use|maintenance|unavailable)$")
    location: Optional[str] = Field(None, max_length=100)

class OperatingRoomResponse(OperatingRoomBase):
    id: str
    created_at: datetime
    updated_at: datetime

# ============================================
# SURGERY MODELS
# ============================================

class SurgeryBase(BaseModel):
    patient_id: str
    doctor_id: str
    operating_room_id: Optional[str] = None
    surgery_type: str = Field(..., max_length=100)
    procedure_name: str = Field(..., max_length=200)
    scheduled_date: date
    scheduled_time: time
    duration_minutes: Optional[int] = Field(None, ge=0)
    urgency_level: Optional[str] = Field(None, pattern="^(routine|urgent|emergency)$")
    participants: Optional[List[str]] = None
    pre_op_notes: Optional[str] = None

class SurgeryCreate(SurgeryBase):
    pass

class SurgeryUpdate(BaseModel):
    operating_room_id: Optional[str] = None
    procedure_name: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    urgency_level: Optional[str] = None
    participants: Optional[List[str]] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    complications: Optional[str] = None

class SurgeryStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(scheduled|in_progress|completed|cancelled|rescheduled)$")
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None

class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(scheduled|in_progress|completed|cancelled|delayed)$")

class SurgeryResponse(SurgeryBase):
    id: str
    status: str
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    post_op_notes: Optional[str] = None
    complications: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ============================================
# NOTE MODELS
# ============================================

class NoteBase(BaseModel):
    patient_id: str
    doctor_id: str
    surgery_id: Optional[str] = None
    note_type: Optional[str] = Field(None, pattern="^(patient_note|retro_schedule|surgery_note|follow_up|prescription|other)$")
    note_context: Optional[str] = Field(None, pattern="^(rounds|consultation|emergency|pre_op|post_op|follow_up|other)$")
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None

class SaveNoteRequest(BaseModel):
    transcription_id: str
    patient_id: str
    title: Optional[str] = "Medical Note"
    note_context: str = "rounds"

class NoteSaveRequest(BaseModel):
    transcription_id: str
    patient_id: str
    doctor_id: str
    note_title: Optional[str] = None
    note_type: str = Field("patient_note")
    note_context: str = Field("rounds")

class NoteResponse(NoteBase):
    id: str
    is_locked: bool
    created_at: datetime
    updated_at: datetime

# ============================================
# TRANSCRIPTION MODELS
# ============================================

class TranscriptionStart(BaseModel):
    doctor_id: str

class TranscriptionStop(BaseModel):
    audio_file: Optional[str] = None  # Base64 or URL
    audio_duration_seconds: Optional[int] = None

class StartRecordingRequest(BaseModel):
    patient_id: Optional[str] = None

class TranscriptionResponse(BaseModel):
    id: str
    transcription_status: str
    transcription_text: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# ============================================
# ANALYSIS MODELS
# ============================================

class AnalysisResponse(BaseModel):
    id: str
    transcription_id: str
    concerns: List[str]
    actions: List[str]
    keywords: List[str]
    urgency: str
    summary: str
    created_at: datetime

# ============================================
# NOTIFICATION MODELS
# ============================================

class NotificationCreate(BaseModel):
    user_id: str
    user_type: str = Field(..., pattern="^(doctor|patient|admin)$")
    title: str
    message: str
    notification_type: str
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    user_type: str
    title: str
    message: str
    notification_type: str
    priority: str
    is_read: bool
    related_entity_type: Optional[str]
    related_entity_id: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]

# ============================================
# DASHBOARD MODELS
# ============================================

class HospitalMetrics(BaseModel):
    or_utilization_percentage: Optional[Decimal]
    total_patients_today: int
    total_surgeries_today: int
    completed_surgeries: int
    avg_wait_time_minutes: Optional[int]
    date: date

class DoctorMetrics(BaseModel):
    doctor_id: str
    notes_taken_today: int
    notes_taken_this_week: int
    patients_seen_today: int
    upcoming_surgeries: int
    total_recordings: int
    date: date

# ============================================
# OR SCHEDULE MODELS
# ============================================

class ORBookingRequest(BaseModel):
    operating_room_id: str
    patient_id: str
    doctor_id: str
    scheduled_date: date
    scheduled_time: time
    procedure_name: str
    surgery_type: str
    duration_minutes: Optional[int] = 60
    urgency_level: Optional[str] = "routine"
    participants: Optional[List[str]] = None

class TimeSlotStatus(BaseModel):
    time: str
    or_rooms: Dict[str, Dict[str, Any]]  # or_id: {status, patient_name, etc}

class DayScheduleResponse(BaseModel):
    date: date
    time_slots: List[TimeSlotStatus]
