"""
Usage:
    Run this script to generate audio files for conversations from `conversations.json` using gTTS.
    Each conversation will use different voices for speakers A and B to simulate a real conversation.
    
    Prerequisites:
    1. Install gTTS: pip install gTTS
    
    python generate_conversation_audios.py
"""
import os
import json
import random
from gtts import gTTS

# Configuration
JSON_PATH = "conversations.json"
OUTPUT_DIR = "static/audio_files"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def synthesize_text(text, output_path, speaker):
    """Synthesize text to speech using gTTS and save to file"""
    try:
        # Use gTTS with Mandarin Chinese
        tts = gTTS(text=text, lang='zh', slow=False)
        tts.save(output_path)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
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

    total_conversations = len(conversations)
    total_sentences = sum(len(conv["sentences"]) for conv in conversations)
    
    print(f"💬 Generating audio for {total_conversations} conversations with {total_sentences} total sentences...")
    print(f"🎭 Using gTTS with Mandarin Chinese for all speakers.")
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
        
        print(f"💬 [{conv_idx}/{total_conversations}] Conversation {conversation_id}: {topic}")
        print(f"   📊 HSK Level: {hsk_level}")
        
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
            
            print(f"   🎵 [{sent_idx}/{len(sentences)}] Generating: {filename}")
            print(f"      Speaker {speaker}: {text}")
            
            success_flag, error = synthesize_text(text, path, speaker)
            
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
        print("❌ No audio files were generated. Check your gTTS installation.")

if __name__ == "__main__":
    print("🎤 Using gTTS for Mandarin Chinese text-to-speech")
    print("🎭 All speakers will use the same gTTS voice (no speaker differentiation)")
    print("=" * 60)
    # Run the main function
    main() 