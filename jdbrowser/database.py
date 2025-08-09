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
                    'delete_header',
                    'create_jd_area_tag',
                    'set_jd_area_tag_order',
                    'set_jd_area_tag_label',
                    'set_jd_area_tag_icon',
                    'delete_jd_area_tag',
                    'create_jd_area_header',
                    'set_jd_area_header_order',
                    'set_jd_area_header_label',
                    'delete_jd_area_header',
                    'create_jd_id_tag',
                    'set_jd_id_tag_order',
                    'set_jd_id_tag_label',
                    'set_jd_id_tag_icon',
                    'delete_jd_id_tag',
                    'create_jd_id_header',
                    'set_jd_id_header_order',
                    'set_jd_id_header_label',
                    'delete_jd_id_header',
                    'create_jd_ext_tag',
                    'set_jd_ext_tag_order',
                    'set_jd_ext_tag_label',
                    'set_jd_ext_tag_icon',
                    'delete_jd_ext_tag',
                    'create_jd_ext_header',
                    'set_jd_ext_header_order',
                    'set_jd_ext_header_label',
                    'delete_jd_ext_header'
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
            parent_uuid TEXT,
            jd_area INTEGER,
            jd_id INTEGER,
            jd_ext INTEGER,
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
            parent_uuid TEXT,
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

        CREATE TABLE IF NOT EXISTS event_create_jd_area_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_area_tag_order (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_area_tag_label (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_area_tag_icon (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            icon BLOB,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_area_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_create_jd_area_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_area_header_order (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_area_header_label (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_area_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_create_jd_id_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_id_tag_order (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_id_tag_label (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_id_tag_icon (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            icon BLOB,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_id_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_create_jd_id_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_id_header_order (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_id_header_label (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_id_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_create_jd_ext_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_ext_tag_order (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_ext_tag_label (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_ext_tag_icon (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            icon BLOB,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_ext_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_create_jd_ext_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_ext_header_order (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_ext_header_label (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_ext_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS state_headers (
            header_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            jd_area INTEGER NOT NULL,
            jd_id INTEGER,
            jd_ext INTEGER,
            label TEXT NOT NULL,
            UNIQUE(jd_area, jd_id, jd_ext)
        );

        CREATE TABLE IF NOT EXISTS state_jd_area_headers (
            header_id TEXT PRIMARY KEY,
            [order] INTEGER NOT NULL UNIQUE,
            label TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS state_jd_id_headers (
            header_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(parent_uuid, [order])
        );

        CREATE TABLE IF NOT EXISTS state_jd_ext_headers (
            header_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(parent_uuid, [order])
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

        CREATE TABLE IF NOT EXISTS state_jd_area_tag_icons (
            tag_id TEXT PRIMARY KEY,
            icon BLOB
        );

        CREATE TABLE IF NOT EXISTS state_jd_id_tag_icons (
            tag_id TEXT PRIMARY KEY,
            icon BLOB
        );

        CREATE TABLE IF NOT EXISTS state_jd_ext_tag_icons (
            tag_id TEXT PRIMARY KEY,
            icon BLOB
        );

        CREATE TABLE IF NOT EXISTS state_tags (
            tag_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            jd_area INTEGER,
            jd_id INTEGER,
            jd_ext INTEGER,
            label TEXT NOT NULL,
            UNIQUE(jd_area, jd_id, jd_ext)
        );

        CREATE TABLE IF NOT EXISTS state_jd_area_tags (
            tag_id TEXT PRIMARY KEY,
            [order] INTEGER NOT NULL UNIQUE,
            label TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS state_jd_id_tags (
            tag_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(parent_uuid, [order])
        );

        CREATE TABLE IF NOT EXISTS state_jd_ext_tags (
            tag_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(parent_uuid, [order])
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

        -- Indexes to accelerate lookups by parent_uuid
        CREATE INDEX IF NOT EXISTS idx_event_set_tag_path_parent_uuid
            ON event_set_tag_path(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_header_path_parent_uuid
            ON event_set_header_path(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_tags_parent_uuid_jd_id
            ON state_tags(parent_uuid, jd_id);
        CREATE INDEX IF NOT EXISTS idx_state_tags_parent_uuid_jd_ext
            ON state_tags(parent_uuid, jd_ext);
        CREATE INDEX IF NOT EXISTS idx_state_headers_parent_uuid_jd_id
            ON state_headers(parent_uuid, jd_id);
        CREATE INDEX IF NOT EXISTS idx_state_headers_parent_uuid_jd_ext
            ON state_headers(parent_uuid, jd_ext);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_ext_tag_order_parent_uuid
            ON event_set_jd_ext_tag_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_ext_header_order_parent_uuid
            ON event_set_jd_ext_header_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_id_tag_order_parent_uuid
            ON event_set_jd_id_tag_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_id_header_order_parent_uuid
            ON event_set_jd_id_header_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_ext_tags_parent_uuid
            ON state_jd_ext_tags(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_ext_headers_parent_uuid
            ON state_jd_ext_headers(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_id_tags_parent_uuid
            ON state_jd_id_tags(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_id_headers_parent_uuid
            ON state_jd_id_headers(parent_uuid);
    """)
    # Ensure existing databases have the parent_uuid column
    def ensure_parent_uuid(table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        if 'parent_uuid' not in [row[1] for row in cursor.fetchall()]:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN parent_uuid TEXT")

    for table in (
        "event_set_tag_path",
        "state_tags",
        "event_set_header_path",
        "state_headers",
        "event_set_jd_id_tag_order",
        "state_jd_id_tags",
        "event_set_jd_id_header_order",
        "state_jd_id_headers",
    ):
        ensure_parent_uuid(table)

    rebuild_state_tags(conn)
    rebuild_state_headers(conn)
    rebuild_state_jd_area_tags(conn)
    rebuild_state_jd_area_headers(conn)
    rebuild_state_jd_id_tags(conn)
    rebuild_state_jd_id_headers(conn)
    rebuild_state_jd_ext_tags(conn)
    rebuild_state_jd_ext_headers(conn)
    conn.commit()
    return conn

def rebuild_state_tags(conn):
    """Rebuild the state_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_tags;

        INSERT INTO state_tags (tag_id, parent_uuid, jd_area, jd_id, jd_ext, label)
        SELECT
            p.tag_id,
            p.parent_uuid,
            p.jd_area,
            p.jd_id,
            p.jd_ext,
            l.new_label
        FROM (
            SELECT
                p.tag_id,
                p.parent_uuid,
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

def rebuild_state_headers(conn):
    """Rebuild the state_headers table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_headers;

        INSERT INTO state_headers (header_id, parent_uuid, jd_area, jd_id, jd_ext, label)
        SELECT
            p.header_id,
            p.parent_uuid,
            p.jd_area,
            p.jd_id,
            p.jd_ext,
            l.new_label
        FROM (
            SELECT
                p.header_id,
                p.parent_uuid,
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

def rebuild_state_jd_area_tags(conn):
    """Rebuild the state_jd_area_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_area_tags;

        INSERT INTO state_jd_area_tags (tag_id, [order], label)
        SELECT
            o.tag_id,
            o.[order],
            l.new_label
        FROM (
            SELECT
                o.tag_id,
                o.[order],
                o.event_id
            FROM event_set_jd_area_tag_order o
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_jd_area_tag_order
                GROUP BY tag_id
            ) latest_order ON o.tag_id = latest_order.tag_id AND o.event_id = latest_order.max_event
        ) o
        JOIN (
            SELECT
                l.tag_id,
                l.new_label,
                l.event_id
            FROM event_set_jd_area_tag_label l
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_jd_area_tag_label
                GROUP BY tag_id
            ) latest_label ON l.tag_id = latest_label.tag_id AND l.event_id = latest_label.max_event
        ) l ON o.tag_id = l.tag_id
        WHERE o.tag_id NOT IN (SELECT tag_id FROM event_delete_jd_area_tag);
    """)

    cursor.executescript("""
        DELETE FROM state_jd_area_tag_icons;

        INSERT INTO state_jd_area_tag_icons (tag_id, icon)
        SELECT
            i.tag_id,
            i.icon
        FROM event_set_jd_area_tag_icon i
        JOIN (
            SELECT tag_id, MAX(event_id) AS max_event
            FROM event_set_jd_area_tag_icon
            GROUP BY tag_id
        ) latest ON i.tag_id = latest.tag_id AND i.event_id = latest.max_event
        WHERE i.tag_id NOT IN (SELECT tag_id FROM event_delete_jd_area_tag);
    """)
    conn.commit()

def rebuild_state_jd_area_headers(conn):
    """Rebuild the state_jd_area_headers table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_area_headers;

        INSERT INTO state_jd_area_headers (header_id, [order], label)
        SELECT
            o.header_id,
            o.[order],
            l.new_label
        FROM (
            SELECT
                o.header_id,
                o.[order],
                o.event_id
            FROM event_set_jd_area_header_order o
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_jd_area_header_order
                GROUP BY header_id
            ) latest_order ON o.header_id = latest_order.header_id AND o.event_id = latest_order.max_event
        ) o
        JOIN (
            SELECT
                l.header_id,
                l.new_label,
                l.event_id
            FROM event_set_jd_area_header_label l
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_jd_area_header_label
                GROUP BY header_id
            ) latest_label ON l.header_id = latest_label.header_id AND l.event_id = latest_label.max_event
        ) l ON o.header_id = l.header_id
        WHERE o.header_id NOT IN (SELECT header_id FROM event_delete_jd_area_header);
    """)
    conn.commit()

def rebuild_state_jd_id_tags(conn):
    """Rebuild the state_jd_id_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_id_tags;

        INSERT INTO state_jd_id_tags (tag_id, parent_uuid, [order], label)
        SELECT
            o.tag_id,
            o.parent_uuid,
            o.[order],
            l.new_label
        FROM (
            SELECT
                o.tag_id,
                o.parent_uuid,
                o.[order],
                o.event_id
            FROM event_set_jd_id_tag_order o
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_jd_id_tag_order
                GROUP BY tag_id
            ) latest_order ON o.tag_id = latest_order.tag_id AND o.event_id = latest_order.max_event
        ) o
        JOIN (
            SELECT
                l.tag_id,
                l.new_label,
                l.event_id
            FROM event_set_jd_id_tag_label l
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_jd_id_tag_label
                GROUP BY tag_id
            ) latest_label ON l.tag_id = latest_label.tag_id AND l.event_id = latest_label.max_event
        ) l ON o.tag_id = l.tag_id
        WHERE o.tag_id NOT IN (SELECT tag_id FROM event_delete_jd_id_tag);
    """)

    cursor.executescript("""
        DELETE FROM state_jd_id_tag_icons;

        INSERT INTO state_jd_id_tag_icons (tag_id, icon)
        SELECT
            i.tag_id,
            i.icon
        FROM event_set_jd_id_tag_icon i
        JOIN (
            SELECT tag_id, MAX(event_id) AS max_event
            FROM event_set_jd_id_tag_icon
            GROUP BY tag_id
        ) latest ON i.tag_id = latest.tag_id AND i.event_id = latest.max_event
        WHERE i.tag_id NOT IN (SELECT tag_id FROM event_delete_jd_id_tag);
    """)
    conn.commit()

def rebuild_state_jd_id_headers(conn):
    """Rebuild the state_jd_id_headers table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_id_headers;

        INSERT INTO state_jd_id_headers (header_id, parent_uuid, [order], label)
        SELECT
            o.header_id,
            o.parent_uuid,
            o.[order],
            l.new_label
        FROM (
            SELECT
                o.header_id,
                o.parent_uuid,
                o.[order],
                o.event_id
            FROM event_set_jd_id_header_order o
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_jd_id_header_order
                GROUP BY header_id
            ) latest_order ON o.header_id = latest_order.header_id AND o.event_id = latest_order.max_event
        ) o
        JOIN (
            SELECT
                l.header_id,
                l.new_label,
                l.event_id
            FROM event_set_jd_id_header_label l
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_jd_id_header_label
                GROUP BY header_id
            ) latest_label ON l.header_id = latest_label.header_id AND l.event_id = latest_label.max_event
        ) l ON o.header_id = l.header_id
        WHERE o.header_id NOT IN (SELECT header_id FROM event_delete_jd_id_header);
    """)
    conn.commit()

def rebuild_state_jd_ext_tags(conn):
    """Rebuild the state_jd_ext_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_ext_tags;

        INSERT INTO state_jd_ext_tags (tag_id, parent_uuid, [order], label)
        SELECT
            o.tag_id,
            o.parent_uuid,
            o.[order],
            l.new_label
        FROM (
            SELECT
                o.tag_id,
                o.parent_uuid,
                o.[order],
                o.event_id
            FROM event_set_jd_ext_tag_order o
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_jd_ext_tag_order
                GROUP BY tag_id
            ) latest_order ON o.tag_id = latest_order.tag_id AND o.event_id = latest_order.max_event
        ) o
        JOIN (
            SELECT
                l.tag_id,
                l.new_label,
                l.event_id
            FROM event_set_jd_ext_tag_label l
            JOIN (
                SELECT tag_id, MAX(event_id) AS max_event
                FROM event_set_jd_ext_tag_label
                GROUP BY tag_id
            ) latest_label ON l.tag_id = latest_label.tag_id AND l.event_id = latest_label.max_event
        ) l ON o.tag_id = l.tag_id
        WHERE o.tag_id NOT IN (SELECT tag_id FROM event_delete_jd_ext_tag);
    """)

    cursor.executescript("""
        DELETE FROM state_jd_ext_tag_icons;

        INSERT INTO state_jd_ext_tag_icons (tag_id, icon)
        SELECT
            i.tag_id,
            i.icon
        FROM event_set_jd_ext_tag_icon i
        JOIN (
            SELECT tag_id, MAX(event_id) AS max_event
            FROM event_set_jd_ext_tag_icon
            GROUP BY tag_id
        ) latest ON i.tag_id = latest.tag_id AND i.event_id = latest.max_event
        WHERE i.tag_id NOT IN (SELECT tag_id FROM event_delete_jd_ext_tag);
    """)
    conn.commit()

def rebuild_state_jd_ext_headers(conn):
    """Rebuild the state_jd_ext_headers table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_ext_headers;

        INSERT INTO state_jd_ext_headers (header_id, parent_uuid, [order], label)
        SELECT
            o.header_id,
            o.parent_uuid,
            o.[order],
            l.new_label
        FROM (
            SELECT
                o.header_id,
                o.parent_uuid,
                o.[order],
                o.event_id
            FROM event_set_jd_ext_header_order o
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_jd_ext_header_order
                GROUP BY header_id
            ) latest_order ON o.header_id = latest_order.header_id AND o.event_id = latest_order.max_event
        ) o
        JOIN (
            SELECT
                l.header_id,
                l.new_label,
                l.event_id
            FROM event_set_jd_ext_header_label l
            JOIN (
                SELECT header_id, MAX(event_id) AS max_event
                FROM event_set_jd_ext_header_label
                GROUP BY header_id
            ) latest_label ON l.header_id = latest_label.header_id AND l.event_id = latest_label.max_event
        ) l ON o.header_id = l.header_id
        WHERE o.header_id NOT IN (SELECT header_id FROM event_delete_jd_ext_header);
    """)
    conn.commit()

def create_jd_ext_tag(conn, parent_uuid, order, label):
    """Create a new jd_ext tag and return its tag_id, or None on conflict."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT tag_id FROM state_jd_ext_tags WHERE parent_uuid IS ? AND [order] = ?',
        (parent_uuid, order),
    )
    if cursor.fetchone():
        return None
    tag_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_ext_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_ext_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_ext_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, tag_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_ext_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
        (event_id, tag_id, label),
    )
    conn.commit()
    return tag_id

def delete_jd_ext_tag(conn, tag_id):
    """Delete an existing jd_ext tag."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_ext_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_ext_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
    conn.commit()

def create_jd_ext_header(conn, parent_uuid, order, label):
    """Create a new jd_ext header and return its header_id, or None on conflict."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT header_id FROM state_jd_ext_headers WHERE parent_uuid IS ? AND [order] = ?',
        (parent_uuid, order),
    )
    if cursor.fetchone():
        return None
    header_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_ext_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_ext_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_header_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_ext_header_order (event_id, header_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, header_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_ext_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return header_id

def update_jd_ext_header(conn, header_id, parent_uuid, order, label):
    """Update an existing jd_ext header. Returns True on success."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT header_id FROM state_jd_ext_headers WHERE parent_uuid IS ? AND [order] = ? AND header_id != ?',
        (parent_uuid, order, header_id),
    )
    if cursor.fetchone():
        return False
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_header_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_ext_header_order (event_id, header_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, header_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_ext_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return True

def delete_jd_ext_header(conn, header_id):
    """Delete an existing jd_ext header."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_ext_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_ext_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    conn.commit()

def create_jd_area_tag(conn, order, label):
    """Create a new jd_area tag and return its tag_id, or None if order conflict."""
    cursor = conn.cursor()
    cursor.execute('SELECT tag_id FROM state_jd_area_tags WHERE [order] = ?', (order,))
    if cursor.fetchone():
        return None
    tag_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_area_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_area_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_area_tag_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_area_tag_order (event_id, tag_id, [order]) VALUES (?, ?, ?)',
        (event_id, tag_id, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_area_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_area_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
        (event_id, tag_id, label),
    )
    conn.commit()
    return tag_id

def create_jd_area_header(conn, order, label):
    """Create a new jd_area header and return its header_id, or None on conflict."""
    cursor = conn.cursor()
    cursor.execute('SELECT header_id FROM state_jd_area_headers WHERE [order] = ?', (order,))
    if cursor.fetchone():
        return None
    header_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_area_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_area_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_area_header_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_area_header_order (event_id, header_id, [order]) VALUES (?, ?, ?)',
        (event_id, header_id, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_area_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_area_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return header_id

def update_jd_area_header(conn, header_id, order, label):
    """Update an existing jd_area header. Returns True on success."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT header_id FROM state_jd_area_headers WHERE [order] = ? AND header_id != ?',
        (order, header_id),
    )
    if cursor.fetchone():
        return False
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_area_header_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_area_header_order (event_id, header_id, [order]) VALUES (?, ?, ?)',
        (event_id, header_id, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_area_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_area_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return True

def delete_jd_area_header(conn, header_id):
    """Delete an existing jd_area header."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_area_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_area_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    conn.commit()

def delete_jd_area_tag(conn, tag_id):
    """Delete an existing jd_area tag."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_area_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_area_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
    conn.commit()

def create_jd_id_tag(conn, parent_uuid, order, label):
    """Create a new jd_id tag and return its tag_id, or None if order conflict."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT tag_id FROM state_jd_id_tags WHERE parent_uuid IS ? AND [order] = ?',
        (parent_uuid, order),
    )
    if cursor.fetchone():
        return None
    tag_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_id_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_id_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_id_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, tag_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_id_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
        (event_id, tag_id, label),
    )
    conn.commit()
    return tag_id

def create_jd_id_header(conn, parent_uuid, order, label):
    """Create a new jd_id header and return its header_id, or None on conflict."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT header_id FROM state_jd_id_headers WHERE parent_uuid IS ? AND [order] = ?',
        (parent_uuid, order),
    )
    if cursor.fetchone():
        return None
    header_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_id_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_id_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_header_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_id_header_order (event_id, header_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, header_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_id_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return header_id

def update_jd_id_header(conn, header_id, parent_uuid, order, label):
    """Update an existing jd_id header. Returns True on success."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT header_id FROM state_jd_id_headers WHERE parent_uuid IS ? AND [order] = ? AND header_id != ?',
        (parent_uuid, order, header_id),
    )
    if cursor.fetchone():
        return False
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_header_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_id_header_order (event_id, header_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, header_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_id_header_label (event_id, header_id, new_label) VALUES (?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return True

def delete_jd_id_header(conn, header_id):
    """Delete an existing jd_id header."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_id_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_id_header (event_id, header_id) VALUES (?, ?)",
        (event_id, header_id),
    )
    conn.commit()

def delete_jd_id_tag(conn, tag_id):
    """Delete an existing jd_id tag."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_id_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_id_tag (event_id, tag_id) VALUES (?, ?)",
        (event_id, tag_id),
    )
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
    parent_uuid = None
    if jd_id is not None:
        if jd_ext is None:
            cursor.execute(
                "SELECT tag_id FROM state_tags WHERE jd_area IS ? AND jd_id IS NULL AND jd_ext IS NULL",
                (jd_area,),
            )
        else:
            cursor.execute(
                "SELECT tag_id FROM state_tags WHERE jd_area IS ? AND jd_id IS ? AND jd_ext IS NULL",
                (jd_area, jd_id),
            )
        row = cursor.fetchone()
        parent_uuid = row[0] if row else None
    cursor.execute(
        "INSERT INTO event_set_tag_path (event_id, tag_id, parent_uuid, jd_area, jd_id, jd_ext) VALUES (?, ?, ?, ?, ?, ?)",
        (event_id, tag_id, parent_uuid, jd_area, jd_id, jd_ext),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute("INSERT INTO event_set_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)", (event_id, tag_id, label))
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
    parent_uuid = None
    if jd_id is not None:
        if jd_ext is None:
            cursor.execute(
                "SELECT tag_id FROM state_tags WHERE jd_area = ? AND jd_id IS NULL AND jd_ext IS NULL",
                (jd_area,),
            )
        else:
            cursor.execute(
                "SELECT tag_id FROM state_tags WHERE jd_area = ? AND jd_id = ? AND jd_ext IS NULL",
                (jd_area, jd_id),
            )
        row = cursor.fetchone()
        parent_uuid = row[0] if row else None
    cursor.execute(
        "INSERT INTO event_set_header_path (event_id, header_id, parent_uuid, jd_area, jd_id, jd_ext) VALUES (?, ?, ?, ?, ?, ?)",
        (event_id, header_id, parent_uuid, jd_area, jd_id, jd_ext),
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
    parent_uuid = None
    if jd_id is not None:
        if jd_ext is None:
            cursor.execute(
                "SELECT tag_id FROM state_tags WHERE jd_area = ? AND jd_id IS NULL AND jd_ext IS NULL",
                (jd_area,),
            )
        else:
            cursor.execute(
                "SELECT tag_id FROM state_tags WHERE jd_area = ? AND jd_id = ? AND jd_ext IS NULL",
                (jd_area, jd_id),
            )
        row = cursor.fetchone()
        parent_uuid = row[0] if row else None
    cursor.execute(
        "INSERT INTO event_set_header_path (event_id, header_id, parent_uuid, jd_area, jd_id, jd_ext) VALUES (?, ?, ?, ?, ?, ?)",
        (event_id, header_id, parent_uuid, jd_area, jd_id, jd_ext),
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
