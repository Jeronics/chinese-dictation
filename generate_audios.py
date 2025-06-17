import json
import os
from gtts import gTTS

JSON_PATH = "sentences.json"
OUTPUT_DIR = "static/audio_files"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    sentences = json.load(f)

for key, value in sentences.items():
    text = value["text"]
    difficulty = value["difficulty"]
    filename = f"{key}_{difficulty}.mp3"
    path = os.path.join(OUTPUT_DIR, filename)

    try:
        tts = gTTS(text=text, lang='zh')
        tts.save(path)
        print(f"✅ Saved {path}")
    except Exception as e:
        print(f"❌ Failed {key}: {e}")
