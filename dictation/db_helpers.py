import os
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
    Update the character progress for a user and hanzi, incrementing correct or fail counts.
    """
    try:
        result = supabase.table("character_progress").select("*") \
            .eq("user_id", user_id).eq("hanzi", hanzi).execute()
        if result.data:
            progress = result.data[0]
            correct_count = progress["correct_count"] + (1 if correct else 0)
            fail_count = progress["fail_count"] + (0 if correct else 1)
            if correct_count >= 3:
                status = "known"
            elif fail_count >= 2:
                status = "failed"
            else:
                status = "learning"
            supabase.table("character_progress").update({
                "correct_count": correct_count,
                "fail_count": fail_count,
                "status": status,
                "last_seen": "now()"
            }).eq("user_id", user_id).eq("hanzi", hanzi).execute()
        else:
            supabase.table("character_progress").insert({
                "user_id": user_id,
                "hanzi": hanzi,
                "hsk_level": hsk_level,
                "correct_count": 1 if correct else 0,
                "fail_count": 0 if correct else 1,
                "status": "known" if correct else "failed",
                "last_seen": "now()"
            }).execute()
    except Exception as e:
        print(f"Error updating character progress for user {user_id}, hanzi {hanzi}: {e}")

def get_user_character_status(user_id: str) -> Dict[str, str]:
    """
    Returns a dict: {hanzi: status} for the given user.
    """
    result = supabase.table("character_progress").select("hanzi, status").eq("user_id", user_id).execute()
    return {row["hanzi"]: row["status"] for row in result.data} if result.data else {}

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
        print(f"Error updating daily work registry for user {user_id}: {e}")

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
        print(f"Error getting daily work stats for user {user_id}: {e}")
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
        print(f"Error getting daily session count for user {user_id}: {e}")
        return 0 