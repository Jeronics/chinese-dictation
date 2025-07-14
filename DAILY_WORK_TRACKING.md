# Daily Work Tracking & Streak System

## Overview

The Chinese Dictation app now includes a comprehensive daily work tracking system that monitors user progress and maintains streaks based on daily practice sessions.

## Features

### 1. Daily Work Registry
- **Session Tracking**: Counts sessions with average accuracy above 7/10
- **Session Types**: Tracks both practice sessions and story sessions separately
- **Story Progress**: For story sessions, tracks parts completed (every 5 sentences count as a streak)

### 2. Streak System
- **Daily Streaks**: Users must complete at least one session with average accuracy above 7/10 to maintain their streak
- **Continuous Tracking**: Streaks are calculated based on consecutive days with successful practice
- **Visual Feedback**: Current streak is displayed prominently in the dashboard

### 3. Dashboard Integration
- **Today's Progress**: Shows sessions with average accuracy above 7/10 for the current day
- **7-Day Chart**: Visual representation of the last 7 days of practice
- **Streak Counter**: Displays current streak with motivational messages

## Database Schema

### `daily_work_registry` Table
```sql
CREATE TABLE daily_work_registry (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    session_date DATE NOT NULL,
    session_type TEXT NOT NULL, -- 'practice' or 'story'
    sentences_above_7 INTEGER NOT NULL DEFAULT 0,
    total_sentences INTEGER NOT NULL DEFAULT 0,
    story_id TEXT, -- NULL for practice sessions
    story_parts_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, session_date, session_type, story_id)
);
```

## How It Works

### Accuracy Calculation
- **Distance Score**: Based on Levenshtein distance between user input and correct answer
- **Session Average**: Average of all distance scores in a session (0-10 scale)
- **Threshold**: Sessions with average score ≥ 7 are considered "above 7"
- **Formula**: `(len(correct) - levenshtein_distance) * 10 / len(correct)` for each sentence, then averaged

### Streak Logic
1. **Daily Check**: System checks if user completed any sessions with average accuracy above 7/10
2. **Consecutive Days**: Streak continues as long as there's at least one successful session per day
3. **Break**: Streak breaks if a day passes without any sessions above 7/10 average

### Story Sessions
- **Part Tracking**: Each story part completed counts as one sentence
- **Streak Contribution**: Every 5 story parts completed contribute to the daily streak
- **Separate Tracking**: Story sessions are tracked separately from practice sessions

## User Interface

### Dashboard
- **Daily Work Section**: Prominent display of today's progress and current streak
- **7-Day Chart**: Bar chart showing daily activity with completion status
- **Motivational Messages**: Encouraging text based on streak length

### Session Summaries
- **Progress Update**: Shows daily progress after completing sessions
- **Streak Status**: Displays current streak with fire emoji for motivation
- **Immediate Feedback**: Users see their progress impact immediately

## Technical Implementation

### Key Functions
- `update_daily_work_registry()`: Records daily work data
- `get_daily_work_stats()`: Calculates statistics for dashboard display
- **Integration**: Called automatically after each sentence completion

### Data Flow
1. User completes a sentence
2. Accuracy is calculated using Levenshtein distance
3. If accuracy ≥ 7, sentence is counted as "above 7"
4. Daily work registry is updated
5. Dashboard displays updated statistics

## Benefits

### For Users
- **Motivation**: Visual streak tracking encourages daily practice
- **Progress Tracking**: Clear view of daily and weekly progress
- **Gamification**: Streak system adds game-like elements to learning

### For Learning
- **Consistency**: Encourages regular practice habits
- **Quality Focus**: Emphasizes accuracy over quantity
- **Long-term Engagement**: Streak system maintains user interest

## Future Enhancements

### Potential Features
- **Weekly/Monthly Goals**: Set targets for sentences above 7/10
- **Achievement Badges**: Rewards for milestone streaks
- **Social Features**: Share streaks with friends
- **Detailed Analytics**: More comprehensive progress reports

### Technical Improvements
- **Performance Optimization**: Caching for frequently accessed stats
- **Mobile Optimization**: Better responsive design for mobile devices
- **Export Features**: Allow users to export their progress data 