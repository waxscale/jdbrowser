import os
import sys
import re

from jdbrowser.migrator import migrate, TOKYO_COLORS, color_text

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "jdbrowser", "migrations")


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


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] != 'migrate':
        print("Usage: python db.py migrate [DB_PATH]\n       python db.py migrate add NAME")
        return
    if len(args) >= 2 and args[1] == 'add':
        if len(args) < 3:
            print("Usage: python db.py migrate add NAME")
            return
        add_migration(args[2])
    else:
        db_path = args[1] if len(args) > 1 else os.path.join(os.getcwd(), 'tag.db')
        migrate(db_path)


if __name__ == '__main__':
    main()
