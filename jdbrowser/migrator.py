import os
import sqlite3
import importlib.util
from typing import List, Tuple

# TokyoNight Dark color palette
TOKYO_COLORS = {
    "bg": (26, 27, 38),       # #1a1b26
    "fg": (192, 202, 245),    # #c0caf5
    "blue": (122, 162, 247),  # #7aa2f7
    "green": (158, 206, 106), # #9ece6a
    "yellow": (224, 175, 104),# #e0af68
    "red": (247, 118, 142),   # #f7768e
}

RESET = "\x1b[0m"


def rgb_escape(fg=None, bg=None) -> str:
    parts: List[str] = []
    if fg is not None:
        parts.append(f"38;2;{fg[0]};{fg[1]};{fg[2]}")
    if bg is not None:
        parts.append(f"48;2;{bg[0]};{bg[1]};{bg[2]}")
    if not parts:
        return ""
    return "\x1b[" + ";".join(parts) + "m"


def color_text(text: str, fg=None, bg=None) -> str:
    return f"{rgb_escape(fg, bg)}{text}{RESET}"


def load_migration(path: str):
    spec = importlib.util.spec_from_file_location("migration", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def get_migrations() -> List[Tuple[str, str]]:
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    files = [f for f in os.listdir(migrations_dir) if f.endswith(".py") and f != "__init__.py"]
    files.sort()
    return [(f[:-3], os.path.join(migrations_dir, f)) for f in files]


def apply_migrations(conn: sqlite3.Connection, use_tui: bool = False):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")
    cursor.execute("SELECT version FROM schema_migrations")
    applied = {row[0] for row in cursor.fetchall()}

    migrations = get_migrations()
    if use_tui:
        print(color_text("== JDBrowser Migrations ==", fg=TOKYO_COLORS["blue"], bg=TOKYO_COLORS["bg"]))
    for version, path in migrations:
        if version in applied:
            if use_tui:
                line = f"✓ {version} (skipped)"
                print(color_text(line, fg=TOKYO_COLORS["yellow"], bg=TOKYO_COLORS["bg"]))
            continue
        module = load_migration(path)
        if use_tui:
            line = f"→ {version}"
            print(color_text(line, fg=TOKYO_COLORS["fg"], bg=TOKYO_COLORS["bg"]))
        module.up(conn)
        cursor.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
        if use_tui:
            line = f"✓ {version}"
            print(color_text(line, fg=TOKYO_COLORS["green"], bg=TOKYO_COLORS["bg"]))


def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    apply_migrations(conn, use_tui=True)
    conn.close()
