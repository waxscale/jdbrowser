from jdbrowser.migrator import migrate
import sys
import os

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), 'tag.db')
    migrate(db_path)
