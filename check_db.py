import sqlite3
import os

def check_db(db_name):
    if not os.path.exists(db_name):
        print(f"Error: {db_name} does not exist.")
        return
    conn = sqlite3.connect(db_name)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(f"Tables in {db_name}: {[t[0] for t in tables]}")
    conn.close()

if __name__ == "__main__":
    check_db("plexus_archive.sqlite")
    check_db("plexus_checkpoints.sqlite")
