import json

STORIES_PATH = "stories.json"

with open(STORIES_PATH, "r", encoding="utf-8") as f:
    stories = json.load(f)

new_stories = {}
key_map = {}
for idx, (old_key, story) in enumerate(stories.items(), 1):
    new_key = str(idx)
    new_stories[new_key] = story
    key_map[old_key] = new_key

with open(STORIES_PATH, "w", encoding="utf-8") as f:
    json.dump(new_stories, f, ensure_ascii=False, indent=2)

print("stories.json keys updated to numeric:")
for old, new in key_map.items():
    print(f"  {old} -> {new}") 