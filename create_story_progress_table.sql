-- Create story_progress table for storing user story progress
CREATE TABLE IF NOT EXISTS story_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    story_id TEXT NOT NULL,
    current_index INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,
    total_parts INTEGER NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, story_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_story_progress_user_story ON story_progress(user_id, story_id);

-- Add comment to table
COMMENT ON TABLE story_progress IS 'Stores user progress for story sessions'; 