import os
from PySide6 import QtWidgets, QtGui, QtCore
import jdbrowser
from .directory_item import DirectoryItem
from .database import (
    setup_database,
    rebuild_state_jd_directory_tags,
    create_jd_directory_tag,
)
from .constants import *

class JdDirectoryListPage(QtWidgets.QWidget):
    def __init__(
        self,
        parent_uuid,
        jd_area,
        jd_id,
        jd_ext,
        grandparent_uuid,
        great_grandparent_uuid,
    ):
        super().__init__()
        self.parent_uuid = parent_uuid
        self.current_jd_area = jd_area
        self.current_jd_id = jd_id
        self.current_jd_ext = jd_ext
        self.grandparent_uuid = grandparent_uuid
        self.great_grandparent_uuid = great_grandparent_uuid
        if jdbrowser.main_window:
            jdbrowser.main_window.setWindowTitle(
                f"File Browser - [{jd_area:02d}.{jd_id:02d}+{jd_ext:04d}]"
            )
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: black;")

        xdg_data_home = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        db_dir = os.path.join(xdg_data_home, "jdbrowser")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "tag.db")
        self.conn = setup_database(self.db_path)

        self.items = []
        self.selected_index = None

        self._setup_ui()
        self._setup_shortcuts()

    def ascend_level(self):
        from .jd_ext_page import JdExtPage

        new_page = JdExtPage(
            parent_uuid=self.grandparent_uuid,
            jd_area=self.current_jd_area,
            jd_id=self.current_jd_id,
            grandparent_uuid=self.great_grandparent_uuid,
        )
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: transparent;")
        layout.addWidget(self.scroll_area)

        self.container = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.container)
        self.vlayout = QtWidgets.QVBoxLayout(self.container)
        self.vlayout.setContentsMargins(5, 5, 5, 5)
        self.vlayout.setSpacing(5)

        self._load_directories()

    def _clear_items(self):
        while self.vlayout.count():
            item = self.vlayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _load_directories(self):
        self._clear_items()
        self.items = []
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT t.tag_id, t.label, t.[order], i.icon
            FROM state_jd_directory_tags t
            LEFT JOIN state_jd_directory_tag_icons i ON t.tag_id = i.tag_id
            WHERE t.parent_uuid IS ?
            ORDER BY t.[order]
            """,
            (self.parent_uuid,)
        )
        rows = cursor.fetchall()
        for idx, row in enumerate(rows):
            tag_id, label, order, icon_data = row
            item = DirectoryItem(tag_id, label, icon_data, self, idx)
            self.vlayout.addWidget(item)
            self.items.append(item)
        self.vlayout.addStretch(1)

    def set_selection(self, index):
        if not (0 <= index < len(self.items)):
            return
        self.selected_index = index
        for i, item in enumerate(self.items):
            item.isSelected = i == index
            item.updateStyle()

    def _add_directory(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_directory_tags WHERE parent_uuid IS ?",
            (self.parent_uuid,),
        )
        result = cursor.fetchone()
        max_order = result[0] if result and result[0] is not None else 0
        new_order = max_order + 1
        create_jd_directory_tag(self.conn, self.parent_uuid, new_order, "")
        rebuild_state_jd_directory_tags(self.conn)
        self._load_directories()

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)

    def _setup_shortcuts(self):
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        mappings = [
            (QtCore.Qt.Key_Backspace, self.ascend_level, None),
            (
                QtCore.Qt.Key_Up,
                self.ascend_level,
                None,
                QtCore.Qt.KeyboardModifier.AltModifier,
            ),
            (QtCore.Qt.Key_A, self._add_directory, None),
        ]
        self.shortcuts = []
        for mapping in mappings:
            key, func, arg = mapping[0], mapping[1], mapping[2]
            modifiers = (
                mapping[3]
                if len(mapping) > 3
                else QtCore.Qt.KeyboardModifier.NoModifier
            )
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key | modifiers), self)
            if arg is None:
                shortcut.activated.connect(func)
            else:
                shortcut.activated.connect(lambda f=func, a=arg: f(a))
            self.shortcuts.append(shortcut)
        quit_keys = ["Q", "Ctrl+Q", "Ctrl+W", "Alt+F4"]
        for seq in quit_keys:
            s = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
            s.activated.connect(jdbrowser.main_window.close)
            self.shortcuts.append(s)
