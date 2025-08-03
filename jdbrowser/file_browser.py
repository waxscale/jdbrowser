import os
from PySide6 import QtWidgets, QtGui, QtCore

from .dialogs import InputTagDialog, EditTagDialog
from .file_item import FileItem
from .database import create_tag, rebuild_state_tags, setup_database
from .constants import *


class FileBrowser(QtWidgets.QMainWindow):
    """Minimal browser for navigating tags using the new UUID path schema."""

    def __init__(self, start_parent_id=None):
        super().__init__()
        self.current_parent_id = start_parent_id
        self.nav_stack = []
        self.cols = 10
        self.items = []
        self.show_prefix = False

        settings = QtCore.QSettings("xAI", "jdbrowser")
        self.show_hidden = settings.value("show_hidden", False, type=bool)

        xdg_data_home = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        db_dir = os.path.join(xdg_data_home, "jdbrowser")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "tag.db")
        self.conn = setup_database(self.db_path)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self._setup_ui()
        self.load_items()

        if settings.contains("pos") and settings.contains("size"):
            self.move(settings.value("pos", type=QtCore.QPoint))
            self.resize(settings.value("size", type=QtCore.QSize))

    # ------------------------------------------------------------------ UI --
    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        self.grid = QtWidgets.QGridLayout(central)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setSpacing(10)

        toolbar = QtWidgets.QToolBar()
        self.addToolBar(toolbar)
        add_action = toolbar.addAction("New Tag")
        add_action.triggered.connect(self._add_tag)
        up_action = toolbar.addAction("Up")
        up_action.triggered.connect(self.go_up)

    # --------------------------------------------------------------- helpers --
    def _warn(self, title: str, message: str) -> None:
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(message)
        box.exec()

    # ------------------------------------------------------------- navigation --
    def update_title(self):
        if self.current_parent_id is None:
            self.setWindowTitle("File Browser - /")
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT label FROM state_tags WHERE tag_id = ?", (self.current_parent_id,)
            )
            row = cursor.fetchone()
            name = row[0] if row else ""
            self.setWindowTitle(f"File Browser - {name}")

    def go_up(self):
        if self.nav_stack:
            self.current_parent_id = self.nav_stack.pop()
            self.load_items()

    def enter_directory(self, tag_id):
        self.nav_stack.append(self.current_parent_id)
        self.current_parent_id = tag_id
        self.load_items()

    # --------------------------------------------------------------- loading --
    def clear_items(self):
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.items.clear()

    def load_items(self):
        self.clear_items()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT t.tag_id, t.jd_id, t.label, i.icon
            FROM state_tags t
            LEFT JOIN state_tag_icons i ON t.tag_id = i.tag_id
            WHERE ((? IS NULL AND t.parent_tag_id IS NULL) OR t.parent_tag_id = ?)
            ORDER BY t.jd_id
            """,
            (self.current_parent_id, self.current_parent_id),
        )
        rows = cursor.fetchall()
        for idx, (tag_id, jd_id, label, icon) in enumerate(rows):
            item = FileItem(tag_id, label, jd_id, icon, self, idx)
            r, c = divmod(idx, self.cols)
            self.grid.addWidget(item, r, c)
            self.items.append(item)
        self.update_title()

    # --------------------------------------------------------------- actions --
    def _add_tag(self):
        dialog = InputTagDialog(parent=self)
        if dialog.exec():
            jd_id, label = dialog.get_values()
            if jd_id is None:
                self._warn("Invalid Input", "jd_id must be an integer.")
                return
            if create_tag(self.conn, self.current_parent_id, jd_id, label) is None:
                self._warn("Invalid Input", "jd_id already exists in this parent.")
            rebuild_state_tags(self.conn)
            self.load_items()

    def _edit_tag(self, tag_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label, jd_id FROM state_tags WHERE tag_id = ?", (tag_id,)
        )
        row = cursor.fetchone()
        if not row:
            return
        current_label, current_jd_id = row
        cursor.execute(
            "SELECT icon FROM state_tag_icons WHERE tag_id = ?", (tag_id,)
        )
        icon_row = cursor.fetchone()
        icon_data = icon_row[0] if icon_row else None

        dialog = EditTagDialog(current_label, icon_data, current_jd_id, self)
        if not dialog.exec():
            return
        new_label = dialog.get_label()
        new_jd_id = dialog.get_jd_id()
        new_icon = dialog.get_icon_data()
        if new_jd_id is None:
            self._warn("Invalid Input", "jd_id must be an integer.")
            return
        cursor.execute(
            "SELECT tag_id FROM state_tags WHERE ((? IS NULL AND parent_tag_id IS NULL) OR parent_tag_id = ?) AND jd_id = ? AND tag_id != ?",
            (self.current_parent_id, self.current_parent_id, new_jd_id, tag_id),
        )
        if cursor.fetchone():
            self._warn("Duplicate jd_id", "jd_id already exists in this parent.")
            return

        cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_path')")
        event_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO event_set_tag_path (event_id, tag_id, parent_tag_id, jd_id) VALUES (?, ?, ?, ?)",
            (event_id, tag_id, self.current_parent_id, new_jd_id),
        )
        cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_label')")
        event_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO event_set_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
            (event_id, tag_id, new_label),
        )
        cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_icon')")
        event_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO event_set_tag_icon (event_id, tag_id, icon) VALUES (?, ?, ?)",
            (event_id, tag_id, new_icon),
        )
        rebuild_state_tags(self.conn)
        self.load_items()

    def swap_tags(self, src_tag_id, dst_tag_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT parent_tag_id, jd_id FROM state_tags WHERE tag_id = ?",
            (src_tag_id,),
        )
        src = cursor.fetchone()
        cursor.execute(
            "SELECT parent_tag_id, jd_id FROM state_tags WHERE tag_id = ?",
            (dst_tag_id,),
        )
        dst = cursor.fetchone()
        if not src or not dst:
            return
        src_parent, src_jd = src
        dst_parent, dst_jd = dst
        if src_parent != dst_parent:
            return
        cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_path')")
        event_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO event_set_tag_path (event_id, tag_id, parent_tag_id, jd_id) VALUES (?, ?, ?, ?)",
            (event_id, src_tag_id, src_parent, dst_jd),
        )
        cursor.execute("INSERT INTO events (event_type) VALUES ('set_tag_path')")
        event_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO event_set_tag_path (event_id, tag_id, parent_tag_id, jd_id) VALUES (?, ?, ?, ?)",
            (event_id, dst_tag_id, dst_parent, src_jd),
        )
        rebuild_state_tags(self.conn)
        self.load_items()

