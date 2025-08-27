import os
import sys
import re
import subprocess

from jdbrowser.migrator import migrate, rollback, TOKYO_COLORS, color_text

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "jdbrowser", "migrations")
DB_PATH = os.path.join(os.path.dirname(__file__), "tag.db")


def add_migration(name: str) -> None:
    files = [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.py') and f != '__init__.py']
    files.sort()
    next_num = int(files[-1].split('_')[0]) + 1 if files else 1
    slug = re.sub(r'\W+', '_', name).lower()
    filename = f"{next_num:04d}_{slug}.py"
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write("def up(conn):\n    pass\n\n\ndef down(conn):\n    pass\n")
    line = f"Created {filename}"
    print(color_text(line, fg=TOKYO_COLORS['green'], bg=TOKYO_COLORS['bg']))
    subprocess.run(["nvim", path])


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: db [add NAME|migrate|rollback]")
        return
    cmd = args[0]
    if cmd == 'add':
        if len(args) < 2:
            print("Usage: db add NAME")
            return
        add_migration(args[1])
    elif cmd == 'migrate':
        migrate(DB_PATH)
    elif cmd == 'rollback':
        rollback(DB_PATH)
    else:
        print("Usage: db [add NAME|migrate|rollback]")


if __name__ == '__main__':
    main()
