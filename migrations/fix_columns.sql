-- Fix missing/incorrect columns

-- Add missing columns to transcriptions
ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS recording_duration_seconds INTEGER;

-- Fix note_analysis table columns
ALTER TABLE note_analysis 
  ADD COLUMN IF NOT EXISTS concerns_identified TEXT[],
  ADD COLUMN IF NOT EXISTS actions_recommended TEXT[],
  ADD COLUMN IF NOT EXISTS keywords_extracted TEXT[],
  ADD COLUMN IF NOT EXISTS urgency_level VARCHAR(20),
  ADD COLUMN IF NOT EXISTS analysis_status VARCHAR(30) DEFAULT 'pending';

-- Add transcription_id to notes table
ALTER TABLE notes ADD COLUMN IF NOT EXISTS transcription_id UUID REFERENCES transcriptions(id) ON DELETE SET NULL;

-- Add index
CREATE INDEX IF NOT EXISTS idx_notes_transcription_id ON notes(transcription_id);

-- Add doctor notifications link
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS doctor_id UUID REFERENCES doctors(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_notifications_doctor_id ON notifications(doctor_id);