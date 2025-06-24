"""
Usage:
    Run this script to generate all audio files from `sentences.json`.
    It uses gTTS to synthesize Mandarin audio and saves each file to static/audio_files/.
    Only run this locally — never call gTTS on the deployed app!

    python generate_audios.py
"""

import os
import json
from gtts import gTTS

# Configuration
JSON_PATH = "sentences.json"
OUTPUT_DIR = "static/audio_files"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the sentence data
with open(JSON_PATH, "r", encoding="utf-8") as f:
    sentences = json.load(f)

total = len(sentences)
success = 0
failed = 0

print(f"🔊 Generating audio for {total} sentences...")

# Generate audio for each sentence
for sid, data in sentences.items():
    text = data["chinese"]
    difficulty = data["difficulty"]
    filename = f"{sid}_{difficulty}.mp3"
    path = os.path.join(OUTPUT_DIR, filename)

    # Skip if file already exists
    if os.path.exists(path):
        print(f"⏩ Skipped (already exists): {filename}")
        continue

    try:
        tts = gTTS(text=text, lang='zh')
        tts.save(path)
        print(f"✅ Saved: {filename}")
        success += 1
    except Exception as e:
        print(f"❌ Failed {sid}: {e}")
        failed += 1

print(f"\n🎉 Done. {success} files created, {failed} failed, {total - success - failed} skipped.")
