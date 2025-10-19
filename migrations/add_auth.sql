-- Migration: Add authentication support

-- Add password field to doctors table
ALTER TABLE doctors ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Create refresh tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for faster token lookups
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_doctor_id ON refresh_tokens(doctor_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);

-- Comments
COMMENT ON TABLE refresh_tokens IS 'Stores refresh tokens for authentication';
COMMENT ON COLUMN doctors.password_hash IS 'Bcrypt hashed password for authentication';
