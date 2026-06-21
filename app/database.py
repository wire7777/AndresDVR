import sqlite3

DB = "/home/wire/andresdvr/database/andresdvr.db"


def connect():
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def init_db():
    with connect() as db:

        db.execute("""
        CREATE TABLE IF NOT EXISTS channels(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guide_number TEXT UNIQUE,
            guide_name TEXT,
            url TEXT,
            favorite INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS recordings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            channel TEXT,
            title TEXT,
            start_time TEXT,
            end_time TEXT,
            size_bytes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Recorded'
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS programs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            title TEXT,
            subtitle TEXT,
            description TEXT,
            start TEXT,
            stop TEXT,
            category TEXT,
            episode TEXT,
            rating TEXT,
            is_new INTEGER DEFAULT 0
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_recordings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            title TEXT,
            subtitle TEXT,
            start TEXT,
            stop TEXT,
            status TEXT DEFAULT 'Scheduled',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        db.commit()


# --------------------------------------------------
# RECORDINGS
# --------------------------------------------------

def list_recordings():
    with connect() as db:
        return db.execute("""
            SELECT *
            FROM recordings
            ORDER BY start_time DESC
        """).fetchall()


def add_recording(
    filename,
    channel,
    title,
    start_time,
    end_time="",
    size_bytes=0,
    status="Recording"
):
    with connect() as db:
        db.execute("""
            INSERT INTO recordings
            (
                filename,
                channel,
                title,
                start_time,
                end_time,
                size_bytes,
                status
            )
            VALUES (?,?,?,?,?,?,?)
        """, (
            filename,
            channel,
            title,
            start_time,
            end_time,
            size_bytes,
            status
        ))
        db.commit()


def finish_recording(filename, end_time, size_bytes):
    with connect() as db:
        db.execute("""
            UPDATE recordings
            SET end_time=?,
                size_bytes=?,
                status='Recorded'
            WHERE filename=?
        """, (
            end_time,
            size_bytes,
            filename
        ))
        db.commit()


def delete_recording(filename):
    with connect() as db:
        db.execute(
            "DELETE FROM recordings WHERE filename=?",
            (filename,)
        )
        db.commit()


# --------------------------------------------------
# CHANNELS
# --------------------------------------------------

def list_channels():
    with connect() as db:
        return db.execute("""
            SELECT *
            FROM channels
            ORDER BY guide_number
        """).fetchall()


def add_channel(number, name, url=""):
    with connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO channels
            (
                guide_number,
                guide_name,
                url
            )
            VALUES (?,?,?)
        """, (
            number,
            name,
            url
        ))
        db.commit()


def get_channel(guide_number):
    with connect() as db:
        return db.execute("""
            SELECT *
            FROM channels
            WHERE guide_number=?
        """, (guide_number,)).fetchone()


# --------------------------------------------------
# GUIDE
# --------------------------------------------------

def get_programs():
    with connect() as db:
        rows = db.execute("""
            SELECT *
            FROM programs
            ORDER BY start
        """).fetchall()

        return [dict(r) for r in rows]


def get_programs_for_channel(channel, limit=30):
    with connect() as db:
        rows = db.execute("""
            SELECT *
            FROM programs
            WHERE channel=?
            ORDER BY start
            LIMIT ?
        """, (
            channel,
            limit
        )).fetchall()

        return [dict(r) for r in rows]


def get_now_next():
    with connect() as db:

        channels = db.execute("""
            SELECT guide_number,
                   guide_name
            FROM channels
            WHERE enabled=1
            ORDER BY guide_number
        """).fetchall()

        result = []

        for ch in channels:

            programs = db.execute("""
                SELECT title
                FROM programs
                WHERE channel=?
                ORDER BY start
                LIMIT 2
            """, (
                ch["guide_number"],
            )).fetchall()

            now_title = None
            next_title = None

            if len(programs) > 0:
                now_title = programs[0]["title"]

            if len(programs) > 1:
                next_title = programs[1]["title"]

            result.append({
                "guide_number": ch["guide_number"],
                "guide_name": ch["guide_name"],
                "now_title": now_title,
                "next_title": next_title
            })

        return result


# --------------------------------------------------
# SCHEDULER
# --------------------------------------------------

def add_scheduled_recording(channel, title, subtitle, start, stop):
    with connect() as db:
        db.execute("""
            INSERT INTO scheduled_recordings
            (
                channel,
                title,
                subtitle,
                start,
                stop,
                status
            )
            VALUES (?,?,?,?,?,'Scheduled')
        """, (
            channel,
            title,
            subtitle,
            start,
            stop
        ))
        db.commit()


def list_scheduled_recordings():
    with connect() as db:
        rows = db.execute("""
            SELECT *
            FROM scheduled_recordings
            ORDER BY start
        """).fetchall()

        return [dict(r) for r in rows]