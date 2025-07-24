from flask import session
from .corrector import Corrector
from .db_helpers import batch_update_character_progress
import logging

class BaseDictationSession:
    def __init__(self, ctx):
        self.ctx = ctx
        self.session = session
        self.corrector = Corrector()

    def get_current_index(self):
        return self.session.get(self.index_key, 0)

    def get_score(self):
        return self.session.get(self.score_key, 0)

    def get_ids(self):
        return self.session.get(self.ids_key, [])

    def get_current_id(self):
        ids = self.get_ids()
        idx = self.get_current_index()
        return ids[idx] if idx < len(ids) else None

    def advance(self):
        self.session[self.index_key] = self.get_current_index() + 1

    def is_finished(self):
        return self.get_current_index() >= len(self.get_ids())

    def get_context(self):
        raise NotImplementedError

    def update_score(self, user_input):
        raise NotImplementedError

    def set_accuracy(self, accuracy):
        if "accuracy_scores" not in self.session:
            self.session["accuracy_scores"] = []
        self.session["accuracy_scores"].append(accuracy)

    def get_last_session_mean(self):
        scores = self.session.get("accuracy_scores", [])
        if not scores:
            return 0
        n = len(scores)
        start = n - (n % 5 if n % 5 != 0 else 5)
        last_session = scores[start:]
        return round(sum(last_session) / len(last_session), 1) if last_session else 0

    def get_total_accuracy_mean(self):
        scores = self.session.get("accuracy_scores", [])
        return round(sum(scores) / len(scores), 1) if scores else 0

    def get_gradient_feedback(self, accuracy):
        if accuracy == 100:
            return ("Perfect!", "#00ff00")  # Extremely bright green
        elif accuracy >= 85:
            return ("Very Good!", "#00cc00")  # Bright green
        elif accuracy >= 70:
            return ("Good!", "#008000")       # Dull green  
        elif accuracy >= 50:
            return ("Getting there..", "#fbc02d") # High-contrast yellow
        elif accuracy >= 25:
            return ("Needs Practice..", "#ffa500") # orange
        else:
            return ("Poor..", "#c62828")        # red

class HSKSession(BaseDictationSession):
    ids_key = "session_ids"
    index_key = "session_index"
    score_key = "session_score"

    def get_current_item(self):
        sid = self.get_current_id()
        return self.ctx.get_sentence(sid)

    def get_context(self):
        item = self.get_current_item()
        hsk_level = item["hsk_level"]
        return {
            "correct_sentence": item["chinese"],
            "audio_file": self.ctx.audio_path(item["id"], hsk_level),
            "score": self.get_score(),
            "level": hsk_level,
            "difficulty": f"HSK{hsk_level}",
            "show_result": False,
            "session_mode": True,
            "current": self.get_current_index() + 1,
            "total": len(self.get_ids()),
        }

    def update_score(self, user_input):
        item = self.get_current_item()
        hsk_level = item["hsk_level"]
        correction, stripped_user, stripped_correct, correct_segments = self.corrector.compare(user_input, item["chinese"])
        accuracy = round(len(correct_segments)/len(stripped_correct)*100) if len(stripped_correct) > 0 else 0
        feedback, feedback_color = self.get_gradient_feedback(accuracy)
        
        # Append accuracy scores to session for later averaging
        self.set_accuracy(accuracy)

        user_id = self.session.get("user_id")
        # Update character progress for logged-in users
        if user_id:
            hanzi_updates = []
            for hanzi in set(item["chinese"]):
                match = next((entry for entry in self.ctx.hsk_data if entry["hanzi"] == hanzi), None)
                if match:
                    hsk_level = match["hsk_level"]
                    if isinstance(hsk_level, str) and hsk_level.startswith("HSK"):
                        hsk_level_int = int(hsk_level.replace("HSK", ""))
                    else:
                        hsk_level_int = int(hsk_level)
                    correct = hanzi in correct_segments
                    hanzi_updates.append({
                        "hanzi": hanzi,
                        "hsk_level": hsk_level_int,
                        "correct": correct
                    })
            if hanzi_updates:
                batch_update_character_progress(user_id, hanzi_updates)
        # Calculate running average accuracy for display
        return {
            "correct_sentence": item["chinese"],
            "result": feedback,
            "result_color": feedback_color,
            "correction": correction,
            "accuracy": accuracy,
            "level": hsk_level,
            "show_result": True,
            "audio_file": self.ctx.audio_path(item["id"], hsk_level),
            "translation": item["translation"],
            "pinyin": item["pinyin"],
            "session_mode": True,
            "current": self.get_current_index() + 1,
            "total": len(self.get_ids()),
            "show_next_button": True,
            "story_mode": False,
            "user_input": user_input
        }

class StorySession(BaseDictationSession):
    ids_key = "story_session_ids"
    index_key = "story_session_index"
    score_key = "story_session_score"

    def get_current_item(self):
        story_id = self.session.get("story_id")
        part_id = self.get_current_id()
        return self.ctx.get_story_part(story_id, part_id)

    def get_context(self):
        part = self.get_current_item()
        story_id = self.session.get("story_id")
        story = self.ctx.get_story(story_id)
        hsk_level = story["hsk_level"]
        return {
            "correct_sentence": part["chinese"],
            "audio_file": self.ctx.story_audio_path(story_id, part["id"]),
            "score": self.get_score(),
            "level": hsk_level,
            "difficulty": f"HSK{hsk_level}",
            "show_result": False,
            "session_mode": True,
            "current": self.get_current_index() + 1,
            "total": len(self.get_ids()),
            "story_mode": True,
            "story_title": story["title"],
            "story_context": story["parts"][:self.get_current_index()],
            "story_audio_files": self.ctx.story_all_audio_paths(story_id),
            "group_scores": self.session.get("story_group_scores", [])
        }

    def update_score(self, user_input):
        part = self.get_current_item()
        story_id = self.session.get("story_id")
        story = self.ctx.get_story(story_id)
        hsk_level = story["hsk_level"]
        correction, stripped_user, stripped_correct, correct_segments = self.corrector.compare(user_input, part["chinese"])
        accuracy = round(len(correct_segments)/len(stripped_correct)*100) if len(stripped_correct) > 0 else 0
        feedback, feedback_color = self.get_gradient_feedback(accuracy)
        # Only increment score if accuracy >= 70
        if accuracy >= 70:
            self.session[self.score_key] += 1
        # Store per-sentence correctness for group scoring
        idx = self.get_current_index()
        self.session[f"story_part_{idx}_correct"] = (accuracy >= 70)
        user_id = self.session.get("user_id")
        # Update character progress for logged-in users
        if user_id:
            hanzi_updates = []
            for hanzi in set(part["chinese"]):
                match = next((entry for entry in self.ctx.hsk_data if entry["hanzi"] == hanzi), None)
                if match:
                    hsk_level = match["hsk_level"]
                    if isinstance(hsk_level, str) and hsk_level.startswith("HSK"):
                        hsk_level_int = int(hsk_level.replace("HSK", ""))
                    else:
                        hsk_level_int = int(hsk_level)
                    correct = hanzi in correct_segments
                    hanzi_updates.append({
                        "hanzi": hanzi,
                        "hsk_level": hsk_level_int,
                        "correct": correct
                    })
            if hanzi_updates:
                batch_update_character_progress(user_id, hanzi_updates)
            # Store accuracy scores in session for later averaging
            if "accuracy_scores" not in self.session:
                self.session["accuracy_scores"] = []
            self.session["accuracy_scores"].append(accuracy)
        # Calculate running average accuracy for display
        accuracy_scores = self.session.get("accuracy_scores", [])
        average_accuracy = round(sum(accuracy_scores) / len(accuracy_scores), 1) if accuracy_scores else 0
        return {
            "correct_sentence": part["chinese"],
            "result": feedback,
            "result_color": feedback_color,
            "correction": correction,
            "accuracy": accuracy,
            "average_accuracy": average_accuracy,
            "score": self.get_score(),
            "level": hsk_level,
            "difficulty": f"HSK{hsk_level}",
            "show_result": True,
            "audio_file": self.ctx.story_audio_path(story_id, part["id"]),
            "translation": part["translation"],
            "pinyin": part["pinyin"],
            "session_mode": True,
            "current": self.get_current_index() + 1,
            "total": len(self.get_ids()),
            "show_next_button": True,
            "story_mode": True,
            "story_context": story["parts"][:self.get_current_index()],
            "story_title": story["title"],
            "story_audio_files": self.ctx.story_all_audio_paths(story_id),
            "user_input": user_input,
            "story_id": story_id,
            "part_id": part["id"]
        } 