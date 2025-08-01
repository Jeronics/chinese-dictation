"""
Usage:
    Run this script to generate all audio files from `sentences.json` using Google Cloud Text-to-Speech.
    It uses Google's neural TTS to synthesize high-quality Mandarin audio.
    
    Prerequisites:
    1. Install google-cloud-texttospeech: pip install google-cloud-texttospeech
    2. Set up Google Cloud credentials:
       - Create a service account and download the JSON key file
       - Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json
       OR
       - Run: gcloud auth application-default login
    
    python generate_audios_google.py
"""
import os
import json
import random
from google.cloud import texttospeech
from dotenv import load_dotenv
load_dotenv()

# Configuration
JSON_PATH = "../sentences.json"
OUTPUT_DIR = "../static/audio_files/hsk_characters"

# Chinese voice options
CHINESE_VOICES = {
    "cmn-CN-Standard-A": "Female (Standard)",
    "cmn-CN-Standard-B": "Male (Standard)",
    "cmn-CN-Standard-C": "Female (Standard)",
    "cmn-CN-Standard-D": "Male (Standard)",
    "cmn-CN-Wavenet-A": "Female (Neural)",
    "cmn-CN-Wavenet-B": "Male (Neural)",
    "cmn-CN-Wavenet-C": "Female (Neural)",
    "cmn-CN-Wavenet-D": "Male (Neural)"
}

# Default voice (you can change this)
DEFAULT_VOICE = "cmn-CN-Wavenet-A"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_client():
    """Create a Google Cloud TTS client"""
    try:
        client = texttospeech.TextToSpeechClient()
        return client
    except Exception as e:
        print(f"❌ Error creating Google Cloud client: {e}")
        print("Make sure you have set up Google Cloud credentials properly")
        return None

def synthesize_text(client, text, output_path, voice_name):
    """Synthesize text to speech and save to file"""
    try:
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="cmn-CN",
            name=voice_name
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,  # Slightly slower for better clarity
            pitch=0.0  # Normal pitch
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Write the response to the output file
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def list_available_voices():
    """List all available Chinese voices"""
    print("🎤 Available Chinese voices:")
    for voice_id, description in CHINESE_VOICES.items():
        print(f"  {voice_id}: {description}")
    print()

def main():
    # Check if Google Cloud credentials are set up
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json")):
        print("❌ Error: Google Cloud credentials not found")
        print("Please set up credentials using one of these methods:")
        print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("2. Run: gcloud auth application-default login")
        return

    # Create client
    client = create_client()
    if not client:
        return

    # Load the sentence data
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        sentences = json.load(f)

    total = len(sentences)
    success = 0
    failed = 0

    print(f"🔊 Generating audio for {total} sentences using Google Cloud TTS...")
    print(f"🎤 Voices will be chosen randomly for each sentence.")
    print()

    voice_list = list(CHINESE_VOICES.keys())

    # Generate audio for each sentence
    for i, (sid, data) in enumerate(sentences.items(), 1):
        text = data["chinese"]
        difficulty = data["difficulty"]
        filename = f"{sid}_{difficulty}.mp3"
        path = os.path.join(OUTPUT_DIR, filename)

        # Skip if file already exists
        if os.path.exists(path):
            print(f"⏩ [{i}/{total}] Skipped (already exists): {filename}")
            continue

        # Choose a random voice for this sentence
        random_voice = random.choice(voice_list)
        random_voice_desc = CHINESE_VOICES[random_voice]

        print(f"🎵 [{i}/{total}] Generating: {filename}")
        print(f"   Text: {text}")
        print(f"   Voice: {random_voice} ({random_voice_desc})")
        
        # Pass random_voice to the synthesis function
        success_flag, error = synthesize_text(client, text, path, voice_name=random_voice)
        
        if success_flag:
            print(f"   ✅ Saved: {filename}")
            success += 1
        else:
            print(f"   ❌ Failed: {error}")
            failed += 1

    print(f"\n🎉 Done. {success} files created, {failed} failed, {total - success - failed} skipped.")

if __name__ == "__main__":
    # Show available voices
    list_available_voices()
    print("Voices will be chosen randomly for each sentence.")
    # Run the main function
    main() 