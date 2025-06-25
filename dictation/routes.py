from flask import Blueprint, render_template, request, session
from .app_context import DictationContext
from .corrector import Corrector

dictation_bp = Blueprint("dictation", __name__)
ctx = DictationContext()
corrector = Corrector()

def render_dictation_result(user_input, sentence_data, session_score_key, show_next=False, current=None, total=None):
    correction, stripped_user, stripped_correct = corrector.compare(user_input, sentence_data["chinese"])
    lev = corrector.levenshtein(stripped_user, stripped_correct)
    distance = (len(stripped_correct) - lev) * 10 // len(stripped_correct) if stripped_correct else 0
    is_correct = stripped_user == stripped_correct

    if is_correct:
        session[session_score_key] += 1
        if session_score_key == "score":
            session["correct_count"] += 1
            if session["correct_count"] >= 3:
                session["level"] += 1
                session["correct_count"] = 0

    return render_template(
        "index.html",
        correct_sentence=sentence_data["chinese"],
        result="✅ Correct!" if is_correct else "❌ Try again.",
        correction=correction,
        distance=distance,
        score=session[session_score_key],
        level=session.get("level", 1),
        difficulty=sentence_data["difficulty"],
        show_result=True,
        audio_file=ctx.audio_path(sentence_data["id"], sentence_data["difficulty"]),
        translation=sentence_data["translation"],
        pinyin=sentence_data["pinyin"],
        session_mode=show_next,
        current=current,
        total=total,
        show_next_button=show_next,
    )

@dictation_bp.route("/")
def menu():
    return render_template("menu.html")

@dictation_bp.route("/practice/<sid>", methods=["GET", "POST"])
def practice(sid):
    if "score" not in session:
        session.update(score=0, level=1, correct_count=0)

    s = ctx.get_sentence(sid)
    s["id"] = sid
    if not ctx.audio_path(sid, s["difficulty"]):
        return "Missing audio file", 500

    if request.method == "POST":
        user_input = request.form["user_input"].strip()
        return render_dictation_result(user_input, s, session_score_key="score")

    return render_template("index.html", correct_sentence=s["chinese"], audio_file=ctx.audio_path(sid, s["difficulty"]),
                           score=session["score"], level=session["level"], difficulty=s["difficulty"], show_result=False)

@dictation_bp.route("/session", methods=["GET", "POST"])
def session_practice():
    if "session_ids" not in session:
        level = request.args.get("hsk")
        session.update(hsk_level=level, session_ids=ctx.get_random_ids(level=level), session_index=0, session_score=0)

    if request.method == "POST" and "next" in request.form:
        session["session_index"] += 1
        if session["session_index"] >= 5:
            score = session["session_score"]
            level = session.get("hsk_level")
            session.clear()
            return render_template("session_summary.html", score=score, total=5, level=level)

    sid = session["session_ids"][session["session_index"]]
    s = ctx.get_sentence(sid)
    s["id"] = sid
    if not ctx.audio_path(sid, s["difficulty"]):
        return "Missing audio file", 500

    if request.method == "POST" and "user_input" in request.form:
        user_input = request.form["user_input"].strip()
        return render_dictation_result(user_input, s, session_score_key="session_score",
                                       show_next=True, current=session["session_index"] + 1, total=5)

    return render_template("index.html", correct_sentence=s["chinese"], audio_file=ctx.audio_path(sid, s["difficulty"]),
                           score=session["session_score"], level=session.get("level", 1), difficulty=s["difficulty"],
                           show_result=False, session_mode=True, current=session["session_index"] + 1, total=5)
