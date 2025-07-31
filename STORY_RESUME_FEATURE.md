# Story Resume Feature

## Overview
The Chinese Dictation app now supports saving and resuming story progress. Users can save their progress at any point during a story session and resume later from where they left off.

## Features

### Save & Resume Later
- **Save Progress**: Users can click "💾 Save & Resume Later" during any story session to save their current progress
- **Resume Later**: When returning to a story, users will automatically resume from their last saved position
- **Progress Tracking**: The system tracks:
  - Current part index
  - Current score
  - Total parts in the story
  - Last updated timestamp

### Restart Story
- **Restart Option**: Users can click "🔄 Restart Story" to clear all progress and start over
- **Clean Slate**: This completely removes any saved progress for the story

### Visual Indicators
- **Story List**: Stories with saved progress show "🔄 Resume Practice" instead of "▶ Start Practice"
- **Notifications**: Flash messages inform users when:
  - Progress is successfully saved
  - Story is resumed from a saved position
  - Progress save fails
  - User needs to log in to save progress

## Technical Implementation

### Database Schema
The feature uses a `story_progress` table with the following structure:
```sql
CREATE TABLE story_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    story_id TEXT NOT NULL,
    current_index INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,
    total_parts INTEGER NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, story_id)
);
```

### User Experience
1. **Logged-in Users**: Can save and resume progress across devices
2. **Guest Users**: Can use the feature during their session, but progress is not saved permanently
3. **Automatic Cleanup**: Progress is automatically cleared when a story is completed

### Accessibility
- High contrast color schemes for colorblind users
- Clear visual indicators and focus states
- Screen reader friendly button labels

## Usage

### Starting a Story
1. Navigate to the Stories page
2. Click "▶ Start Practice" for a new story or "🔄 Resume Practice" for a saved story
3. Begin practicing the story parts

### Saving Progress
1. During any story session, click "💾 Save & Resume Later"
2. You'll be redirected to the Stories page with a success message
3. Your progress is saved and can be resumed later

### Resuming Progress
1. Return to the Stories page
2. Click "🔄 Resume Practice" on any story with saved progress
3. You'll automatically continue from where you left off

### Restarting a Story
1. During any story session, click "🔄 Restart Story"
2. All saved progress for that story will be cleared
3. You'll start the story from the beginning

## Database Setup
Run the following SQL script to create the required table:
```sql
-- See developer_tools/create_story_progress_table.sql for the complete schema
```

## Notes
- Progress is only saved for logged-in users
- Guest users can use the feature but progress is not persisted
- Progress is automatically cleared when a story is completed
- The feature works with all existing stories in the system 