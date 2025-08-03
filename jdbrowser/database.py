"""Database layer for jdbrowser using parent based hierarchy.

This module replaces the previous jd_area/jd_id/jd_ext numbering
scheme with a simple parent/child relationship.  Each item (tag or
header) keeps a reference to the UUID of its parent and an integer
``item_order`` used for sorting amongst its siblings.

The schema is implemented using an append only event log similar to the
previous design.  Convenience helper functions are provided for common
operations used by the application.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from typing import Optional


def _latest_event(table: str, id_col: str) -> str:
    """Helper returning SQL for selecting latest event per id."""

    return f"""
        SELECT {id_col}, MAX(event_id) AS max_event
        FROM {table}
        GROUP BY {id_col}
    """


def setup_database(db_path: str) -> sqlite3.Connection:
    """Initialise database and rebuild state tables."""

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );

        CREATE TABLE IF NOT EXISTS event_create_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_tag_parent (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            parent_id TEXT,
            item_order INTEGER NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_tag_label (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_tag_icon (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            icon BLOB,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_tag (
            event_id INTEGER PRIMARY KEY,
            tag_id TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_create_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_header_parent (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            parent_id TEXT,
            item_order INTEGER NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_set_header_label (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            new_label TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_delete_header (
            event_id INTEGER PRIMARY KEY,
            header_id TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS state_tag_icons (
            tag_id TEXT PRIMARY KEY,
            icon BLOB
        );

        CREATE TABLE IF NOT EXISTS state_tags (
            tag_id TEXT PRIMARY KEY,
            parent_id TEXT,
            item_order INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(parent_id, item_order)
        );

        CREATE TABLE IF NOT EXISTS state_headers (
            header_id TEXT PRIMARY KEY,
            parent_id TEXT,
            item_order INTEGER NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(parent_id, item_order)
        );
        """
    )

    rebuild_state_tags(conn)
    rebuild_state_headers(conn)
    conn.commit()
    return conn


def rebuild_state_tags(conn: sqlite3.Connection) -> None:
    """Rebuild ``state_tags`` from the event log."""

    cursor = conn.cursor()
    cursor.executescript(
        f"""
        DELETE FROM state_tags;

        INSERT INTO state_tags(tag_id, parent_id, item_order, label)
        SELECT p.tag_id, p.parent_id, p.item_order, l.new_label
        FROM (
            SELECT p.tag_id, p.parent_id, p.item_order, p.event_id
            FROM event_set_tag_parent p
            JOIN ({_latest_event('event_set_tag_parent','tag_id')}) latest
            ON p.tag_id = latest.tag_id AND p.event_id = latest.max_event
        ) p
        JOIN (
            SELECT l.tag_id, l.new_label, l.event_id
            FROM event_set_tag_label l
            JOIN ({_latest_event('event_set_tag_label','tag_id')}) latest
            ON l.tag_id = latest.tag_id AND l.event_id = latest.max_event
        ) l ON p.tag_id = l.tag_id
        WHERE p.tag_id NOT IN (SELECT tag_id FROM event_delete_tag);

        DELETE FROM state_tag_icons;

        INSERT INTO state_tag_icons(tag_id, icon)
        SELECT i.tag_id, i.icon
        FROM event_set_tag_icon i
        JOIN ({_latest_event('event_set_tag_icon','tag_id')}) latest
          ON i.tag_id = latest.tag_id AND i.event_id = latest.max_event
        WHERE i.tag_id NOT IN (SELECT tag_id FROM event_delete_tag);
        """
    )
    conn.commit()


def rebuild_state_headers(conn: sqlite3.Connection) -> None:
    """Rebuild ``state_headers`` from the event log."""

    cursor = conn.cursor()
    cursor.executescript(
        f"""
        DELETE FROM state_headers;

        INSERT INTO state_headers(header_id, parent_id, item_order, label)
        SELECT p.header_id, p.parent_id, p.item_order, l.new_label
        FROM (
            SELECT p.header_id, p.parent_id, p.item_order, p.event_id
            FROM event_set_header_parent p
            JOIN ({_latest_event('event_set_header_parent','header_id')}) latest
              ON p.header_id = latest.header_id AND p.event_id = latest.max_event
        ) p
        JOIN (
            SELECT l.header_id, l.new_label, l.event_id
            FROM event_set_header_label l
            JOIN ({_latest_event('event_set_header_label','header_id')}) latest
              ON l.header_id = latest.header_id AND l.event_id = latest.max_event
        ) l ON p.header_id = l.header_id
        WHERE p.header_id NOT IN (SELECT header_id FROM event_delete_header);
        """
    )
    conn.commit()


def _check_parent_depth(cursor: sqlite3.Cursor, parent_id: Optional[str]) -> bool:
    """Return True if ``parent_id`` represents a valid parent (depth <= 2)."""

    if parent_id is None:
        return True

    cursor.execute(
        "SELECT parent_id FROM state_tags WHERE tag_id = ?", (parent_id,)
    )
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "SELECT parent_id FROM state_headers WHERE header_id = ?", (parent_id,)
        )
        row = cursor.fetchone()

    if row is None:
        return False  # parent does not exist

    if row[0] is None:
        return True  # parent at top level

    # check grandparent
    cursor.execute(
        "SELECT parent_id FROM state_tags WHERE tag_id = ?", (row[0],)
    )
    gp = cursor.fetchone()
    if gp is None:
        cursor.execute(
            "SELECT parent_id FROM state_headers WHERE header_id = ?", (row[0],)
        )
        gp = cursor.fetchone()

    # grandparent exists but has its own parent -> depth > 2
    return gp is not None and gp[0] is None


def create_tag(
    conn: sqlite3.Connection,
    parent_id: Optional[str],
    item_order: int,
    label: str,
) -> Optional[str]:
    """Create a tag.  Returns the new tag_id or ``None`` on failure."""

    cursor = conn.cursor()
    if not _check_parent_depth(cursor, parent_id):
        return None

    cursor.execute(
        "SELECT tag_id FROM state_tags WHERE parent_id IS ? AND item_order = ?",
        (parent_id, item_order),
    )
    if cursor.fetchone():
        return None

    tag_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events(event_type) VALUES('create_tag')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_tag(event_id, tag_id) VALUES(?, ?)",
        (event_id, tag_id),
    )
    cursor.execute("INSERT INTO events(event_type) VALUES('set_tag_parent')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_tag_parent(event_id, tag_id, parent_id, item_order) VALUES(?, ?, ?, ?)",
        (event_id, tag_id, parent_id, item_order),
    )
    cursor.execute("INSERT INTO events(event_type) VALUES('set_tag_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_tag_label(event_id, tag_id, new_label) VALUES(?, ?, ?)",
        (event_id, tag_id, label),
    )
    conn.commit()
    return tag_id


def create_header(
    conn: sqlite3.Connection,
    parent_id: Optional[str],
    item_order: int,
    label: str,
) -> Optional[str]:
    """Create a header.  Returns ``header_id`` or ``None`` on failure."""

    cursor = conn.cursor()
    if not _check_parent_depth(cursor, parent_id):
        return None

    cursor.execute(
        "SELECT header_id FROM state_headers WHERE parent_id IS ? AND item_order = ?",
        (parent_id, item_order),
    )
    if cursor.fetchone():
        return None

    header_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO events(event_type) VALUES('create_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_create_header(event_id, header_id) VALUES(?, ?)",
        (event_id, header_id),
    )
    cursor.execute("INSERT INTO events(event_type) VALUES('set_header_parent')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_parent(event_id, header_id, parent_id, item_order) VALUES(?, ?, ?, ?)",
        (event_id, header_id, parent_id, item_order),
    )
    cursor.execute("INSERT INTO events(event_type) VALUES('set_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_label(event_id, header_id, new_label) VALUES(?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return header_id


def update_header(
    conn: sqlite3.Connection,
    header_id: str,
    parent_id: Optional[str],
    item_order: int,
    label: str,
) -> bool:
    """Update an existing header.  Returns ``True`` on success."""

    cursor = conn.cursor()
    if not _check_parent_depth(cursor, parent_id):
        return False

    cursor.execute(
        "SELECT header_id FROM state_headers WHERE parent_id IS ? AND item_order = ? AND header_id != ?",
        (parent_id, item_order, header_id),
    )
    if cursor.fetchone():
        return False

    cursor.execute("INSERT INTO events(event_type) VALUES('set_header_parent')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_parent(event_id, header_id, parent_id, item_order) VALUES(?, ?, ?, ?)",
        (event_id, header_id, parent_id, item_order),
    )
    cursor.execute("INSERT INTO events(event_type) VALUES('set_header_label')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_set_header_label(event_id, header_id, new_label) VALUES(?, ?, ?)",
        (event_id, header_id, label),
    )
    conn.commit()
    return True


def delete_header(conn: sqlite3.Connection, header_id: str) -> None:
    """Delete a header."""

    cursor = conn.cursor()
    cursor.execute("INSERT INTO events(event_type) VALUES('delete_header')")
    event_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO event_delete_header(event_id, header_id) VALUES(?, ?)",
        (event_id, header_id),
    )
    conn.commit()


__all__ = [
    "setup_database",
    "rebuild_state_tags",
    "rebuild_state_headers",
    "create_tag",
    "create_header",
    "update_header",
    "delete_header",
]

