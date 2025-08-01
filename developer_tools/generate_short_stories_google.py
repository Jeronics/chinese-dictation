"""
Usage:
    Run this script to generate audio files for short stories from `stories.json` using Google Cloud Text-to-Speech.
    Each story will use a random voice, but all parts within the same story will use the same voice for consistency.
    
    Prerequisites:
    1. Install google-cloud-texttospeech: pip install google-cloud-texttospeech
    2. Set up Google Cloud credentials:
       - Create a service account and download the JSON key file
       - Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json
       OR
       - Run: gcloud auth application-default login
    
    python generate_short_stories_google.py
"""
import os
import json
import random
from google.cloud import texttospeech
from dotenv import load_dotenv
load_dotenv()

# Configuration
JSON_PATH = "../stories.json"
OUTPUT_DIR = "../static/audio_files/stories"

# Chinese voice options - using more realistic neural voices
CHINESE_VOICES = {
    "cmn-CN-Wavenet-A": "Female (Neural - Clear)",
    "cmn-CN-Wavenet-B": "Male (Neural - Deep)",
    "cmn-CN-Wavenet-C": "Female (Neural - Warm)",
    "cmn-CN-Wavenet-D": "Male (Neural - Friendly)",
    "cmn-CN-Standard-A": "Female (Standard - Clear)",
    "cmn-CN-Standard-B": "Male (Standard - Deep)",
    "cmn-CN-Standard-C": "Female (Standard - Warm)",
    "cmn-CN-Standard-D": "Male (Standard - Friendly)"
}

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
            speaking_rate=0.85,  # Slightly slower for better clarity in stories
            pitch=0.0,  # Normal pitch
            effects_profile_id=["headphone-class-device"]  # Optimized for headphones
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
    print("🎤 Available Chinese voices for stories:")
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

    # Load the stories data
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            stories = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {JSON_PATH} not found")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {JSON_PATH}: {e}")
        return

    voice_list = list(CHINESE_VOICES.keys())
    total_stories = len(stories)
    total_parts = sum(len(story["parts"]) for story in stories.values())
    
    print(f"📚 Generating audio for {total_stories} stories with {total_parts} total parts...")
    print(f"🎤 Each story will use a consistent random voice throughout all parts.")
    print()

    success_stories = 0
    failed_stories = 0
    success_parts = 0
    failed_parts = 0
    skipped_parts = 0

    # Generate audio for each story
    for story_idx, (story_id, story) in enumerate(stories.items(), 1):
        story_title = story["title"]
        story_title_chinese = story["title_chinese"]
        difficulty = story["difficulty"]
        parts = story["parts"]
        
        # Choose a random voice for this entire story
        story_voice = random.choice(voice_list)
        story_voice_desc = CHINESE_VOICES[story_voice]
        
        
        story_success = 0
        story_failed = 0
        
        # Generate audio for each part of the story
        for part_idx, part in enumerate(parts, 1):
            part["id"] = f"story_{story_id}_{part_idx}"
            text = part["chinese"]
            part_number = part_idx
            
            # Create filename: story_<story_id>_<part_number>.mp3
            filename = f"story_{story_id}_{part_number}.mp3"
            path = os.path.join(OUTPUT_DIR, filename)
            
            # Skip if file already exists
            if os.path.exists(path):
                # print(f"   ⏩ [{part_idx}/{len(parts)}] Skipped (already exists): {filename}")
                skipped_parts += 1
                continue
            
            # print(f"   🎵 [{part_idx}/{len(parts)}] Generating: {filename}")
            # print(f"      Text: {text}")
            
            # Use the same voice for all parts of this story
            success_flag, error = synthesize_text(client, text, path, voice_name=story_voice)
            
            if success_flag:
                # print(f"      ✅ Saved: {filename}")
                story_success += 1
                success_parts += 1
            else:
                # print(f"      ❌ Failed: {error}")
                story_failed += 1
                failed_parts += 1
        
        # Story summary
        if story_success == len(parts):
            # print(f"   🎉 Story complete: {story_success}/{len(parts)} parts generated")
            success_stories += 1
        else:
            # print(f"   ⚠️  Story incomplete: {story_success}/{len(parts)} parts generated, {story_failed} failed")
            failed_stories += 1
        
        # print()

    # Final summary
    print("=" * 60)
    print("🎉 GENERATION COMPLETE")
    print("=" * 60)
    print(f"📚 Stories: {success_stories} complete, {failed_stories} incomplete")
    print(f"🎵 Parts: {success_parts} generated, {failed_parts} failed, {skipped_parts} skipped")
    print(f"📁 Audio files saved to: {OUTPUT_DIR}")
    print()
    
    if success_parts > 0:
        print("✅ Audio files are ready for use in the application!")
        print("   The stories will now have audio playback in practice sessions.")
    else:
        print("❌ No audio files were generated. Check your Google Cloud setup.")

if __name__ == "__main__":
    # Show available voices
    list_available_voices()
    print("Each story will use a consistent random voice throughout all parts.")
    print("=" * 60)
    # Run the main function
    main() 