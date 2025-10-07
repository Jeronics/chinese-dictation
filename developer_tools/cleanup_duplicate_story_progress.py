#!/usr/bin/env python3
"""
Cleanup script to remove duplicate story_progress entries.
Keeps only the most recent entry for each (user_id, story_id) pair.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Add parent directory to path to import from project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cleanup_duplicates():
    """Remove duplicate story progress entries, keeping only the most recent."""
    
    # Get all story progress entries
    result = supabase.table("story_progress").select("*").execute()
    entries = result.data
    
    print(f"Found {len(entries)} total story progress entries")
    
    # Group by (user_id, story_id)
    grouped = {}
    for entry in entries:
        key = (entry["user_id"], entry["story_id"])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(entry)
    
    print(f"Found {len(grouped)} unique (user_id, story_id) combinations")
    
    # For each group, keep the most recent and delete the rest
    total_deleted = 0
    for key, group_entries in grouped.items():
        if len(group_entries) > 1:
            # Sort by last_updated descending
            sorted_entries = sorted(group_entries, key=lambda x: x["last_updated"], reverse=True)
            most_recent = sorted_entries[0]
            to_delete = sorted_entries[1:]
            
            print(f"\nUser {key[0][:8]}..., Story {key[1]}: {len(group_entries)} duplicates")
            print(f"  Keeping: ID={most_recent['id']}, Index={most_recent['current_index']}, Updated={most_recent['last_updated']}")
            
            # Delete old entries
            for entry in to_delete:
                print(f"  Deleting: ID={entry['id']}, Index={entry['current_index']}, Updated={entry['last_updated']}")
                supabase.table("story_progress").delete().eq("id", entry["id"]).execute()
                total_deleted += 1
    
    print(f"\nCleanup complete! Deleted {total_deleted} duplicate entries.")
    
    # Show final count
    final_result = supabase.table("story_progress").select("*").execute()
    print(f"Remaining entries: {len(final_result.data)}")

if __name__ == "__main__":
    print("=== Story Progress Cleanup Script ===\n")
    
    # Check for --force flag
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        cleanup_duplicates()
    else:
        print("Usage: python cleanup_duplicate_story_progress.py --force")
        print("This script will delete duplicate story progress entries.")
        sys.exit(1)

