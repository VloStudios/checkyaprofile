import requests
import sqlite3
from datetime import datetime

DB = "gh_tracker.db"


# db
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
        repo_id INTEGER,
        name TEXT,
        stars INTEGER,
        forks INTEGER,
        language TEXT,
        updated_at TEXT,
        snapshot_time TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_snapshot(repos):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    ts = datetime.utcnow().isoformat()

    for r in repos:
        c.execute("""
        INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"],
            r["name"],
            r["stargazers_count"],
            r["forks_count"],
            r["language"],
            r["updated_at"],
            ts
        ))

    conn.commit()
    conn.close()


def load_last_snapshot():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT repo_id, name, stars, forks
    FROM snapshots
    WHERE snapshot_time = (SELECT MAX(snapshot_time) FROM snapshots)
    """)

    rows = c.fetchall()
    conn.close()

    return {r[0]: r for r in rows}


# api
def fetch_repos(user):
    r = requests.get(f"https://api.github.com/users/{user}/repos")
    return r.json() if r.status_code == 200 else []


# diff
def diff(new, old):
    new_ids = set()

    print("\nchanges")

    for r in new:
        rid = r["id"]
        new_ids.add(rid)

        if rid not in old:
            print(f"+ {r['name']}")
            continue

        o = old[rid]

        if r["stargazers_count"] != o[2]:
            print(f"* {r['name']} stars {o[2]} -> {r['stargazers_count']}")

        if r["forks_count"] != o[3]:
            print(f"* {r['name']} forks {o[3]} -> {r['forks_count']}")

    removed = set(old.keys()) - new_ids

    for rid in removed:
        print(f"- {old[rid][1]}")


# view
def list_repos(repos):
    for r in repos:
        print(f"{r['name']} | {r['stargazers_count']} stars | {r['forks_count']} forks")


# cli
def menu():
    print("\n1 fetch")
    print("2 diff")
    print("3 list")
    print("4 exit")


def main():
    init_db()

    user = input("user: ").strip()
    cache = []

    while True:
        menu()
        c = input("> ").strip()

        if c == "1":
            cache = fetch_repos(user)
            save_snapshot(cache)
            print("saved")

        elif c == "2":
            if not cache:
                cache = fetch_repos(user)

            old = load_last_snapshot()
            if old:
                diff(cache, old)
            else:
                print("no snapshot")

        elif c == "3":
            if not cache:
                cache = fetch_repos(user)
            list_repos(cache)

        elif c == "4":
            break


if __name__ == "__main__":
    main()
