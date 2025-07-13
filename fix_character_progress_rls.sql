-- Fix RLS policies for character_progress table
-- This script enables users to insert and update their own character progress

-- First, let's check if the table exists and create it if it doesn't
CREATE TABLE IF NOT EXISTS character_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    hanzi TEXT NOT NULL,
    hsk_level TEXT NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    fail_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'learning',
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, hanzi)
);

-- Enable RLS on the table
ALTER TABLE character_progress ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can insert their own progress" ON character_progress;
DROP POLICY IF EXISTS "Users can update their own progress" ON character_progress;
DROP POLICY IF EXISTS "Users can select their own progress" ON character_progress;

-- Create policy for inserting new progress
CREATE POLICY "Users can insert their own progress"
ON character_progress
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Create policy for updating existing progress
CREATE POLICY "Users can update their own progress"
ON character_progress
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Create policy for selecting progress
CREATE POLICY "Users can select their own progress"
ON character_progress
FOR SELECT
USING (auth.uid() = user_id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_character_progress_user_hanzi ON character_progress(user_id, hanzi);
CREATE INDEX IF NOT EXISTS idx_character_progress_user_level ON character_progress(user_id, hsk_level);

-- Add comment to table
COMMENT ON TABLE character_progress IS 'Stores user progress for individual Chinese characters'; 