import os
import sqlite3
import uuid

def setup_database(db_path):
    """Initialize SQLite database tables with unique constraint and triggers."""
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL CHECK (
                event_type IN (
                    'create_tag',
                    'set_tag_path',
                    'set_tag_label',
                    'set_tag_icon',
                    'delete_tag'
                )
            ),
            timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS event_create_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_tag_path (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            jd_area INTEGER,
            jd_id INTEGER,
            jd_ext INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
            UNIQUE(jd_area, jd_id, jd_ext)
        );

        CREATE TABLE IF NOT EXISTS event_set_tag_label (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_tag_icon (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            icon BLOB,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS state_tag_icons (
            tag_id TEXT PRIMARY KEY,
            icon BLOB
        );

        CREATE TABLE IF NOT EXISTS state_tags (
            tag_id TEXT PRIMARY KEY,
            jd_area INTEGER,
            jd_id INTEGER,
            jd_ext INTEGER,
            label TEXT NOT NULL,
            UNIQUE(jd_area, jd_id, jd_ext)
        );

        -- Trigger to prevent jd_id without jd_area
        CREATE TRIGGER IF NOT EXISTS check_jd_id
        BEFORE INSERT ON event_set_tag_path
        WHEN NEW.jd_id IS NOT NULL AND NEW.jd_area IS NULL
        BEGIN
            SELECT RAISE(ABORT, 'jd_id requires jd_area');
        END;

        -- Trigger to prevent jd_ext without jd_id
        CREATE TRIGGER IF NOT EXISTS check_jd_ext
        BEFORE INSERT ON event_set_tag_path
        WHEN NEW.jd_ext IS NOT NULL AND NEW.jd_id IS NULL
        BEGIN
            SELECT RAISE(ABORT, 'jd_ext requires jd_id');
        END;
    """)
    rebuild_state_tags(conn)
    conn.commit()
    return conn

def rebuild_state_tags(conn):
    """Rebuild the state_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_tags;

        INSERT INTO state_tags (tag_id, jd_area, jd_id, jd_ext, label)
        SELECT
            p.tag_id,
            p.jd_area,
            p.jd_id,
            p.jd_ext,
            l.new_label
        FROM (
            SELECT
                p.tag_id,
                p.jd_area,
                p.jd_id,
                p.jd_ext,
                p.event_id
            FROM event_set_tag_path p
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_tag_path
                GROUP BY tag_id
            ) latest_path ON p.tag_id = latest_path.tag_id AND p.event_id = latest_path.max_event
        ) p
        JOIN (
            SELECT
                l.tag_id,
                l.new_label,
                l.event_id
            FROM event_set_tag_label l
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_tag_label
                GROUP BY tag_id
            ) latest_label ON l.tag_id = latest_label.tag_id AND l.event_id = latest_label.max_event
        ) l ON p.tag_id = l.tag_id
        WHERE p.tag_id NOT IN (SELECT tag_id FROM event_delete_tag);
    """)
    cursor.executescript("""
        DELETE FROM state_tag_icons;

        INSERT INTO state_tag_icons (tag_id, icon)
        SELECT
            i.tag_id,
            i.icon
        FROM event_set_tag_icon i
        JOIN (
            SELECT tag_id, MAX(event_id) AS max_event
            FROM event_set_tag_icon
            GROUP BY tag_id
        ) latest ON i.tag_id = latest.tag_id AND i.event_id = latest.max_event
        WHERE i.tag_id NOT IN (SELECT tag_id FROM event_delete_tag);
    """)
    conn.commit()

def create_tag(conn, jd_area, jd_id, jd_ext, label):
    """Create a new tag and return its tag_id, or None if constraints are violated."""
    cursor = conn.cursor()
    # Check for unique (jd_area, jd_id, jd_ext) constraint
    cursor.execute("SELECT tag_id FROM state_tags WHERE jd_area IS ? AND jd_id IS ? AND jd_ext IS ?", (jd_area, jd_id, jd_ext))
    if cursor.fetchone():
        return None  # Conflict exists
    # Validate constraints: no jd_id without jd_area, no jd_ext without jd_id
    if jd_id is not None and jd_area is None:
        return None
    if jd_ext is not None and jd_id is None:
        return None
    tag_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_tag')")
    event_id = cursor.lastrowid
    cursor.execute("INSERT INTO event_create_tag (event_id, tag_id) VALUES (?, ?)", (event_id, tag_id))
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_path')")
    event_id = cursor.lastrowid
    cursor.execute("INSERT INTO event_set_tag_path (event_id, tag_id, jd_area, jd_id, jd_ext) VALUES (?, ?, ?, ?, ?)", (event_id, tag_id, jd_area, jd_id, jd_ext))
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute("INSERT INTO event_set_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)", (event_id, tag_id, label))
    conn.commit()
    return tag_id