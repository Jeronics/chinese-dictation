import json, os, random
from collections import defaultdict, OrderedDict

class DictationContext:
    def __init__(self, json_path="sentences.json", audio_dir="static/audio_files", hsk_path="hsk_characters.json", stories_path="stories.json"):
        self.sentences = self.load_sentences(json_path)
        self.audio_dir = audio_dir
        self.hsk_lookup = self.load_hsk(hsk_path)
        self.hsk_totals = self.count_hanzi_per_hsk()
        self.stories = self.load_stories(stories_path)

    def load_sentences(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_hsk(self, path):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        self.hsk_data = items  # guardar llista completa
        return {item["hanzi"]: item["hsk_level"] for item in items}

    def load_stories(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get_sentence(self, sid):
        return self.sentences.get(sid)

    def get_story(self, story_id):
        return self.stories.get(story_id)

    def get_story_part(self, story_id, part_id):
        story = self.get_story(story_id)
        if story:
            for part in story["parts"]:
                if part["id"] == part_id:
                    return part
        return None

    def audio_path(self, sid, difficulty):
        filename = f"{sid}_{difficulty}.mp3"
        path = os.path.join(self.audio_dir, filename)
        return f"audio_files/{filename}" if os.path.exists(path) else None

    def story_audio_path(self, story_id, part_number):
        """Get audio path for a story part using the new naming convention."""
        filename = f"story_{story_id}_{part_number}.mp3"
        print("AUDIO FILE!!!!!!!!!", self.audio_dir, filename)
        path = os.path.join(self.audio_dir, filename)
        print("PATH", path)
        return f"audio_files/{filename}" if os.path.exists(path) else None

    def story_all_audio_paths(self, story_id):
        """Return a list of audio file paths for all parts of a story, using the new naming convention."""
        story = self.get_story(story_id)
        if not story:
            return []
        audio_paths = []
        for idx, part in enumerate(story["parts"], 1):
            filename = f"story_{story_id}_{idx}.mp3"
            path = os.path.join(self.audio_dir, filename)
            if os.path.exists(path):
                audio_paths.append(f"audio_files/{filename}")
            else:
                # fallback: try old convention (e.g., emperor_1.mp3)
                fallback_filename = f"{story_id}_{idx}.mp3"
                fallback_path = os.path.join(self.audio_dir, fallback_filename)
                if os.path.exists(fallback_path):
                    audio_paths.append(f"audio_files/{fallback_filename}")
        return audio_paths

    def get_random_ids(self, count=5, level=None):
        sents = [sid for sid, s in self.sentences.items() if s["difficulty"] == level] if level else list(self.sentences)
        return random.sample(sents, min(count, len(sents)))

    def get_phrases_by_level(self, level=None):
        """Get phrases/sentences filtered by HSK level"""
        if level:
            return {sid: s for sid, s in self.sentences.items() if s["difficulty"] == level}
        return self.sentences

    def count_hanzi_per_hsk(self):
        hsk_counts = defaultdict(int)
        for hanzi, level in self.hsk_lookup.items():
            hsk_counts[level] += 1
        return OrderedDict(
            sorted(hsk_counts.items(), key=lambda x: int(x[0]))
        )

