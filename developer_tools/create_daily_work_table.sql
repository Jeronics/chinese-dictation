-- Create daily_work_registry table for tracking daily sessions and streaks
CREATE TABLE IF NOT EXISTS daily_work_registry (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    session_date DATE NOT NULL,
    session_type TEXT NOT NULL, -- 'practice' or 'story'
    sentences_above_7 INTEGER NOT NULL DEFAULT 0,
    total_sentences INTEGER NOT NULL DEFAULT 0,
    story_id TEXT, -- NULL for practice sessions
    story_parts_completed INTEGER DEFAULT 0, -- For story sessions, count parts completed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, session_date, session_type, story_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_daily_work_user_date ON daily_work_registry(user_id, session_date);
CREATE INDEX IF NOT EXISTS idx_daily_work_user_type ON daily_work_registry(user_id, session_type);

-- Enable RLS on the table
ALTER TABLE daily_work_registry ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can insert their own daily work" ON daily_work_registry;
DROP POLICY IF EXISTS "Users can update their own daily work" ON daily_work_registry;
DROP POLICY IF EXISTS "Users can select their own daily work" ON daily_work_registry;

-- Create policy for inserting new daily work
CREATE POLICY "Users can insert their own daily work"
ON daily_work_registry
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Create policy for updating existing daily work
CREATE POLICY "Users can update their own daily work"
ON daily_work_registry
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Create policy for selecting daily work
CREATE POLICY "Users can select their own daily work"
ON daily_work_registry
FOR SELECT
USING (auth.uid() = user_id);

-- Add comment to table
COMMENT ON TABLE daily_work_registry IS 'Stores daily work registry and streak tracking for users'; 