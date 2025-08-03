import os
import sqlite3
import uuid

def setup_database(db_path):
    """Initialize SQLite database tables with triggers and state constraints."""
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
                    'delete_tag',
                    'create_header',
                    'set_header_path',
                    'set_header_label',
                    'delete_header'
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
            parent_tag_id TEXT,
            jd_id INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
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

        CREATE TABLE IF NOT EXISTS event_create_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_header_path (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            jd_area INTEGER NOT NULL,
            jd_id INTEGER,
            jd_ext INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_header_label (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS state_headers (
            header_id TEXT PRIMARY KEY,
            jd_area INTEGER NOT NULL,
            jd_id INTEGER,
            jd_ext INTEGER,
            label TEXT NOT NULL,
            UNIQUE(jd_area, jd_id, jd_ext)
        );

        -- Trigger to prevent jd_ext without jd_id for headers
        CREATE TRIGGER IF NOT EXISTS check_header_jd_ext
        BEFORE INSERT ON event_set_header_path
        WHEN NEW.jd_ext IS NOT NULL AND NEW.jd_id IS NULL
        BEGIN
            SELECT RAISE(ABORT, 'jd_ext requires jd_id');
        END;

        CREATE TABLE IF NOT EXISTS state_tag_icons (
            tag_id TEXT PRIMARY KEY,
            icon BLOB
        );

        CREATE TABLE IF NOT EXISTS state_tags (
            tag_id TEXT PRIMARY KEY,
            parent_tag_id TEXT,
            jd_id INTEGER,
            label TEXT NOT NULL,
            FOREIGN KEY(parent_tag_id) REFERENCES state_tags(tag_id) ON DELETE CASCADE
        );
    """)
    rebuild_state_tags(conn)
    rebuild_state_headers(conn)
    conn.commit()
    return conn

def rebuild_state_tags(conn):
    """Rebuild the state_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_tags;

        INSERT INTO state_tags (tag_id, parent_tag_id, jd_id, label)
        SELECT
            p.tag_id,
            p.parent_tag_id,
            p.jd_id,
            l.new_label
        FROM (
            SELECT
                p.tag_id,
                p.parent_tag_id,
                p.jd_id,
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

def rebuild_state_headers(conn):
    """Rebuild the state_headers table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_headers;

        INSERT INTO state_headers (header_id, jd_area, jd_id, jd_ext, label)
        SELECT
            p.header_id,
            p.jd_area,
            p.jd_id,
            p.jd_ext,
            l.new_label
        FROM (
            SELECT
                p.header_id,
                p.jd_area,
                p.jd_id,
                p.jd_ext,
                p.event_id
            FROM event_set_header_path p
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_header_path
                GROUP BY header_id
            ) latest_path ON p.header_id = latest_path.header_id AND p.event_id = latest_path.max_event
        ) p
        JOIN (
            SELECT
                l.header_id,
                l.new_label,
                l.event_id
            FROM event_set_header_label l
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_header_label
                GROUP BY header_id
            ) latest_label ON l.header_id = latest_label.header_id AND l.event_id = latest_label.max_event
        ) l ON p.header_id = l.header_id
        WHERE p.header_id NOT IN (SELECT header_id FROM event_delete_header);
    """)
    conn.commit()

def create_tag(conn, parent_tag_id, jd_id, label):
    """Create a new tag and return its tag_id, or None if constraints are violated."""
    cursor = conn.cursor()
    # Enforce unique jd_id within the same parent scope
    cursor.execute(
        "SELECT tag_id FROM state_tags WHERE parent_tag_id IS ? AND jd_id IS ?",
        (parent_tag_id, jd_id),
    )
    if cursor.fetchone():
        return None
    tag_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_path')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_tag_path (event_id, tag_id, parent_tag_id, jd_id) VALUES (?, ?, ?, ?)",
        (event_id, tag_id, parent_tag_id, jd_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
        (event_id, tag_id, label),
    )
    conn.commit()
    return tag_id

def create_header(conn, jd_area, jd_id, jd_ext, label):
    """Create a new header and return its header_id, or None if constraints are violated."""
    cursor = conn.cursor()
    # Enforce jd_area not null
    if jd_area is None:
        return None
    # Check unique (jd_area, jd_id, jd_ext)
    cursor.execute(
        "SELECT header_id FROM state_headers WHERE jd_area = ? AND jd_id IS ? AND jd_ext IS ?",
        (jd_area, jd_id, jd_ext),
    )
    if cursor.fetchone():
        return None
    if jd_ext is not None and jd_id is None:
        return None
    header_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_header')")
    event_id = cursor.lastrowid
    cursor.execute("INSERT INTO event_create_header (event_id, header_id) VALUES (?, ?)", (event_id, header_id))
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_header_path')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_path (event_id, header_id, jd_area, jd_id, jd_ext) VALUES (?, ?, ?, ?, ?)",
        (event_id, header_id, jd_area, jd_id, jd_ext),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return header_id

def update_header(conn, header_id, jd_area, jd_id, jd_ext, label):
    """Update an existing header. Returns True on success."""
    cursor = conn.cursor()
    if jd_area is None or (jd_ext is not None and jd_id is None):
        return False
    cursor.execute(
        "SELECT header_id FROM state_headers WHERE jd_area = ? AND jd_id IS ? AND jd_ext IS ? AND header_id != ?",
        (jd_area, jd_id, jd_ext, header_id),
    )
    if cursor.fetchone():
        return False
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_header_path')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_path (event_id, header_id, jd_area, jd_id, jd_ext) VALUES (?, ?, ?, ?, ?)",
        (event_id, header_id, jd_area, jd_id, jd_ext),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return True

def delete_header(conn, header_id):
    """Delete an existing header."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    conn.commit()
