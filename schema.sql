-- ============================================
-- MEDICAL MANAGEMENT SYSTEM DATABASE SCHEMA
-- Clean version - No sample data
-- ============================================

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. DOCTORS TABLE
-- ============================================
CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    specialization VARCHAR(100),
    license_number VARCHAR(50) UNIQUE,
    profile_image_url TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'on_leave')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. PATIENTS TABLE
-- ============================================
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other')),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    blood_type VARCHAR(5),
    allergies TEXT,
    medical_history TEXT,
    insurance_info JSONB,
    profile_image_url TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deceased')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. OPERATING ROOMS (ORs) TABLE
-- ============================================
CREATE TABLE operating_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_number VARCHAR(20) UNIQUE NOT NULL,
    room_name VARCHAR(100),
    capacity INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'in_use', 'maintenance', 'unavailable')),
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. SURGERIES TABLE
-- ============================================
CREATE TABLE surgeries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    operating_room_id UUID REFERENCES operating_rooms(id) ON DELETE SET NULL,
    surgery_type VARCHAR(100) NOT NULL,
    procedure_name VARCHAR(200) NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER,
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    status VARCHAR(30) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'rescheduled')),
    urgency_level VARCHAR(20) CHECK (urgency_level IN ('routine', 'urgent', 'emergency')),
    participants JSONB,
    pre_op_notes TEXT,
    post_op_notes TEXT,
    complications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. NOTES TABLE
-- ============================================
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    surgery_id UUID REFERENCES surgeries(id) ON DELETE CASCADE,
    note_type VARCHAR(50) CHECK (note_type IN ('patient_note', 'retro_schedule', 'surgery_note', 'follow_up', 'prescription', 'other')),
    note_context VARCHAR(50) CHECK (note_context IN ('rounds', 'consultation', 'emergency', 'pre_op', 'post_op', 'follow_up', 'other')),
    title VARCHAR(200),
    content TEXT,
    is_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. TRANSCRIPTIONS TABLE
-- ============================================
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    audio_file_url TEXT,
    audio_duration_seconds INTEGER,
    transcription_text TEXT,
    transcription_status VARCHAR(30) DEFAULT 'processing' CHECK (transcription_status IN ('recording', 'processing', 'completed', 'failed')),
    confidence_score DECIMAL(5,2),
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================
-- 7. NOTE ANALYSIS TABLE
-- ============================================
CREATE TABLE note_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transcription_id UUID NOT NULL REFERENCES transcriptions(id) ON DELETE CASCADE,
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50),
    analysis_result JSONB,
    keywords TEXT[],
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. NOTIFICATIONS TABLE
-- ============================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    user_type VARCHAR(20) CHECK (user_type IN ('doctor', 'patient', 'admin')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) CHECK (notification_type IN ('appointment', 'surgery', 'note', 'reminder', 'alert', 'system')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    is_read BOOLEAN DEFAULT FALSE,
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- ============================================
-- 9. DASHBOARD METRICS TABLE
-- ============================================
CREATE TABLE dashboard_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE NOT NULL,
    or_utilization_percentage DECIMAL(5,2),
    total_patients_count INTEGER DEFAULT 0,
    total_surgeries_count INTEGER DEFAULT 0,
    notes_taken_count INTEGER DEFAULT 0,
    avg_wait_time_minutes INTEGER,
    completed_surgeries_count INTEGER DEFAULT 0,
    cancelled_surgeries_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_date)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Doctors indexes
CREATE INDEX idx_doctors_email ON doctors(email);
CREATE INDEX idx_doctors_status ON doctors(status);

-- Patients indexes
CREATE INDEX idx_patients_patient_code ON patients(patient_code);
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patients_status ON patients(status);

-- Surgeries indexes
CREATE INDEX idx_surgeries_patient_id ON surgeries(patient_id);
CREATE INDEX idx_surgeries_doctor_id ON surgeries(doctor_id);
CREATE INDEX idx_surgeries_scheduled_date ON surgeries(scheduled_date);
CREATE INDEX idx_surgeries_status ON surgeries(status);
CREATE INDEX idx_surgeries_operating_room_id ON surgeries(operating_room_id);

-- Notes indexes
CREATE INDEX idx_notes_patient_id ON notes(patient_id);
CREATE INDEX idx_notes_doctor_id ON notes(doctor_id);
CREATE INDEX idx_notes_surgery_id ON notes(surgery_id);
CREATE INDEX idx_notes_created_at ON notes(created_at);
CREATE INDEX idx_notes_note_context ON notes(note_context);

-- Transcriptions indexes
CREATE INDEX idx_transcriptions_note_id ON transcriptions(note_id);
CREATE INDEX idx_transcriptions_doctor_id ON transcriptions(doctor_id);
CREATE INDEX idx_transcriptions_status ON transcriptions(transcription_status);

-- Note analysis indexes
CREATE INDEX idx_note_analysis_transcription_id ON note_analysis(transcription_id);
CREATE INDEX idx_note_analysis_note_id ON note_analysis(note_id);

-- Notifications indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- Dashboard metrics indexes
CREATE INDEX idx_dashboard_metrics_date ON dashboard_metrics(metric_date);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON doctors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_operating_rooms_updated_at BEFORE UPDATE ON operating_rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_surgeries_updated_at BEFORE UPDATE ON surgeries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- TABLE COMMENTS
-- ============================================

COMMENT ON TABLE doctors IS 'Stores doctor/physician information and credentials';
COMMENT ON TABLE patients IS 'Stores patient information and medical records';
COMMENT ON TABLE operating_rooms IS 'Stores operating room details and availability';
COMMENT ON TABLE surgeries IS 'Stores surgery schedules, participants, and details';
COMMENT ON TABLE notes IS 'Stores medical notes taken during rounds or consultations';
COMMENT ON TABLE transcriptions IS 'Stores AI transcriptions of voice-recorded medical notes';
COMMENT ON TABLE note_analysis IS 'Stores AI analysis results of transcribed notes';
COMMENT ON TABLE notifications IS 'Stores user notifications and alerts';
COMMENT ON TABLE dashboard_metrics IS 'Stores daily dashboard metrics and analytics';

-- ============================================
-- COLUMN COMMENTS
-- ============================================

COMMENT ON COLUMN surgeries.participants IS 'JSONB array of surgery team members, e.g., ["Dr. Smith", "Nurse Johnson"]';
COMMENT ON COLUMN notes.note_context IS 'Context where the note was taken: rounds, consultation, emergency, etc.';
COMMENT ON COLUMN notes.surgery_id IS 'Optional: links note to a surgery if applicable';
COMMENT ON COLUMN note_analysis.analysis_result IS 'JSONB containing AI analysis: concerns, actions, entities, urgency, etc.';
COMMENT ON COLUMN dashboard_metrics.or_utilization_percentage IS 'Daily OR utilization percentage for analytics dashboard';