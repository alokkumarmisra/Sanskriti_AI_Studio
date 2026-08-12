-- Migration: Create users and auth_sessions tables for Milestone 6.6
-- This migration creates the authentication system needed for user profile and settings pages

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(256) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    first_name VARCHAR(128),
    last_name VARCHAR(128),
    role VARCHAR(32) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create auth_sessions table for refresh token management
CREATE TABLE IF NOT EXISTS auth_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for auth_sessions
CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS sessions_expires_idx ON auth_sessions(expires_at);
CREATE INDEX IF NOT EXISTS sessions_refresh_token_idx ON auth_sessions(refresh_token);

-- Add owned_project_ids column to users (for tracking project ownership)
ALTER TABLE users ADD COLUMN IF NOT EXISTS owned_project_ids VARCHAR(255) DEFAULT '[]';
