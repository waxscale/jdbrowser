import sqlite3


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    )
    return cur.fetchone() is not None


def up(conn: sqlite3.Connection) -> None:
    # Ensure foreign keys setting is handled explicitly during table rebuilds
    conn.execute("PRAGMA foreign_keys = OFF")

    # state_tags: add FK parent_id -> state_tags(tag_id)
    if table_exists(conn, "state_tags"):
        # Clean any orphan parent_id values that would violate the new FK
        conn.execute(
            """
            UPDATE state_tags
            SET parent_id = NULL
            WHERE parent_id IS NOT NULL
              AND parent_id NOT IN (SELECT tag_id FROM state_tags)
            """
        )

        conn.execute(
            """
            CREATE TABLE state_tags__new (
                tag_id TEXT PRIMARY KEY,
                parent_id TEXT,
                item_order INTEGER NOT NULL,
                label TEXT NOT NULL,
                UNIQUE(parent_id, item_order),
                FOREIGN KEY(parent_id) REFERENCES state_tags(tag_id)
                    ON DELETE SET NULL ON UPDATE NO ACTION
            )
            """
        )
        conn.execute(
            "INSERT INTO state_tags__new (tag_id, parent_id, item_order, label)\n"
            "SELECT tag_id, parent_id, item_order, label FROM state_tags"
        )
        conn.execute("DROP TABLE state_tags")
        conn.execute("ALTER TABLE state_tags__new RENAME TO state_tags")

    # state_headers: add FK parent_id -> state_headers(header_id)
    if table_exists(conn, "state_headers"):
        # Clean any orphan parent_id values that would violate the new FK
        conn.execute(
            """
            UPDATE state_headers
            SET parent_id = NULL
            WHERE parent_id IS NOT NULL
              AND parent_id NOT IN (SELECT header_id FROM state_headers)
            """
        )

        conn.execute(
            """
            CREATE TABLE state_headers__new (
                header_id TEXT PRIMARY KEY,
                parent_id TEXT,
                item_order INTEGER NOT NULL,
                label TEXT NOT NULL,
                UNIQUE(parent_id, item_order),
                FOREIGN KEY(parent_id) REFERENCES state_headers(header_id)
                    ON DELETE SET NULL ON UPDATE NO ACTION
            )
            """
        )
        conn.execute(
            "INSERT INTO state_headers__new (header_id, parent_id, item_order, label)\n"
            "SELECT header_id, parent_id, item_order, label FROM state_headers"
        )
        conn.execute("DROP TABLE state_headers")
        conn.execute("ALTER TABLE state_headers__new RENAME TO state_headers")

    # state_tag_icons: add FK tag_id -> state_tags(tag_id)
    if table_exists(conn, "state_tag_icons") and table_exists(conn, "state_tags"):
        # Remove any icons whose tag does not exist
        conn.execute(
            "DELETE FROM state_tag_icons WHERE tag_id NOT IN (SELECT tag_id FROM state_tags)"
        )

        conn.execute(
            """
            CREATE TABLE state_tag_icons__new (
                tag_id TEXT PRIMARY KEY,
                icon BLOB,
                FOREIGN KEY(tag_id) REFERENCES state_tags(tag_id)
                    ON DELETE CASCADE ON UPDATE NO ACTION
            )
            """
        )
        conn.execute(
            "INSERT INTO state_tag_icons__new (tag_id, icon)\n"
            "SELECT tag_id, icon FROM state_tag_icons"
        )
        conn.execute("DROP TABLE state_tag_icons")
        conn.execute("ALTER TABLE state_tag_icons__new RENAME TO state_tag_icons")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()


def down(conn: sqlite3.Connection) -> None:
    # Revert to previous definitions without the added foreign keys
    conn.execute("PRAGMA foreign_keys = OFF")

    if table_exists(conn, "state_tag_icons"):
        conn.execute(
            """
            CREATE TABLE state_tag_icons__old (
                tag_id TEXT PRIMARY KEY,
                icon BLOB
            )
            """
        )
        conn.execute(
            "INSERT INTO state_tag_icons__old (tag_id, icon)\n"
            "SELECT tag_id, icon FROM state_tag_icons"
        )
        conn.execute("DROP TABLE state_tag_icons")
        conn.execute("ALTER TABLE state_tag_icons__old RENAME TO state_tag_icons")

    if table_exists(conn, "state_headers"):
        conn.execute(
            """
            CREATE TABLE state_headers__old (
                header_id TEXT PRIMARY KEY,
                parent_id TEXT,
                item_order INTEGER NOT NULL,
                label TEXT NOT NULL,
                UNIQUE(parent_id, item_order)
            )
            """
        )
        conn.execute(
            "INSERT INTO state_headers__old (header_id, parent_id, item_order, label)\n"
            "SELECT header_id, parent_id, item_order, label FROM state_headers"
        )
        conn.execute("DROP TABLE state_headers")
        conn.execute("ALTER TABLE state_headers__old RENAME TO state_headers")

    if table_exists(conn, "state_tags"):
        conn.execute(
            """
            CREATE TABLE state_tags__old (
                tag_id TEXT PRIMARY KEY,
                parent_id TEXT,
                item_order INTEGER NOT NULL,
                label TEXT NOT NULL,
                UNIQUE(parent_id, item_order)
            )
            """
        )
        conn.execute(
            "INSERT INTO state_tags__old (tag_id, parent_id, item_order, label)\n"
            "SELECT tag_id, parent_id, item_order, label FROM state_tags"
        )
        conn.execute("DROP TABLE state_tags")
        conn.execute("ALTER TABLE state_tags__old RENAME TO state_tags")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()

