import sqlite3
import uuid

_shared_connection = None


def setup_database(db_path):
    """Initialize SQLite database tables with triggers and state constraints.

    A single SQLite connection is reused across the application so that all
    pages share the same database handle.
    """
    global _shared_connection
    if _shared_connection is not None:
        return _shared_connection
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL CHECK (
                event_type IN (
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
                    'delete_jd_ext_header',
                    'create_jd_directory',
                    'set_jd_directory_order',
                    'set_jd_directory_label',
                    'set_jd_directory_icon',
                    'delete_jd_directory',
                    'add_directory_tag',
                    'remove_directory_tag'
                )
            ),
            timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
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

        CREATE TABLE IF NOT EXISTS event_create_jd_directory (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_directory_order (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_directory_label (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_jd_directory_icon (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            icon BLOB,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_jd_directory (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_add_directory_tag (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_remove_directory_tag (
            event_id INTEGER PRIMARY KEY,
            directory_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
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

        CREATE TABLE IF NOT EXISTS state_jd_directory_icons (
            directory_id TEXT PRIMARY KEY,
            icon BLOB
        );

        DROP TABLE IF EXISTS state_jd_directory_tags;
        CREATE TABLE state_jd_directory_tags (
            directory_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            PRIMARY KEY (directory_id, tag_id)
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

        DROP TABLE IF EXISTS state_jd_directories;
        CREATE TABLE state_jd_directories (
            directory_id TEXT PRIMARY KEY,
            parent_uuid TEXT,
            [order] INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE([order])
        );

        -- Indexes to accelerate lookups by parent_uuid
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_ext_tag_order_parent_uuid
            ON event_set_jd_ext_tag_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_ext_header_order_parent_uuid
            ON event_set_jd_ext_header_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_id_tag_order_parent_uuid
            ON event_set_jd_id_tag_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_id_header_order_parent_uuid
            ON event_set_jd_id_header_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_event_set_jd_directory_order_parent_uuid
            ON event_set_jd_directory_order(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_ext_tags_parent_uuid
            ON state_jd_ext_tags(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_ext_headers_parent_uuid
            ON state_jd_ext_headers(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_id_tags_parent_uuid
            ON state_jd_id_tags(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_id_headers_parent_uuid
            ON state_jd_id_headers(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_directories_parent_uuid
            ON state_jd_directories(parent_uuid);
    """)
    # Ensure existing databases have required columns
    def ensure_column(table_name, column_name, column_type="TEXT"):
        cursor.execute(f"PRAGMA table_info({table_name})")
        if column_name not in [row[1] for row in cursor.fetchall()]:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )

    for table in (
        "event_set_jd_id_tag_order",
        "state_jd_id_tags",
        "event_set_jd_id_header_order",
        "state_jd_id_headers",
        "event_set_jd_ext_tag_order",
        "state_jd_ext_tags",
        "event_set_jd_ext_header_order",
        "state_jd_ext_headers",
        "event_set_jd_directory_order",
        "state_jd_directories",
    ):
        ensure_column(table, "parent_uuid")

    rebuild_state_jd_area_tags(conn)
    rebuild_state_jd_area_headers(conn)
    rebuild_state_jd_id_tags(conn)
    rebuild_state_jd_id_headers(conn)
    rebuild_state_jd_ext_tags(conn)
    rebuild_state_jd_ext_headers(conn)
    rebuild_state_jd_directories(conn)
    rebuild_state_directory_tags(conn)
    conn.commit()
    _shared_connection = conn
    return _shared_connection

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
    rebuild_state_directory_tags(conn)

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
    rebuild_state_directory_tags(conn)

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
    rebuild_state_directory_tags(conn)

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

def rebuild_state_jd_directories(conn):
    """Rebuild the state_jd_directories table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_directories;

        WITH latest_order AS (
            SELECT
                o.directory_id,
                o.parent_uuid,
                o.[order]
            FROM event_set_jd_directory_order o
            JOIN (
                SELECT directory_id, MAX(event_id) AS max_event
                FROM event_set_jd_directory_order
                GROUP BY directory_id
            ) lo ON o.directory_id = lo.directory_id AND o.event_id = lo.max_event
        ),
        latest_label AS (
            SELECT
                l.directory_id,
                l.new_label
            FROM event_set_jd_directory_label l
            JOIN (
                SELECT directory_id, MAX(event_id) AS max_event
                FROM event_set_jd_directory_label
                GROUP BY directory_id
            ) ll ON l.directory_id = ll.directory_id AND l.event_id = ll.max_event
        )
        INSERT INTO state_jd_directories (directory_id, parent_uuid, [order], label)
        SELECT
            o.directory_id,
            o.parent_uuid,
            o.[order],
            COALESCE(l.new_label, '') AS label
        FROM latest_order o
        LEFT JOIN latest_label l ON o.directory_id = l.directory_id
        WHERE o.directory_id NOT IN (SELECT directory_id FROM event_delete_jd_directory);
    """)

    cursor.executescript("""
        DELETE FROM state_jd_directory_icons;

        INSERT INTO state_jd_directory_icons (directory_id, icon)
        SELECT
            i.directory_id,
            i.icon
        FROM event_set_jd_directory_icon i
        JOIN (
            SELECT directory_id, MAX(event_id) AS max_event
            FROM event_set_jd_directory_icon
            GROUP BY directory_id
        ) latest ON i.directory_id = latest.directory_id AND i.event_id = latest.max_event
        WHERE i.directory_id NOT IN (SELECT directory_id FROM event_delete_jd_directory);
    """)
    conn.commit()


def rebuild_state_directory_tags(conn):
    """Rebuild the state_jd_directory_tags table from the event log."""
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM state_jd_directory_tags;

        WITH tag_actions AS (
            SELECT directory_id, tag_id, event_id, 1 AS is_add FROM event_add_directory_tag
            UNION ALL
            SELECT directory_id, tag_id, event_id, 0 AS is_add FROM event_remove_directory_tag
        ),
        latest AS (
            SELECT directory_id, tag_id, MAX(event_id) AS max_event
            FROM tag_actions
            GROUP BY directory_id, tag_id
        )
        INSERT INTO state_jd_directory_tags (directory_id, tag_id)
        SELECT a.directory_id, a.tag_id
        FROM tag_actions a
        JOIN latest l ON a.directory_id = l.directory_id
                     AND a.tag_id = l.tag_id
                     AND a.event_id = l.max_event
        WHERE a.is_add = 1
          AND a.directory_id NOT IN (SELECT directory_id FROM event_delete_jd_directory)
          AND a.tag_id NOT IN (
              SELECT tag_id FROM event_delete_jd_ext_tag
              UNION SELECT tag_id FROM event_delete_jd_id_tag
              UNION SELECT tag_id FROM event_delete_jd_area_tag
          );
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

def create_jd_directory(conn, parent_uuid, order, label):
    """Create a new directory and return its directory_id, or None on conflict."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT directory_id FROM state_jd_directories WHERE [order] = ?',
        (order,),
    )
    if cursor.fetchone():
        return None
    directory_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events (event_type) VALUES ('create_jd_directory')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_jd_directory (event_id, directory_id) VALUES (?, ?)",
        (event_id, directory_id),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_order')")
    event_id = cursor.lastrowid
    cursor.execute(
        'INSERT INTO event_set_jd_directory_order (event_id, directory_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)',
        (event_id, directory_id, parent_uuid, order),
    )
    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_jd_directory_label (event_id, directory_id, new_label) VALUES (?, ?, ?)",
        (event_id, directory_id, label),
    )
    conn.commit()
    return directory_id

def delete_jd_directory(conn, directory_id):
    """Delete an existing directory."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('delete_jd_directory')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_jd_directory (event_id, directory_id) VALUES (?, ?)",
        (event_id, directory_id),
    )
    conn.commit()

def add_directory_tag(conn, directory_id, tag_uuid):
    """Associate a directory with a tag."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('add_directory_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_add_directory_tag (event_id, directory_id, tag_id) VALUES (?, ?, ?)",
        (event_id, directory_id, tag_uuid),
    )
    conn.commit()

def remove_directory_tag(conn, directory_id, tag_uuid):
    """Remove an association between a directory and a tag."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_type) VALUES ('remove_directory_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_remove_directory_tag (event_id, directory_id, tag_id) VALUES (?, ?, ?)",
        (event_id, directory_id, tag_uuid),
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
