# Chinese Dictation App

A web application for practicing Chinese character dictation with HSK-leveled content, progress tracking, and short stories.

## Features

### 📝 Common Phrases
- Browse and practice individual phrases by HSK level (HSK1-HSK6)
- Filter phrases by difficulty level
- Practice individual phrases with audio playback
- Real-time character correction and accuracy scoring

### 📚 Short Stories
- Complete stories broken into manageable parts for practice
- Two example stories included:
  - **The Emperor's New Clothes** (皇帝的新装) - HSK3 level, 20 parts
  - **The Turtle and the Hare** (龟兔赛跑) - HSK2 level, 24 parts
- Story sessions track progress through all parts
- **Context Panel**: Shows all previously seen story parts on the right side
- View complete stories before starting practice

### 🎯 Practice Sessions
- Mixed 5-sentence sessions
- HSK-level specific sessions
- Real-time scoring and progress tracking
- Character-level accuracy feedback

### 📊 Progress Tracking
- Dashboard showing progress by HSK level
- Character-level progress tracking (known, learning, failed)
- Visual progress indicators
- Detailed HSK level breakdowns

### 🔐 User Management
- Guest mode for quick practice
- User registration and login
- Progress synchronization across devices
- Supabase backend integration

## Getting Started

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chinese-dictation
```

2. Create and activate a virtual environment:
```bash
python -m venv xvenv
source xvenv/bin/activate  # On Windows: xvenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with your Supabase credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

5. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5001`

## Usage

### Main Menu
The main menu provides access to all features:
- **Start 5-Sentence Mixed Session**: Quick practice with random sentences
- **Common Phrases**: Browse and practice individual phrases by HSK level
- **Short Stories**: Choose from available stories for extended practice
- **Progress Dashboard**: View your learning progress
- **HSK Level Sessions**: Practice specific HSK levels

### Common Phrases
1. Select an HSK level (or "All Levels")
2. Browse available phrases with Chinese text, pinyin, and translations
3. Click "Practice" on any phrase to start dictation practice

### Short Stories
1. Choose a story from the available options
2. View the complete story broken into parts
3. Start a practice session to work through all parts sequentially
4. **Context Panel**: As you progress, see all previously completed parts on the right side
5. Track your progress and accuracy through the story

### Practice Sessions
- Listen to audio (for phrases)
- Type the Chinese characters you hear
- Get immediate feedback on accuracy
- See character-by-character corrections
- Track your score and progress

## File Structure

```
chinese-dictation/
├── dictation/
│   ├── __init__.py
│   ├── app_context.py      # Data loading and management
│   ├── corrector.py        # Character comparison logic
│   └── routes.py           # Flask routes and views
├── static/
│   ├── audio_files/        # Audio files for phrases
│   ├── images/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── menu.html
│   ├── phrases.html        # Phrases browsing interface
│   ├── stories.html        # Stories selection interface
│   ├── story_detail.html   # Individual story view
│   ├── story_summary.html  # Story session results
│   └── ...                 # Other templates
├── sentences.json          # Phrase/sentence data
├── stories.json            # Story data
├── hsk_characters.json     # HSK character data
└── run.py                  # Application entry point
```

## Data Format

### Stories JSON Structure
```json
{
  "story_id": {
    "title": "Story Title",
    "title_chinese": "故事标题",
    "difficulty": "HSK2",
    "parts": [
      {
        "id": "story_part_1",
        "chinese": "中文文本",
        "pinyin": "Pinyin text",
        "translation": "English translation",
        "part_number": 1
      }
    ]
  }
}
```

### Sentences JSON Structure
```json
{
  "sentence_id": {
    "chinese": "中文文本",
    "pinyin": "Pinyin text",
    "translation": "English translation",
    "hsk_level": 1
  }
}
```

## Contributing

To add new stories:
1. Add story data to `stories.json`
2. Follow the existing format with proper HSK level assignment
3. Break stories into manageable parts (1-3 sentences per part)
4. Include Chinese text, pinyin, and English translations
5. Generate audio files using `generate_short_stories_google.py`

To add new phrases:
1. Add sentence data to `sentences.json`
2. Assign appropriate HSK level
3. Generate corresponding audio files using `generate_audios_google.py`

## Audio Generation

### For Short Stories
```bash
python generate_short_stories_google.py
```
- Generates audio for all story parts in `stories.json`
- Each story uses a consistent random voice throughout all parts
- Audio files are saved as `{part_id}.mp3` in `static/audio_files/`

### For Phrases/Sentences
```bash
python generate_audios_google.py
```
- Generates audio for all sentences in `sentences.json`
- Each sentence uses a random voice
- Audio files are saved as `{sentence_id}_{difficulty}.mp3` in `static/audio_files/`

### Prerequisites for Audio Generation
1. Install Google Cloud TTS: `pip install google-cloud-texttospeech`
2. Set up Google Cloud credentials:
   - Create a service account and download the JSON key file
   - Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json`
   - OR run: `gcloud auth application-default login`

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript
- **Audio**: MP3 files for phrase pronunciation
- **Styling**: Custom CSS with colorblind-friendly design

## Accessibility

The application is designed with accessibility in mind:
- High-contrast color schemes
- Colorblind-friendly design
- Clear typography and spacing
- Keyboard navigation support

## License

[Add your license information here] 