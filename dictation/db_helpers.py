import os
import logging
from datetime import date, timedelta
from supabase import create_client
from typing import Optional, Dict, Any, List

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_character_progress(user_id: str, hanzi: str, hsk_level: int, correct: bool) -> None:
    """
    Update the character progress for a user and hanzi, adjusting the grade field.
    """
    try:
        result = supabase.table("character_progress").select("*") \
            .eq("user_id", user_id).eq("hanzi", hanzi).execute()
        if result.data:
            progress = result.data[0]
            prev_grade = progress.get("grade", -1)
            if correct:
                new_grade = min(prev_grade + 1, 3)
            else:
                new_grade = max(prev_grade - 1, -1)
            supabase.table("character_progress").update({
                "grade": new_grade,
                "last_seen": "now()"
            }).eq("user_id", user_id).eq("hanzi", hanzi).execute()
        else:
            supabase.table("character_progress").insert({
                "user_id": user_id,
                "hanzi": hanzi,
                "hsk_level": hsk_level,
                "grade": 0 if correct else -1,
                "last_seen": "now()"
            }).execute()
    except Exception as e:
        logging.error(f"Error updating character progress for user {user_id}, hanzi {hanzi}: {e}")



def update_daily_work_registry(
    user_id: str,
    session_type: str,
    average_accuracy: float,
    total_sentences: int,
    story_id: Optional[str] = None,
    story_parts_completed: int = 0
) -> None:
    """
    Update daily work registry for a user with session average accuracy.
    """
    try:
        today = date.today().isoformat()
        sentences_above_7 = 1 if average_accuracy >= 7 else 0
        result = supabase.table("daily_work_registry").select("*") \
            .eq("user_id", user_id) \
            .eq("session_date", today) \
            .eq("session_type", session_type) \
            .eq("story_id", story_id or "NULL") \
            .execute()
        if result.data:
            existing = result.data[0]
            new_sentences_above_7 = existing["sentences_above_7"] + sentences_above_7
            new_total_sentences = existing["total_sentences"] + total_sentences
            new_story_parts_completed = existing["story_parts_completed"] + story_parts_completed
            supabase.table("daily_work_registry").update({
                "sentences_above_7": new_sentences_above_7,
                "total_sentences": new_total_sentences,
                "story_parts_completed": new_story_parts_completed
            }).eq("id", existing["id"]).execute()
        else:
            supabase.table("daily_work_registry").insert({
                "user_id": user_id,
                "session_date": today,
                "session_type": session_type,
                "sentences_above_7": sentences_above_7,
                "total_sentences": total_sentences,
                "story_id": story_id,
                "story_parts_completed": story_parts_completed
            }).execute()
    except Exception as e:
        logging.error(f"Error updating daily work registry for user {user_id}: {e}")

def get_daily_work_stats(user_id: str) -> Dict[str, Any]:
    """
    Get daily work statistics for dashboard.
    """
    try:
        today = date.today()
        today_result = supabase.table("daily_work_registry").select("*") \
            .eq("user_id", user_id) \
            .eq("session_date", today.isoformat()) \
            .execute()
        today_sentences_above_7 = 0
        today_total_sentences = 0
        for record in today_result.data:
            today_sentences_above_7 += record["sentences_above_7"]
            today_total_sentences += record["total_sentences"]
        current_streak = 0
        check_date = today
        while True:
            date_str = check_date.isoformat()
            result = supabase.table("daily_work_registry").select("*") \
                .eq("user_id", user_id) \
                .eq("session_date", date_str) \
                .execute()
            if not result.data:
                break
            has_above_7 = any(record["sentences_above_7"] > 0 for record in result.data)
            if has_above_7:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        last_7_days: List[Dict[str, Any]] = []
        for i in range(6, -1, -1):
            check_date = today - timedelta(days=i)
            date_str = check_date.isoformat()
            result = supabase.table("daily_work_registry").select("*") \
                .eq("user_id", user_id) \
                .eq("session_date", date_str) \
                .execute()
            day_sentences_above_7 = sum(record["sentences_above_7"] for record in result.data)
            day_total_sentences = sum(record["total_sentences"] for record in result.data)
            last_7_days.append({
                "date": check_date.strftime("%a"),
                "sentences_above_7": day_sentences_above_7,
                "total_sentences": day_total_sentences,
                "completed": day_sentences_above_7 > 0
            })
        return {
            "today_sentences_above_7": today_sentences_above_7,
            "today_total_sentences": today_total_sentences,
            "current_streak": current_streak,
            "last_7_days": last_7_days
        }
    except Exception as e:
        logging.error(f"Error getting daily work stats for user {user_id}: {e}")
        return {
            "today_sentences_above_7": 0,
            "today_total_sentences": 0,
            "current_streak": 0,
            "last_7_days": []
        }

def get_daily_session_count(user_id: str) -> int:
    """
    Returns the number of daily sessions completed today for the user.
    A session is a row in daily_work_registry for today and user_id, regardless of session_type.
    """
    try:
        today = date.today().isoformat()
        result = supabase.table("daily_work_registry").select("id").eq("user_id", user_id).eq("session_date", today).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        logging.error(f"Error getting daily session count for user {user_id}: {e}")
        return 0

def batch_update_character_progress(user_id: str, hanzi_updates: list) -> None:
    """
    Batch update character progress for a user. hanzi_updates is a list of dicts:
    {"hanzi": ..., "hsk_level": ..., "correct": ...}
    """
    try:
        hanzi_list = [u["hanzi"] for u in hanzi_updates]
        # Fetch current progress for all hanzi in one query
        result = supabase.table("character_progress").select("hanzi, grade").eq("user_id", user_id).in_("hanzi", hanzi_list).execute()
        current = {row["hanzi"]: row for row in (result.data or [])}
        upserts = []
        for update in hanzi_updates:
            hanzi = update["hanzi"]
            hsk_level = update["hsk_level"]
            correct = update["correct"]
            prev = current.get(hanzi)
            if prev:
                prev_grade = prev.get("grade", -1)
                if correct:
                    new_grade = min(prev_grade + 1, 3)
                else:
                    new_grade = max(prev_grade - 1, 0)
            else:
                new_grade = 0 if correct else -1
            upserts.append({
                "user_id": user_id,
                "hanzi": hanzi,
                "hsk_level": hsk_level,
                "grade": new_grade,
                "last_seen": "now()"
            })
        if upserts:
            supabase.table("character_progress").upsert(upserts, on_conflict="user_id,hanzi").execute()
    except Exception as e:
        logging.error(f"Error batch updating character progress for user {user_id}: {e}")


def get_user_progress_summary(user_id: str, ctx) -> List[Dict[str, Any]]:
    """
    Get user progress summary for dashboard showing HSK level progress.
    Returns list of level dictionaries with progress counts.
    """
    try:
        # Get all user progress for all hanzi
        progress_rows = supabase.table("character_progress") \
            .select("hanzi, hsk_level, grade") \
            .eq("user_id", user_id).execute().data or []
        
        # Map hanzi to grade for quick lookup
        hanzi_to_grade = {row["hanzi"]: row["grade"] for row in progress_rows}
        
        # For each HSK level, count known, learning, failed, unseen
        levels = []
        for hsk_level, total in ctx.hsk_totals.items():
            # Get all hanzi for this level
            hanzi_list = [item["hanzi"] for item in ctx.hsk_data if item["hsk_level"] == hsk_level]
            known = learning = failed = unseen = 0
            
            for hanzi in hanzi_list:
                grade = hanzi_to_grade.get(hanzi, None)
                if grade is None:
                    unseen += 1
                elif grade == -1:
                    failed += 1
                elif grade in [0, 1]:
                    learning += 1
                elif grade in [2, 3]:
                    known += 1
            
            known_pct = int(100 * known / total) if total else 0
            levels.append({
                "level": hsk_level,
                "known": known,
                "failed": failed,
                "learning": learning,
                "unseen": unseen,
                "total": total,
                "percent": known_pct
            })
        
        return levels
    except Exception as e:
        logging.error("Error loading progress from Supabase:", e)
        return [] 