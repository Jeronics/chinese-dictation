import os
import csv
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all reported corrections
data = supabase.table("reported_corrections").select("*").execute().data

if not data:
    print("No data found.")
    exit(0)

# Get all fieldnames from the first row
fieldnames = list(data[0].keys())

with open("reported_corrections.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        writer.writerow(row)

print(f"Exported {len(data)} rows to reported_corrections.csv") 