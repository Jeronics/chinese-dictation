"""
Generate optimized audio files for web use.
This script creates smaller, web-optimized audio files with reduced bitrate and sample rate.
"""
import os
import json
import subprocess
from pathlib import Path
from gtts import gTTS

# Configuration
JSON_PATH = "conversations.json"
OUTPUT_DIR = "static/audio_files/conversations"
OPTIMIZED_DIR = "static/audio_files/optimized"

# Audio optimization settings
BITRATE = "64k"  # Reduced from default 128k
SAMPLE_RATE = "22050"  # Reduced from default 44100

def ensure_directories():
    """Ensure all necessary directories exist"""
    for dir_path in [OUTPUT_DIR, OPTIMIZED_DIR]:
        os.makedirs(dir_path, exist_ok=True)

def optimize_audio(input_path, output_path):
    """Optimize audio file using ffmpeg"""
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-acodec', 'mp3',
            '-b:a', BITRATE,
            '-ar', SAMPLE_RATE,
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, None
        else:
            return False, f"FFmpeg error: {result.stderr}"
    
    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg to optimize audio files."
    except Exception as e:
        return False, str(e)

def synthesize_text(text, output_path, speaker):
    """Synthesize text to speech using gTTS and optimize"""
    try:
        # Create temporary file
        temp_path = output_path.replace('.mp3', '_temp.mp3')
        
        # Use gTTS with Mandarin Chinese
        tts = gTTS(text=text, lang='zh', slow=False)
        tts.save(temp_path)
        
        # Optimize the audio
        success, error = optimize_audio(temp_path, output_path)
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if success:
            return True, None
        else:
            return False, error
            
    except Exception as e:
        return False, str(e)

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return round(os.path.getsize(filepath) / (1024 * 1024), 3)

def main():
    """Generate optimized audio files"""
    ensure_directories()
    
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
    
    print(f"🎵 Generating optimized audio for {total_conversations} conversations...")
    print(f"📊 Total sentences: {total_sentences}")
    print(f"⚙️  Optimization settings:")
    print(f"   🎚️  Bitrate: {BITRATE}")
    print(f"   📡 Sample rate: {SAMPLE_RATE} Hz")
    print(f"   📁 Output: {OPTIMIZED_DIR}")
    print()

    success_count = 0
    failed_count = 0
    total_original_size = 0
    total_optimized_size = 0

    # Generate audio for each conversation
    for conv_idx, conversation in enumerate(conversations, 1):
        conversation_id = conversation["conversation_id"]
        topic = conversation["topic"]
        sentences = conversation["sentences"]
        
        print(f"💬 [{conv_idx}/{total_conversations}] Conversation {conversation_id}: {topic}")
        
        # Create conversation directory
        conv_dir = os.path.join(OPTIMIZED_DIR, "conversations")
        os.makedirs(conv_dir, exist_ok=True)
        
        for sent_idx, sentence in enumerate(sentences, 1):
            sentence_id = sentence["id"]
            text = sentence["chinese"]
            speaker = sentence["speaker"]
            
            # Create filename
            filename = f"conv_{conversation_id}_{sentence_id}.mp3"
            output_path = os.path.join(conv_dir, filename)
            
            # Skip if optimized file already exists
            if os.path.exists(output_path):
                print(f"   ⏩ [{sent_idx}/{len(sentences)}] Skipped (already exists): {filename}")
                continue
            
            print(f"   🎵 [{sent_idx}/{len(sentences)}] Generating: {filename}")
            
            success, error = synthesize_text(text, output_path, speaker)
            
            if success:
                # Calculate size savings
                optimized_size = get_file_size_mb(output_path)
                total_optimized_size += optimized_size
                success_count += 1
                
                print(f"      ✅ Saved: {filename} ({optimized_size} MB)")
            else:
                print(f"      ❌ Failed: {error}")
                failed_count += 1
        
        print()

    # Generate summary
    print("📊 Generation Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   💾 Total optimized size: {total_optimized_size} MB")
    
    # Estimate original size (assuming 128k bitrate)
    estimated_original_size = total_optimized_size * 2  # Rough estimate
    savings = estimated_original_size - total_optimized_size
    savings_percent = (savings / estimated_original_size) * 100
    
    print(f"   📉 Estimated savings: {savings:.2f} MB ({savings_percent:.1f}%)")
    print(f"   📁 Files saved to: {OPTIMIZED_DIR}")

if __name__ == "__main__":
    main() 