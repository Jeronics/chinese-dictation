-- Create conversation_progress table
CREATE TABLE IF NOT EXISTS conversation_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id INTEGER NOT NULL,
    current_index INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, conversation_id)
);

-- Enable Row Level Security
ALTER TABLE conversation_progress ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to see only their own progress
CREATE POLICY "Users can view their own conversation progress" ON conversation_progress
    FOR SELECT USING (auth.uid() = user_id);

-- Create policy to allow users to insert their own progress
CREATE POLICY "Users can insert their own conversation progress" ON conversation_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create policy to allow users to update their own progress
CREATE POLICY "Users can update their own conversation progress" ON conversation_progress
    FOR UPDATE USING (auth.uid() = user_id);

-- Create policy to allow users to delete their own progress
CREATE POLICY "Users can delete their own conversation progress" ON conversation_progress
    FOR DELETE USING (auth.uid() = user_id); 