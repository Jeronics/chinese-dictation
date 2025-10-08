"""
Usage:
    Run this script to generate audio files for conversations from `conversations.json` using Google Cloud Text-to-Speech.
    Each conversation will use different voices for speakers A and B to simulate a real conversation.
    
    Prerequisites:
    1. Install google-cloud-texttospeech: pip install google-cloud-texttospeech
    2. Set up Google Cloud credentials:
       - Create a service account and download the JSON key file
       - Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json
       OR
       - Run: gcloud auth application-default login
    
    python generate_conversation_audios_google.py
"""
import os
import json
import random
from google.cloud import texttospeech
from dotenv import load_dotenv
load_dotenv()

# Configuration
JSON_PATH = "../conversations.json"
OUTPUT_DIR = "../static/audio_files/conversations"

# Chinese voice options - using more realistic neural voices
MALE_VOICES = {
    "cmn-CN-Wavenet-B": "Male (Neural - Deep)",
    "cmn-CN-Wavenet-D": "Male (Neural - Friendly)",
    "cmn-CN-Standard-B": "Male (Standard - Deep)",
    "cmn-CN-Standard-D": "Male (Standard - Friendly)"
}

FEMALE_VOICES = {
    "cmn-CN-Wavenet-A": "Female (Neural - Clear)",
    "cmn-CN-Wavenet-C": "Female (Neural - Warm)",
    "cmn-CN-Standard-A": "Female (Standard - Clear)",
    "cmn-CN-Standard-C": "Female (Standard - Warm)"
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
            speaking_rate=0.9,  # Slightly slower for better clarity in conversations
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
    print("🎤 Available Chinese voices for conversations:")
    print("\n👨 Male Voices:")
    for voice_id, description in MALE_VOICES.items():
        print(f"  {voice_id}: {description}")
    print("\n👩 Female Voices:")
    for voice_id, description in FEMALE_VOICES.items():
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

    # Load the conversations data
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            conversations = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {JSON_PATH} not found")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {JSON_PATH}: {e}")
        return

    male_voice_list = list(MALE_VOICES.keys())
    female_voice_list = list(FEMALE_VOICES.keys())
    
    total_conversations = len(conversations)
    total_sentences = sum(len(conv["sentences"]) for conv in conversations)
    
    print(f"💬 Generating audio for {total_conversations} conversations with {total_sentences} total sentences...")
    print(f"🎭 Each conversation will use different male and female voices for speakers A and B.")
    print()

    success_conversations = 0
    failed_conversations = 0
    success_sentences = 0
    failed_sentences = 0
    skipped_sentences = 0

    # Generate audio for each conversation
    for conv_idx, conversation in enumerate(conversations, 1):
        conversation_id = conversation["conversation_id"]
        topic = conversation["topic"]
        hsk_level = conversation["hsk_level"]
        sentences = conversation["sentences"]
        
        # Choose random voices for this conversation (one male, one female)
        voice_a = random.choice(male_voice_list if random.random() > 0.5 else female_voice_list)
        # Make speaker B the opposite gender for variety
        voice_b = random.choice(female_voice_list if voice_a in male_voice_list else male_voice_list)
        
        voice_a_desc = MALE_VOICES.get(voice_a, FEMALE_VOICES.get(voice_a))
        voice_b_desc = MALE_VOICES.get(voice_b, FEMALE_VOICES.get(voice_b))
        
        print(f"💬 [{conv_idx}/{total_conversations}] Conversation {conversation_id}: {topic}")
        print(f"   📊 HSK Level: {hsk_level}")
        print(f"   🎭 Speaker A: {voice_a} ({voice_a_desc})")
        print(f"   🎭 Speaker B: {voice_b} ({voice_b_desc})")
        
        conv_success = 0
        conv_failed = 0
        
        # Generate audio for each sentence in the conversation
        for sent_idx, sentence in enumerate(sentences, 1):
            sentence_id = sentence["id"]
            text = sentence["chinese"]
            speaker = sentence["speaker"]
            
            # Create filename: conv_<conversation_id>_<sentence_id>.mp3
            filename = f"conv_{conversation_id}_{sentence_id}.mp3"
            path = os.path.join(OUTPUT_DIR, filename)
            
            # Skip if file already exists
            if os.path.exists(path):
                print(f"   ⏩ [{sent_idx}/{len(sentences)}] Skipped (already exists): {filename}")
                skipped_sentences += 1
                continue
            
            # Select voice based on speaker
            voice_name = voice_a if speaker == "A" else voice_b
            
            print(f"   🎵 [{sent_idx}/{len(sentences)}] Generating: {filename}")
            print(f"      Speaker {speaker}: {text}")
            
            success_flag, error = synthesize_text(client, text, path, voice_name)
            
            if success_flag:
                print(f"      ✅ Saved: {filename}")
                conv_success += 1
                success_sentences += 1
            else:
                print(f"      ❌ Failed: {error}")
                conv_failed += 1
                failed_sentences += 1
        
        # Conversation summary
        if conv_success == len(sentences):
            print(f"   🎉 Conversation complete: {conv_success}/{len(sentences)} sentences generated")
            success_conversations += 1
        else:
            print(f"   ⚠️  Conversation incomplete: {conv_success}/{len(sentences)} sentences generated, {conv_failed} failed")
            failed_conversations += 1
        
        print()

    # Final summary
    print("=" * 60)
    print("🎉 GENERATION COMPLETE")
    print("=" * 60)
    print(f"💬 Conversations: {success_conversations} complete, {failed_conversations} incomplete")
    print(f"🎵 Sentences: {success_sentences} generated, {failed_sentences} failed, {skipped_sentences} skipped")
    print(f"📁 Audio files saved to: {OUTPUT_DIR}")
    print()
    
    if success_sentences > 0:
        print("✅ Audio files are ready for use in the application!")
        print("   The conversations will now have audio playback in practice sessions.")
    else:
        print("❌ No audio files were generated. Check your Google Cloud setup.")

if __name__ == "__main__":
    # Show available voices
    list_available_voices()
    print("Each conversation will use different male and female voices for speakers A and B.")
    print("=" * 60)
    # Run the main function
    main()


