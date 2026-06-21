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
            number TEXT,
            name TEXT,
            callsign TEXT,
            program TEXT
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS recordings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            channel TEXT,
            start TEXT,
            stop TEXT,
            title TEXT
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS programs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            start TEXT,
            stop TEXT,
            title TEXT,
            subtitle TEXT,
            description TEXT
        )
        """)

        db.commit()

def list_recordings():
    with connect() as db:
        return db.execute("""
            SELECT *
            FROM recordings
            ORDER BY start_time DESC
        """).fetchall()



def add_recording(filename, channel, title,
                  start_time, end_time="",
                  size_bytes=0, status="Finished"):

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
        """,
        (
            filename,
            channel,
            title,
            start_time,
            end_time,
            size_bytes,
            status
        ))
        db.commit()

def add_recording(filename, channel, start, stop="", title=""):
    with connect() as db:
        db.execute("""
            INSERT INTO recordings
            (filename, channel, start, stop, title)
            VALUES (?,?,?,?,?)
        """, (filename, channel, start, stop, title))
        db.commit()


def delete_recording(record_id):
    with connect() as db:
        db.execute(
            "DELETE FROM recordings WHERE id=?",
            (record_id,)
        )
        db.commit()

def delete_recording(filename):
    with connect() as db:
        db.execute(
            "DELETE FROM recordings WHERE filename=?",
            (filename,)
        )
        db.commit()


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
        """,
        (
            number,
            name,
            url
        ))
        db.commit()