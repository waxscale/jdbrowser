__version__ = "1.0.0"

import os

from .database import setup_database

# Global pointer to the main application window.
main_window = None

# Global pointer to the currently displayed page widget.
# This can hold a JdAreaPage, JdIdPage, JdExtPage or JdDirectoryListPage.
current_page = None

# Shared database connection used throughout the application.
xdg_data_home = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
db_dir = os.path.join(xdg_data_home, "jdbrowser")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "tag.db")
conn = setup_database(db_path)
