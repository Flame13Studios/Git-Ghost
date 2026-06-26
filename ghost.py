import sqlite3
import os
import argparse
from datetime import datetime

def parse_time(time_str):
    """Helper to convert database timestamp strings into datetime objects."""
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

def generate_smart_commit(db_path):
    """Pulls all unique code additions from today and builds a structured Git commit message."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    query = "SELECT new_line FROM ghost_ledger WHERE timestamp LIKE ? ORDER BY id ASC"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query, (f"{today_str}%",))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print(f"📭 No ghostly changes recorded today ({today_str}) to build a commit from.")
            return

        unique_lines = []
        for row in rows:
            for line in row[0].splitlines():
                clean_line = line.strip()
                if clean_line and clean_line not in unique_lines:
                    unique_lines.append(clean_line)

        print("\n" + "="*60)
        print("🤖 GIT-GHOST AUTOMATED SMART COMMIT GENERATOR 🤖")
        print("="*60)
        print("feat(auto): synchronized background development updates\n")
        print("Glinting changes extracted automatically by Git-Ghost:")
        for line in unique_lines:
            print(f"  - {line}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"❌ Failed to generate commit: {e}")

def export_to_markdown(export_filename, rows, active_filters_desc):
    """Writes the current filtered timeline data out to a clean Markdown document."""
    try:
        with open(export_filename, "w", encoding="utf-8") as md:
            md.write(f"# 📜 Git-Ghost History Ledger Export\n\n")
            md.write(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if active_filters_desc:
                md.write(f"**Active Extraction Filters:**\n")
                for filter_line in active_filters_desc:
                    md.write(f"- {filter_line}\n")
            md.write("\n---\n\n")

            # Reset tracking variables for session clumping in markdown file
            current_session_start = None
            last_timestamp = None

            for row in rows:
                timestamp_str, file_name, new_line, clipboard = row
                current_time = parse_time(timestamp_str)

                if last_timestamp is None or (last_timestamp - current_time).total_seconds() > 600:
                    current_session_start = timestamp_str
                    md.write(f"## 🕒 Session Fragment: {current_session_start}\n\n")
                
                last_timestamp = current_time

                md.write(f"### 📁 File Modification: `{file_name}`\n")
                md.write(f"- **Recorded Event Time:** {timestamp_str}\n")
                md.write(f"- **Snapshot Ghost Context / Clipboard:** `{clipboard if clipboard else '[Empty]'}`\n\n")
                md.write("#### ➕ Delta Block Appended:\n")
                md.write("```python\n")
                md.write(f"{new_line}\n")
                md.write("```\n")
                md.write("\n" + "-"*40 + "\n\n")

        print(f"🚀 [EXPORT SUCCESS] Captured timeline cleanly written to: {os.path.abspath(export_filename)}")
    except Exception as e:
        print(f"❌ Failed to export markdown file: {e}")

def read_vault():
    db_name = "git_ghost.db"
    watch_dir = os.path.abspath(".")
    db_path = os.path.join(watch_dir, db_name)

    if not os.path.exists(db_path):
        print("❌ Error: No Git-Ghost database found in this directory.")
        return

    # 1. Argument Parser Configuration
    parser = argparse.ArgumentParser(description="📜 Git-Ghost Advanced Production Ledger Dashboard")
    parser.add_argument("--file", type=str, help="Filter logs by a specific file name.")
    parser.add_argument("--search", type=str, help="Search clipboard history for a keyword.")
    parser.add_argument("--commit", action="store_true", help="Generate a smart summary Git commit message for today.")
    parser.add_argument("--export", type=str, help="Export current filtered timeline directly to a Markdown (.md) file.")
    args = parser.parse_args()

    # Feature 2 Bypass Rule: If user wants a commit message, handle it immediately and finish.
    if args.commit:
        generate_smart_commit(db_path)
        return

    # 2. Build Core Filter Queries
    base_query = "SELECT timestamp, file_name, new_line, clipboard_content FROM ghost_ledger"
    conditions = []
    query_params = []
    active_filters_desc = []

    if args.file:
        conditions.append("file_name = ?")
        query_params.append(args.file)
        active_filters_desc.append(f"Target File: {args.file}")

    if args.search:
        conditions.append("clipboard_content LIKE ?")
        query_params.append(f"%{args.search}%")
        active_filters_desc.append(f"Clipboard Search Match: '{args.search}'")

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    # Session grouping works cleanly by reading chronologically descending order
    base_query += " ORDER BY id DESC"

    # 3. Pull Data From Database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(base_query, query_params)
        rows = cursor.fetchall()
        conn.close()

        # Feature 3 Bypass Rule: If an export argument is passed, direct output away from standard print loop
        if args.export:
            export_to_markdown(args.export, rows, active_filters_desc)
            return

        # 4. Standard Console Rendering Loop (With Feature 1: Session Clustering)
        print("\n" + "="*60)
        print("📜 GIT-GHOST HISTORY LEDGER 📜")
        if active_filters_desc:
            print("🎯 Active Filters:")
            for filter_desc in active_filters_desc:
                print(f"   {filter_desc}")
        print("="*60)

        if not rows:
            print("📭 No ghostly traces found matching those query metrics.")
            print("="*60 + "\n")
            return

        last_timestamp = None

        for row in rows:
            timestamp_str, file_name, new_line, clipboard = row
            current_time = parse_time(timestamp_str)

            # Feature 1 Check: If the difference between sequential rows is greater than 10 minutes (600s), split session
            if last_timestamp is None or (last_timestamp - current_time).total_seconds() > 600:
                print(f"\n⚡=== SESSION TIME FRAGMENT BLOCK: {timestamp_str} ===⚡\n")
            
            last_timestamp = current_time

            print(f"⏰ Time: {timestamp_str} | 📁 File: {file_name}")
            print("➕ Code Added:")
            for line in new_line.splitlines():
                print(f"   {line}")
            print(f"👻 Ghost Context: {clipboard if clipboard else '[Empty]'}")
            print("-" * 60)

        print("="*60 + "\n")

    except Exception as e:
        print(f"❌ Failed to process dashboard layer: {e}")

if __name__ == "__main__":
    read_vault()