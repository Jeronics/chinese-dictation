"""
Usage:
    Run this script to generate all audio files from `sentences.json` using Azure Cognitive Services.
    It uses Azure's neural TTS to synthesize high-quality Mandarin audio.
    
    Prerequisites:
    1. Install azure-cognitiveservices-speech: pip install azure-cognitiveservices-speech
    2. Set environment variables:
       - AZURE_SPEECH_KEY: Your Azure Speech Service key
       - AZURE_SPEECH_REGION: Your Azure Speech Service region (e.g., 'eastus')
    
    python generate_audios_azure.py
"""

import os
import json
import asyncio
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
from azure.cognitiveservices.speech.audio import AudioOutputConfig

# Configuration
JSON_PATH = "sentences.json"
OUTPUT_DIR = "static/audio_files"

# Azure Speech Service configuration
AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION")

if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
    print("❌ Error: Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables")
    print("Get your key from: https://portal.azure.com/ -> Cognitive Services -> Speech Service")
    exit(1)

# Chinese voice options (you can change these)
CHINESE_VOICES = {
    "zh-CN-XiaoxiaoNeural": "Xiaoxiao (Female, Young)",
    "zh-CN-YunxiNeural": "Yunxi (Male, Young)", 
    "zh-CN-YunyangNeural": "Yunyang (Male, News)",
    "zh-CN-XiaochenNeural": "Xiaochen (Female, Friendly)",
    "zh-CN-YunfengNeural": "Yunfeng (Male, Calm)",
    "zh-CN-XiaohanNeural": "Xiaohan (Female, Gentle)",
    "zh-CN-XiaomoNeural": "Xiaomo (Female, Energetic)",
    "zh-CN-XiaoxuanNeural": "Xiaoxuan (Female, Mature)",
    "zh-CN-XiaoyanNeural": "Xiaoyan (Female, Professional)",
    "zh-CN-XiaoyouNeural": "Xiaoyou (Female, Young)",
    "zh-CN-YunjianNeural": "Yunjian (Male, Professional)"
}

# Default voice (you can change this)
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_synthesizer(voice_name=DEFAULT_VOICE):
    """Create a speech synthesizer with the specified voice"""
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice_name
    
    # Configure audio output
    audio_config = AudioConfig(filename=None)  # We'll set filename per synthesis
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    return synthesizer

async def synthesize_text(synthesizer, text, output_path):
    """Synthesize text to speech and save to file"""
    try:
        # Configure audio output for this specific file
        audio_config = AudioOutputConfig(filename=output_path)
        synthesizer = SpeechSynthesizer(
            speech_config=synthesizer.speech_config, 
            audio_config=audio_config
        )
        
        # Synthesize the text
        result = await synthesizer.speak_text_async(text)
        
        if result.reason.name == "SynthesizingAudioCompleted":
            return True, None
        else:
            return False, f"Synthesis failed: {result.reason}"
            
    except Exception as e:
        return False, str(e)

def list_available_voices():
    """List all available Chinese voices"""
    print("🎤 Available Chinese voices:")
    for voice_id, description in CHINESE_VOICES.items():
        print(f"  {voice_id}: {description}")
    print()

async def main():
    # Load the sentence data
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        sentences = json.load(f)

    total = len(sentences)
    success = 0
    failed = 0

    print(f"🔊 Generating audio for {total} sentences using Azure TTS...")
    print(f"🎤 Using voice: {DEFAULT_VOICE} ({CHINESE_VOICES[DEFAULT_VOICE]})")
    print()

    # Create synthesizer
    synthesizer = create_synthesizer()

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

        print(f"🎵 [{i}/{total}] Generating: {filename}")
        print(f"   Text: {text}")
        
        success_flag, error = await synthesize_text(synthesizer, text, path)
        
        if success_flag:
            print(f"   ✅ Saved: {filename}")
            success += 1
        else:
            print(f"   ❌ Failed: {error}")
            failed += 1
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)

    print(f"\n🎉 Done. {success} files created, {failed} failed, {total - success - failed} skipped.")

if __name__ == "__main__":
    # Show available voices
    list_available_voices()
    
    # Ask user if they want to change the voice
    selected_voice = DEFAULT_VOICE
    print(f"Current voice: {selected_voice}")
    change_voice = input("Do you want to change the voice? (y/n): ").lower().strip()
    
    if change_voice == 'y':
        print("\nAvailable voices:")
        for i, (voice_id, description) in enumerate(CHINESE_VOICES.items(), 1):
            print(f"{i}. {voice_id}: {description}")
        
        try:
            choice = int(input(f"\nSelect voice (1-{len(CHINESE_VOICES)}): ")) - 1
            voice_list = list(CHINESE_VOICES.keys())
            if 0 <= choice < len(voice_list):
                selected_voice = voice_list[choice]
                print(f"Selected: {selected_voice}")
            else:
                print("Invalid choice, using default voice")
        except ValueError:
            print("Invalid input, using default voice")
    
    # Update the default voice for this session
    DEFAULT_VOICE = selected_voice
    
    # Run the main function
    asyncio.run(main()) 