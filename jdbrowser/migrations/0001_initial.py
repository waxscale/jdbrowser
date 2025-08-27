import sqlite3

def up(conn: sqlite3.Connection):
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
        CREATE INDEX IF NOT EXISTS idx_state_jd_ext_tags_parent_uuid
            ON state_jd_ext_tags(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_ext_headers_parent_uuid
            ON state_jd_ext_headers(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_id_tags_parent_uuid
            ON state_jd_id_tags(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_state_jd_id_headers_parent_uuid
            ON state_jd_id_headers(parent_uuid);
    """)
    conn.commit()


def down(conn: sqlite3.Connection):
    cursor = conn.cursor()
    tables = [
        "events",
        "event_create_jd_area_tag",
        "event_set_jd_area_tag_order",
        "event_set_jd_area_tag_label",
        "event_set_jd_area_tag_icon",
        "event_delete_jd_area_tag",
        "event_create_jd_area_header",
        "event_set_jd_area_header_order",
        "event_set_jd_area_header_label",
        "event_delete_jd_area_header",
        "event_create_jd_id_tag",
        "event_set_jd_id_tag_order",
        "event_set_jd_id_tag_label",
        "event_set_jd_id_tag_icon",
        "event_delete_jd_id_tag",
        "event_create_jd_id_header",
        "event_set_jd_id_header_order",
        "event_set_jd_id_header_label",
        "event_delete_jd_id_header",
        "event_create_jd_ext_tag",
        "event_set_jd_ext_tag_order",
        "event_set_jd_ext_tag_label",
        "event_set_jd_ext_tag_icon",
        "event_delete_jd_ext_tag",
        "event_create_jd_ext_header",
        "event_set_jd_ext_header_order",
        "event_set_jd_ext_header_label",
        "event_delete_jd_ext_header",
        "event_create_jd_directory",
        "event_set_jd_directory_order",
        "event_set_jd_directory_label",
        "event_set_jd_directory_icon",
        "event_delete_jd_directory",
        "event_add_directory_tag",
        "event_remove_directory_tag",
        "state_jd_area_headers",
        "state_jd_id_headers",
        "state_jd_ext_headers",
        "state_jd_area_tag_icons",
        "state_jd_id_tag_icons",
        "state_jd_ext_tag_icons",
        "state_jd_directory_icons",
        "state_jd_directory_tags",
        "state_jd_area_tags",
        "state_jd_id_tags",
        "state_jd_ext_tags",
        "state_jd_directories",
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    indexes = [
        "idx_event_set_jd_ext_tag_order_parent_uuid",
        "idx_event_set_jd_ext_header_order_parent_uuid",
        "idx_event_set_jd_id_tag_order_parent_uuid",
        "idx_event_set_jd_id_header_order_parent_uuid",
        "idx_state_jd_ext_tags_parent_uuid",
        "idx_state_jd_ext_headers_parent_uuid",
        "idx_state_jd_id_tags_parent_uuid",
        "idx_state_jd_id_headers_parent_uuid",
    ]
    for index in indexes:
        cursor.execute(f"DROP INDEX IF EXISTS {index}")
    conn.commit()
