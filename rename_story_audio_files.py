import os
import re

AUDIO_DIR = "static/audio_files"

# Mapping from old prefix to new story ID
story_map = {
    "emperor": "1",
    "turtle": "2"
}

def rename_files():
    for filename in os.listdir(AUDIO_DIR):
        for old_prefix, story_id in story_map.items():
            match = re.match(rf"{old_prefix}_(\d+)\.mp3$", filename)
            if match:
                part_num = match.group(1)
                new_name = f"story_{story_id}_{part_num}.mp3"
                old_path = os.path.join(AUDIO_DIR, filename)
                new_path = os.path.join(AUDIO_DIR, new_name)
                print(f"Renaming {filename} -> {new_name}")
                os.rename(old_path, new_path)

if __name__ == "__main__":
    rename_files() 