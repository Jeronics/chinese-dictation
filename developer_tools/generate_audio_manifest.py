"""
Generate audio manifest for lazy loading and optimization.
This script creates a JSON manifest of all audio files with metadata.
"""
import os
import json
from pathlib import Path

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return round(os.path.getsize(filepath) / (1024 * 1024), 3)

def generate_audio_manifest():
    """Generate manifest of all audio files"""
    audio_dir = Path("static/audio_files")
    manifest = {
        "hsk_characters": {},
        "conversations": {},
        "stories": {},
        "total_files": 0,
        "total_size_mb": 0
    }
    
    # Process HSK characters
    hsk_dir = audio_dir / "hsk_characters"
    if hsk_dir.exists():
        for file in hsk_dir.glob("*.mp3"):
            size_mb = get_file_size_mb(file)
            manifest["hsk_characters"][file.name] = {
                "size_mb": size_mb,
                "path": f"hsk_characters/{file.name}"
            }
            manifest["total_files"] += 1
            manifest["total_size_mb"] += size_mb
    
    # Process conversations
    conv_dir = audio_dir / "conversations"
    if conv_dir.exists():
        conversations = {}
        for file in conv_dir.glob("*.mp3"):
            size_mb = get_file_size_mb(file)
            conv_id = file.stem.split('_')[1]  # Extract conversation ID
            
            if conv_id not in conversations:
                conversations[conv_id] = {
                    "files": {},
                    "total_size_mb": 0,
                    "file_count": 0
                }
            
            conversations[conv_id]["files"][file.name] = {
                "size_mb": size_mb,
                "path": f"conversations/{file.name}"
            }
            conversations[conv_id]["total_size_mb"] += size_mb
            conversations[conv_id]["file_count"] += 1
            manifest["total_files"] += 1
            manifest["total_size_mb"] += size_mb
        
        manifest["conversations"] = conversations
    
    # Process stories
    story_dir = audio_dir / "stories"
    if story_dir.exists():
        stories = {}
        for file in story_dir.glob("*.mp3"):
            size_mb = get_file_size_mb(file)
            story_id = file.stem.split('_')[1]  # Extract story ID
            
            if story_id not in stories:
                stories[story_id] = {
                    "files": {},
                    "total_size_mb": 0,
                    "file_count": 0
                }
            
            stories[story_id]["files"][file.name] = {
                "size_mb": size_mb,
                "path": f"stories/{file.name}"
            }
            stories[story_id]["total_size_mb"] += size_mb
            stories[story_id]["file_count"] += 1
            manifest["total_files"] += 1
            manifest["total_size_mb"] += size_mb
        
        manifest["stories"] = stories
    
    # Round total size
    manifest["total_size_mb"] = round(manifest["total_size_mb"], 2)
    
    return manifest

def main():
    """Generate and save audio manifest"""
    print("🎵 Generating audio manifest...")
    
    manifest = generate_audio_manifest()
    
    # Save manifest
    with open("static/audio_files/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Manifest generated:")
    print(f"   📁 Total files: {manifest['total_files']}")
    print(f"   💾 Total size: {manifest['total_size_mb']} MB")
    print(f"   🎯 HSK characters: {len(manifest['hsk_characters'])}")
    print(f"   💬 Conversations: {len(manifest['conversations'])}")
    print(f"   📖 Stories: {len(manifest['stories'])}")
    print(f"   📄 Saved to: static/audio_files/manifest.json")

if __name__ == "__main__":
    main() 