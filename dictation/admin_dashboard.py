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

@admin_bp.route("/admin/run-color-palette")
def run_color_palette():
    """Run the color palette generator"""
    import subprocess
    import os
    
    try:
        # Run the color palette generator
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'developer_tools', 'show_color_palette_simple.py')
        subprocess.run(['python3', script_path], check=True)
        return "Color palette generated successfully! Check the generated HTML file."
    except subprocess.CalledProcessError as e:
        return f"Error generating color palette: {e}", 500

@admin_bp.route("/admin/export-corrections")
def export_corrections():
    """Export reported corrections to CSV"""
    import subprocess
    import os
    
    try:
        # Run the export script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'developer_tools', 'export_reported_corrections_to_csv.py')
        subprocess.run(['python3', script_path], check=True)
        return "Corrections exported successfully! Check the generated CSV file."
    except subprocess.CalledProcessError as e:
        return f"Error exporting corrections: {e}", 500 