import os
from flask import Blueprint, render_template
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

admin_bp = Blueprint("admin_dashboard", __name__)

@admin_bp.route("/admin/reported-corrections")
def reported_corrections_dashboard():
    rows = supabase.table("reported_corrections").select("*").order("created_at", desc=True).execute().data
    return render_template("reported_corrections_dashboard.html", reports=rows) 