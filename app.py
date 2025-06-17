from flask import Flask, render_template, request, session
from gtts import gTTS
import os
import json

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

    def compare_sentences(self, user_input, correct_sentence):
        result = ""
        for u_char, c_char in zip(user_input, correct_sentence):
            if u_char == c_char:
                result += u_char
            else:
                result += f"<del>{u_char}</del>{c_char}"
        if len(user_input) < len(correct_sentence):
            result += f"<span style='color: red;'>{correct_sentence[len(user_input):]}</span>"
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
                is_correct = user_input == sentence
                correction_html = self.compare_sentences(user_input, sentence)
                distance = (len(sentence)-self.levenshtein(user_input, sentence))*10//len(sentence)

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

app = Flask(__name__)
app.secret_key = "your-secret-key"
DictationApp(app)

if __name__ == "__main__":
    app.run(debug=True)
