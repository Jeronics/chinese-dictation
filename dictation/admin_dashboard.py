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

@admin_bp.route("/admin")
def admin_dashboard():
    """Main admin dashboard page"""
    return render_template("admin_dashboard.html")

@admin_bp.route("/admin/reported-corrections")
def reported_corrections_dashboard():
    """View reported corrections and automatically export if there are new ones"""
    import os
    import csv
    from datetime import datetime
    
    # Get all reported corrections
    rows = supabase.table("reported_corrections").select("*").order("created_at", desc=True).execute().data
    
    if not rows:
        return render_template("reported_corrections_dashboard.html", reports=rows, export_status="No corrections to export")
    
    # Check if CSV file exists and get its last modification time
    csv_file_path = "reported_corrections.csv"
    csv_exists = os.path.exists(csv_file_path)
    
    if csv_exists:
        # Get the latest correction timestamp from database
        latest_correction_time = max(row.get('created_at', '') for row in rows if row.get('created_at'))
        
        # Get CSV file modification time
        csv_mod_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))
        
        # Parse the latest correction time
        try:
            latest_correction_datetime = datetime.fromisoformat(latest_correction_time.replace('Z', '+00:00'))
            # If CSV is newer than latest correction, no need to export
            if csv_mod_time > latest_correction_datetime:
                return render_template("reported_corrections_dashboard.html", reports=rows, export_status="CSV is up to date")
        except (ValueError, TypeError):
            pass  # If parsing fails, proceed with export
    
    # Export to CSV (either file doesn't exist or there are new corrections)
    try:
        # Get all fieldnames from the first row
        fieldnames = list(rows[0].keys())
        
        with open(csv_file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        
        export_status = f"✅ Exported {len(rows)} corrections to CSV (updated)"
    except Exception as e:
        export_status = f"❌ Export failed: {str(e)}"
    
    return render_template("reported_corrections_dashboard.html", reports=rows, export_status=export_status)

@admin_bp.route("/admin/run-color-palette")
def run_color_palette():
    """Run the color palette generator and serve the result"""
    import subprocess
    import os
    from flask import send_file
    
    try:
        # Run the color palette generator
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'developer_tools', 'show_color_palette_simple.py')
        subprocess.run(['python3', script_path], check=True)
        
        # Serve the generated HTML file
        html_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'developer_tools', 'simple_color_palette.html')
        if os.path.exists(html_file_path):
            return send_file(html_file_path, mimetype='text/html')
        else:
            return "Color palette generated but file not found.", 404
    except subprocess.CalledProcessError as e:
        return f"Error generating color palette: {e}", 500

@admin_bp.route("/admin/color-palette")
def view_color_palette():
    """View the generated color palette"""
    import os
    from flask import send_file
    
    html_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'developer_tools', 'simple_color_palette.html')
    if os.path.exists(html_file_path):
        return send_file(html_file_path, mimetype='text/html')
    else:
        return "Color palette not found. Please generate it first using the 'Generate Color Palette' button.", 404

 