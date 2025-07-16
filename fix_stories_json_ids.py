import json

STORIES_PATH = "stories.json"

with open(STORIES_PATH, "r", encoding="utf-8") as f:
    stories = json.load(f)

updated = False
for story_id, story in stories.items():
    for idx, part in enumerate(story["parts"], 1):
        new_id = f"story_{story_id}_{idx}"
        if part["id"] != new_id:
            print(f"Updating part id: {part['id']} -> {new_id}")
            part["id"] = new_id
            updated = True

if updated:
    with open(STORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    print("stories.json updated!")
else:
    print("No changes needed.") 