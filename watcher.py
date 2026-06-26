import os
import time
import sqlite3
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
import difflib

class GitGhostSystem(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.db_name = "git_ghost.db"
        self.watch_dir = os.path.abspath(".")
        self.file_snapshots = {}
        
        self.setup_vault()
        self.take_initial_snapshots(self.watch_dir)

    def setup_vault(self):
        db_path = os.path.join(self.watch_dir, self.db_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ghost_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                file_name TEXT,
                new_line TEXT,
                clipboard_content TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def read_file_lines(self, target_path):
        if not os.path.exists(target_path):
            return []
        try:
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        except Exception:
            return []

    def take_initial_snapshots(self, directory):
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file in [self.db_name, "watcher.py", "ghost.py", "start_ghost.bat"] or file.endswith('.tmp') or file.startswith('~'):
                    continue
                full_path = os.path.abspath(os.path.join(root, file))
                self.file_snapshots[full_path] = self.read_file_lines(full_path)

    def get_clipboard_content(self):
        try:
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text.strip() if isinstance(text, str) else ""
        except Exception:
            return ""

    def save_to_vault(self, file_name, new_lines_block, clipboard):
        try:
            db_path = os.path.join(self.watch_dir, self.db_name)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO ghost_ledger (timestamp, file_name, new_line, clipboard_content)
                VALUES (?, ?, ?, ?)
            ''', (current_time, file_name, new_lines_block, clipboard))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f" [SYSTEM ERROR] Database Write Fault: {e}")

    def on_any_event(self, event):
        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path)
        
        if file_name in [self.db_name, "watcher.py", "ghost.py", "start_ghost.bat"] or file_name.endswith('.tmp') or file_name.startswith('~'):
            return

        if event.event_type in ['modified', 'created']:
            time.sleep(0.3)
            target_path = os.path.abspath(event.src_path)
            
            current_lines = self.read_file_lines(target_path)
            old_lines = self.file_snapshots.get(target_path, [])
            
            added_lines = []
            diff = difflib.ndiff(old_lines, current_lines)
            
            for line in diff:
                if line.startswith('+ '):
                    added_lines.append(line[2:])
            
            self.file_snapshots[target_path] = current_lines

            if added_lines:
                unified_block = "".join(added_lines).strip()
                
                if unified_block:
                    ghost_context = self.get_clipboard_content()
                    self.save_to_vault(file_name, unified_block, ghost_context)
                    
                    # Clean, professional runtime reporting frames
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🗲 EVENT RETRIEVED: {file_name}")
                    print(f" └── 📝 Isolated Diff Delta ({len(unified_block.splitlines())} lines captured)")
                    print(f" └── 💾 SQLite Database Secure Ledger Update Complete.")
                    print("─" * 80)

if __name__ == "__main__":
    event_handler = GitGhostSystem()
    observer = Observer()
    observer.schedule(event_handler, path=event_handler.watch_dir, recursive=True)
    
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│                     GIT-GHOST : PASSIVE MONITOR ENGINE                       │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    print(f" STATUS: ACTIVE  | TRACE-TARGET: {event_handler.watch_dir}")
    print(f" LOCAL TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SUBSYSTEM: WIN32_WATCHDOG_V1")
    print("─" * 80)
    print(" Waiting for local filesystem stream events...")
    print("─" * 80)
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n [SYSTEM NOTICE] Shutting down Observer Pipeline gracefully...")
        observer.stop()
    observer.join()