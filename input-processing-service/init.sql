-- Database initialization script for Input Processing Service

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS input_processing;

-- Use the database
\c input_processing;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create input_records table
CREATE TABLE IF NOT EXISTS input_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    raw_input TEXT NOT NULL,
    input_length INTEGER NOT NULL,
    detected_language VARCHAR(10),
    language_confidence VARCHAR(20),
    translation_result JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    current_phase VARCHAR(50),
    validation_result JSONB,
    content_policy_check JSONB,
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create processing_statuses table
CREATE TABLE IF NOT EXISTS processing_statuses (
    id SERIAL PRIMARY KEY,
    input_record_id INTEGER NOT NULL REFERENCES input_records(id) ON DELETE CASCADE,
    phase VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress_percentage INTEGER DEFAULT 0,
    phase_data JSONB,
    error_message TEXT,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_input_records_user_id ON input_records(user_id);
CREATE INDEX IF NOT EXISTS idx_input_records_status ON input_records(status);
CREATE INDEX IF NOT EXISTS idx_input_records_created_at ON input_records(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_statuses_input_record_id ON processing_statuses(input_record_id);
CREATE INDEX IF NOT EXISTS idx_processing_statuses_phase ON processing_statuses(phase);
CREATE INDEX IF NOT EXISTS idx_processing_statuses_status ON processing_statuses(status);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_input_records_updated_at BEFORE UPDATE ON input_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (for development)
INSERT INTO users (email, password_hash, first_name, last_name, is_active, is_verified)
VALUES 
    ('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8K8K8K8', 'Test', 'User', TRUE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- Create a view for processing statistics
CREATE OR REPLACE VIEW processing_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_inputs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_inputs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_inputs,
    AVG(input_length) as avg_input_length,
    COUNT(DISTINCT user_id) as unique_users
FROM input_records
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE input_processing TO user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO user;

