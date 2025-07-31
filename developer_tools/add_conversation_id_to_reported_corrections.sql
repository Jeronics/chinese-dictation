-- Add conversation_id column to reported_corrections table
ALTER TABLE reported_corrections 
ADD COLUMN IF NOT EXISTS conversation_id INTEGER; 