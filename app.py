from flask import Flask, render_template, request, session, redirect, url_for
from gtts import gTTS
import os
import json
import random
import unicodedata
import difflib

class DictationApp:
    def __init__(self, app, json_path="sentences.json", audio_dir="static/audio_files", level_threshold=3):
        self.app = app
        self.json_path = json_path
        self.audio_dir = audio_dir
        self.level_threshold = level_threshold
        self.sentences = self.load_sentences()
        self.register_routes()

    def load_sentences(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def ensure_audio(self, sid, text, difficulty):
        filename = f"{sid}_{difficulty}.mp3"
        filepath = os.path.join(self.audio_dir, filename)
        if not os.path.exists(filepath):
            os.makedirs(self.audio_dir, exist_ok=True)
            tts = gTTS(text=text, lang='zh')
            tts.save(filepath)
        return f"audio_files/{filename}"

    def strip_punctuation(self, text):
        return ''.join(
            ch for ch in text
            if not unicodedata.category(ch).startswith('P') and not ch.isspace()
        )

    def compare_sentences(self, user_input, correct_sentence):
        stripped_user = self.strip_punctuation(user_input)
        stripped_correct = self.strip_punctuation(correct_sentence)

        matcher = difflib.SequenceMatcher(None, stripped_user, stripped_correct)
        result = ""
        ui, ci = 0, 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                result += correct_sentence[ci:ci + (j2 - j1)]
                ui += (i2 - i1)
                ci += (j2 - j1)
            elif tag == 'replace':
                for k in range(j2 - j1):
                    u = user_input[ui + k] if ui + k < len(user_input) else ""
                    c = correct_sentence[ci + k] if ci + k < len(correct_sentence) else ""
                    result += f"<span style='color: red;'><del>{u}</del>{c}</span>"
                ui += (i2 - i1)
                ci += (j2 - j1)
            elif tag == 'insert':
                inserted = correct_sentence[ci:ci + (j2 - j1)]
                result += f"<span style='color: red;'>{inserted}</span>"
                ci += (j2 - j1)
            elif tag == 'delete':
                deleted = user_input[ui:ui + (i2 - i1)]
                result += f"<span style='color: red;'><del>{deleted}</del></span>"
                ui += (i2 - i1)

        return result

    def levenshtein(self, s1, s2):
        len_s1, len_s2 = len(s1), len(s2)
        dp = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]
        for i in range(len_s1 + 1): dp[i][0] = i
        for j in range(len_s2 + 1): dp[0][j] = j
        for i in range(1, len_s1 + 1):
            for j in range(1, len_s2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
        return dp[len_s1][len_s2]

    def get_random_session_ids(self, count=5):
        return random.sample(list(self.sentences.keys()), count)

    def register_routes(self):
        @self.app.route("/")
        def menu():
            grouped = {"easy": [], "medium": [], "hard": []}
            for sid, data in self.sentences.items():
                grouped[data["difficulty"]].append((sid, data["chinese"]))
            return render_template("menu.html", grouped=grouped)

        @self.app.route("/practice/<sid>", methods=["GET", "POST"])
        def practice(sid):
            if "score" not in session:
                session["score"] = 0
                session["level"] = 1
                session["correct_count"] = 0

            sentence = self.sentences[sid]["chinese"]
            difficulty = self.sentences[sid]["difficulty"]
            audio_file = self.ensure_audio(sid, sentence, difficulty)

            if request.method == "POST":
                user_input = request.form["user_input"].strip()
                clean_user = self.strip_punctuation(user_input)
                clean_correct = self.strip_punctuation(sentence)
                is_correct = clean_user == clean_correct
                correction_html = self.compare_sentences(user_input, sentence)
                distance = (len(clean_correct) - self.levenshtein(clean_user, clean_correct)) * 10 // len(clean_correct)

                if is_correct:
                    session["score"] += 1
                    session["correct_count"] += 1
                    if session["correct_count"] >= self.level_threshold:
                        session["level"] += 1
                        session["correct_count"] = 0

                return render_template("index.html",
                                       correct_sentence=sentence,
                                       result=("✅ Correct!" if is_correct else "❌ Try again."),
                                       correction=correction_html,
                                       distance=distance,
                                       score=session["score"],
                                       level=session["level"],
                                       show_result=True,
                                       audio_file=audio_file)

            return render_template("index.html",
                                   correct_sentence=sentence,
                                   audio_file=audio_file,
                                   score=session.get("score", 0),
                                   level=session.get("level", 1),
                                   show_result=False)

        @self.app.route("/session", methods=["GET", "POST"])
        def session_practice():
            if "session_ids" not in session:
                session["session_ids"] = self.get_random_session_ids()
                session["session_index"] = 0
                session["session_score"] = 0

            sid = session["session_ids"][session["session_index"]]
            sentence = self.sentences[sid]["chinese"]
            difficulty = self.sentences[sid]["difficulty"]
            audio_file = self.ensure_audio(sid, sentence, difficulty)

            if request.method == "POST":
                user_input = request.form["user_input"].strip()
                clean_user = self.strip_punctuation(user_input)
                clean_correct = self.strip_punctuation(sentence)
                is_correct = clean_user == clean_correct
                correction_html = self.compare_sentences(user_input, sentence)
                distance = (len(clean_correct) - self.levenshtein(clean_user, clean_correct)) * 10 // len(clean_correct)

                if is_correct:
                    session["session_score"] += 1

                return render_template("index.html",
                                       correct_sentence=sentence,
                                       result=("✅ Correct!" if is_correct else "❌ Try again."),
                                       correction=correction_html,
                                       distance=distance,
                                       score=session["session_score"],
                                       level=session.get("level", 1),
                                       show_result=True,
                                       audio_file=audio_file,
                                       session_mode=True,
                                       current=session["session_index"] + 1,
                                       total=5,
                                       show_next_button=True)

            return render_template("index.html",
                                   correct_sentence=sentence,
                                   audio_file=audio_file,
                                   score=session["session_score"],
                                   level=session.get("level", 1),
                                   show_result=False,
                                   session_mode=True,
                                   current=session["session_index"] + 1,
                                   total=5)

        @self.app.route("/session/result", methods=["GET", "POST"])
        def session_result():
            session["session_index"] += 1

            if session["session_index"] >= 5:
                score = session["session_score"]
                session.clear()
                return render_template("session_summary.html", score=score, total=5)

            sid = session["session_ids"][session["session_index"]]
            sentence = self.sentences[sid]["chinese"]
            difficulty = self.sentences[sid]["difficulty"]
            audio_file = self.ensure_audio(sid, sentence, difficulty)

            return render_template("index.html",
                                   correct_sentence=sentence,
                                   audio_file=audio_file,
                                   score=session["session_score"],
                                   level=session.get("level", 1),
                                   show_result=False,
                                   session_mode=True,
                                   current=session["session_index"] + 1,
                                   total=5)

# Inicialitzar Flask
app = Flask(__name__)
app.secret_key = "your-secret-key"
DictationApp(app)

if __name__ == "__main__":
    app.run(debug=True)
