import json, os, random

class DictationContext:
    def __init__(self, json_path="sentences.json", audio_dir="static/audio_files", hsk_path="hsk_characters.json"):
        self.sentences = self.load_sentences(json_path)
        self.audio_dir = audio_dir
        self.hsk_lookup = self.load_hsk(hsk_path)

    def load_sentences(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_hsk(self, path):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        return {item["hanzi"]: item["hsk_level"] for item in items}

    def get_sentence(self, sid):
        return self.sentences.get(sid)

    def audio_path(self, sid, difficulty):
        filename = f"{sid}_{difficulty}.mp3"
        path = os.path.join(self.audio_dir, filename)
        return f"audio_files/{filename}" if os.path.exists(path) else None

    def get_random_ids(self, count=5, level=None):
        sents = [sid for sid, s in self.sentences.items() if s["difficulty"] == level] if level else list(self.sentences)
        return random.sample(sents, min(count, len(sents)))
