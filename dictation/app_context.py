import json, os, random
from collections import defaultdict, OrderedDict

class DictationContext:
    def __init__(self, json_path="sentences.json", audio_dir="static/audio_files", hsk_path="hsk_characters.json", stories_path="stories.json", conversations_path="conversations.json"):
        self.sentences = self.load_sentences(json_path)
        self.audio_dir = audio_dir
        self.hsk_lookup = self.load_hsk(hsk_path)
        self.hsk_totals = self.count_hanzi_per_hsk()
        self.stories = self.load_stories(stories_path)
        self.conversations = self.load_conversations(conversations_path)

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

    def load_conversations(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                conversations = json.load(f)
                # Convert to dictionary with conversation_id as key
                return {str(conv["conversation_id"]): conv for conv in conversations}
        except FileNotFoundError:
            return {}

    def get_sentence(self, sid):
        return self.sentences.get(sid)

    def get_story(self, story_id):
        return self.stories.get(story_id)

    def get_conversation(self, conversation_id):
        return self.conversations.get(str(conversation_id))

    def get_story_part(self, story_id, part_id):
        story = self.get_story(story_id)
        if story:
            for part in story["parts"]:
                if part["id"] == part_id:
                    return part
        return None

    def get_conversation_sentence(self, conversation_id, sentence_id):
        conversation = self.get_conversation(conversation_id)
        if conversation:
            for sentence in conversation["sentences"]:
                if sentence["id"] == sentence_id:
                    return sentence
        return None

    def story_audio_path(self, story_id, part_id):
        filename = f"story_{story_id}_{part_id}.mp3"
        # Check new organized structure first
        new_path = os.path.join(self.audio_dir, "stories", filename)
        if os.path.exists(new_path):
            return f"audio_files/stories/{filename}"
        
        # Fallback to old structure for backward compatibility
        old_path = os.path.join(self.audio_dir, filename)
        return f"audio_files/{filename}" if os.path.exists(old_path) else None

    def story_all_audio_paths(self, story_id):
        story = self.get_story(story_id)
        if not story:
            return []
        audio_paths = []
        for part in story["parts"]:
            filename = f"story_{story_id}_{part['id']}.mp3"
            # Check new organized structure first
            new_path = os.path.join(self.audio_dir, "stories", filename)
            if os.path.exists(new_path):
                audio_paths.append(f"audio_files/stories/{filename}")
            # Fallback to old structure
            else:
                old_path = os.path.join(self.audio_dir, filename)
                if os.path.exists(old_path):
                    audio_paths.append(f"audio_files/{filename}")
        return audio_paths

    def conversation_audio_path(self, conversation_id, sentence_id):
        filename = f"conv_{conversation_id}_{sentence_id}.mp3"
        # Check new organized structure first
        new_path = os.path.join(self.audio_dir, "conversations", filename)
        if os.path.exists(new_path):
            return filename
        
        # Fallback to old structure for backward compatibility
        old_path = os.path.join(self.audio_dir, filename)
        return filename if os.path.exists(old_path) else None

    def conversation_all_audio_paths(self, conversation_id):
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        audio_paths = []
        for sentence in conversation["sentences"]:
            filename = f"conv_{conversation_id}_{sentence['id']}.mp3"
            # Check new organized structure first
            new_path = os.path.join(self.audio_dir, "conversations", filename)
            if os.path.exists(new_path):
                audio_paths.append(filename)
            # Fallback to old structure
            else:
                old_path = os.path.join(self.audio_dir, filename)
                if os.path.exists(old_path):
                    audio_paths.append(filename)
        return audio_paths

    def audio_path(self, sid, hsk_level):
        filename = f"{sid}_HSK{hsk_level}.mp3"
        # Check new organized structure first
        new_path = os.path.join(self.audio_dir, "hsk_characters", filename)
        if os.path.exists(new_path):
            return f"audio_files/hsk_characters/{filename}"
        
        # Fallback to old structure for backward compatibility
        old_path = os.path.join(self.audio_dir, filename)
        return f"audio_files/{filename}" if os.path.exists(old_path) else None

    def get_random_ids(self, count=5, level=None):
        sents = [sid for sid, s in self.sentences.items() if s["hsk_level"] == level] if level else list(self.sentences)
        return random.sample(sents, min(count, len(sents)))

    def get_phrases_by_level(self, level=None):
        """Get phrases/sentences filtered by HSK level"""
        if level:
            return {sid: s for sid, s in self.sentences.items() if s["hsk_level"] == int(level)}
        return self.sentences

    def count_hanzi_per_hsk(self):
        hsk_counts = defaultdict(int)
        for hanzi, level in self.hsk_lookup.items():
            hsk_counts[level] += 1
        return OrderedDict(
            sorted(hsk_counts.items(), key=lambda x: int(x[0]))
        )

