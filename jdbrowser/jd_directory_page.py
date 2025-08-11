import os
import re
from PySide6 import QtWidgets, QtCore, QtGui
import jdbrowser
from .constants import *
from .database import (
    setup_database,
    add_directory_tag,
    remove_directory_tag,
    rebuild_state_directory_tags,
    rebuild_state_jd_directories,
)
from .dialogs import EditTagDialog, SimpleEditTagDialog
from .directory_item import DirectoryItem
from .tag_search_overlay import TagSearchOverlay

class JdDirectoryPage(QtWidgets.QWidget):
    def __init__(
        self,
        directory_id,
        parent_uuid=None,
        jd_area=None,
        jd_id=None,
        jd_ext=None,
        grandparent_uuid=None,
        great_grandparent_uuid=None,
        ext_label=None,
    ):
        super().__init__()
        self.directory_id = directory_id
        self.parent_uuid = parent_uuid
        self.current_jd_area = jd_area
        self.current_jd_id = jd_id
        self.current_jd_ext = jd_ext
        self.grandparent_uuid = grandparent_uuid
        self.great_grandparent_uuid = great_grandparent_uuid
        self.ext_label = ext_label
        if jdbrowser.main_window:
            jdbrowser.main_window.setWindowTitle(f"File Browser - [{directory_id}]")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        xdg_data_home = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        db_dir = os.path.join(xdg_data_home, "jdbrowser")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "tag.db")
        self.conn = setup_database(self.db_path)

        settings = QtCore.QSettings("xAI", "jdbrowser")
        self.show_prefix = settings.value("show_prefix", False, type=bool)

        self.tag_search_overlay = None
        self.remove_tag_overlay = None

        self._setup_ui()
        self._setup_shortcuts()
        self.set_selection(0)

        self.setStyleSheet(
            """
            QWidget { background-color: #000000; }
            """
        )

    # DirectoryItem expects a set_selection method on its page
    def set_selection(self, index):
        self.item.isSelected = index == 0
        self.item.updateStyle()

    def _format_order(self, order):
        formatted = f"{order:016d}"
        return "_".join(formatted[i:i+4] for i in range(0, 16, 4))

    def _build_breadcrumb(self, crumbs):
        bar = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(0)
        bar.setStyleSheet(f"background-color: {BREADCRUMB_BG_COLOR};")
        for i, (text, handler) in enumerate(crumbs):
            if i:
                sep = QtWidgets.QLabel(" / ")
                sep.setStyleSheet(f"color: {BREADCRUMB_ACTIVE_COLOR};")
                sep.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                layout.addWidget(sep)
            label = QtWidgets.QLabel(text)
            label.setStyleSheet(
                f"color: {BREADCRUMB_INACTIVE_COLOR}; font-weight: bold;"
            )
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            layout.addWidget(label)
        layout.addStretch(1)
        return bar

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label, [order] FROM state_jd_directories WHERE directory_id = ?",
            (self.directory_id,),
        )
        row = cursor.fetchone()
        label = row[0] if row else ""
        order = row[1] if row else 0

        crumb = self._format_order(order)
        if self.parent_uuid is not None and self.ext_label:
            parent_crumb = self._strip_prefix(self.ext_label)
            self.breadcrumb_bar = self._build_breadcrumb(
                [(parent_crumb, self.ascend_level), (crumb, None)]
            )
        else:
            self.breadcrumb_bar = self._build_breadcrumb([(crumb, None)])
        layout.addWidget(self.breadcrumb_bar)

        cursor.execute(
            "SELECT icon FROM state_jd_directory_icons WHERE directory_id = ?",
            (self.directory_id,),
        )
        row = cursor.fetchone()
        icon_data = row[0] if row else None

        cursor.execute(
            """
            SELECT dt.tag_id,
                   COALESCE(ext.label, id.label, area.label) AS label,
                   COALESCE(ext.[order], id.[order], area.[order]) AS [order],
                   COALESCE(ext.parent_uuid, id.parent_uuid) AS parent_uuid
            FROM state_jd_directory_tags dt
            LEFT JOIN state_jd_ext_tags ext ON dt.tag_id = ext.tag_id
            LEFT JOIN state_jd_id_tags id ON dt.tag_id = id.tag_id
            LEFT JOIN state_jd_area_tags area ON dt.tag_id = area.tag_id
            WHERE dt.directory_id = ?
            ORDER BY [order]
            """,
            (self.directory_id,),
        )
        tag_rows = cursor.fetchall()
        tags = [tuple(t) for t in tag_rows]

        self.item = DirectoryItem(
            self.directory_id, label, order, icon_data, self, 0, tags
        )
        self.item.updateLabel(self.show_prefix)
        self.item.isSelected = False
        self.item.updateStyle()
        self.item.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(self.item)
        layout.addStretch(1)

    def _strip_prefix(self, text: str) -> str:
        return re.sub(r"^\[[^\]]*\]\s*", "", text).strip()

    def _setup_shortcuts(self):
        self.shortcuts = []
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        mappings = [
            (QtCore.Qt.Key_Backspace, self.ascend_level, None),
            (
                QtCore.Qt.Key_Up,
                self.ascend_level,
                None,
                QtCore.Qt.KeyboardModifier.AltModifier,
            ),
            (QtCore.Qt.Key_C, self._edit_tag_label_with_icon, None),
            (QtCore.Qt.Key_R, self._rename_tag_label, None),
            (QtCore.Qt.Key_F2, self._rename_tag_label, None),
            (QtCore.Qt.Key_E, self.open_tag_search, None),
            (QtCore.Qt.Key_X, self.open_remove_tag_search, None),
        ]
        for key, func, arg, *mod in mappings:
            seq = QtGui.QKeySequence(mod[0] | key) if mod else QtGui.QKeySequence(key)
            s = QtGui.QShortcut(seq, self)
            if arg is None:
                s.activated.connect(func)
            else:
                s.activated.connect(lambda f=func, a=arg: f(a))
            self.shortcuts.append(s)
        self.quit_sequences = ["Q", "Ctrl+Q", "Ctrl+W", "Alt+F4"]
        for seq in self.quit_sequences:
            s = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
            s.activated.connect(jdbrowser.main_window.close)
            self.shortcuts.append(s)

    def _warn(self, title: str, message: str) -> None:
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStyleSheet(
            f"""
            QMessageBox {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
            }}
            QLabel {{
                background-color: transparent;
                color: {TEXT_COLOR};
            }}
            QLabel#qt_msgbox_label,
            QLabel#qt_msgboxex_icon_label {{
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {HIGHLIGHT_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {HOVER_COLOR};
            }}
            """
        )
        box.exec()

    def _refresh_item(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label, [order] FROM state_jd_directories WHERE directory_id = ?",
            (self.directory_id,),
        )
        row = cursor.fetchone()
        label = row[0] if row else ""
        order = row[1] if row else 0
        cursor.execute(
            "SELECT icon FROM state_jd_directory_icons WHERE directory_id = ?",
            (self.directory_id,),
        )
        row = cursor.fetchone()
        icon_data = row[0] if row else None
        cursor.execute(
            """
            SELECT dt.tag_id,
                   COALESCE(ext.label, id.label, area.label) AS label,
                   COALESCE(ext.[order], id.[order], area.[order]) AS [order],
                   COALESCE(ext.parent_uuid, id.parent_uuid) AS parent_uuid
            FROM state_jd_directory_tags dt
            LEFT JOIN state_jd_ext_tags ext ON dt.tag_id = ext.tag_id
            LEFT JOIN state_jd_id_tags id ON dt.tag_id = id.tag_id
            LEFT JOIN state_jd_area_tags area ON dt.tag_id = area.tag_id
            WHERE dt.directory_id = ?
            ORDER BY [order]
            """,
            (self.directory_id,),
        )
        tag_rows = cursor.fetchall()
        tags = [tuple(t) for t in tag_rows]
        self.item.label_text = label
        self.item.order = order
        self.item.tags = tags
        self.item._build_tag_pills()
        self.item.updateLabel(self.show_prefix)
        if icon_data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                rounded = QtGui.QPixmap(240, 150)
                rounded.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 5, 5)
                painter.setClipPath(path)
                scaled = pixmap.scaled(
                    240,
                    150,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                self.item.icon.setPixmap(rounded)
                self.item.icon.setFixedSize(240, 150)
                self.item.icon.setStyleSheet("background-color: transparent;")
        else:
            self.item.icon.setPixmap(QtGui.QPixmap())
            self.item.icon.setFixedSize(240, 150)
            self.item.icon.setStyleSheet(
                f"background-color: {SLATE_COLOR}; border-radius: 5px;"
            )
        self.item.updateStyle()

    def _rename_tag_label(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label FROM state_jd_directories WHERE directory_id = ?",
            (self.directory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return
        current_label = row[0]
        dialog = SimpleEditTagDialog(current_label, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_label = dialog.get_label()
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_label')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_directory_label (event_id, directory_id, new_label) VALUES (?, ?, ?)",
                (event_id, self.directory_id, new_label),
            )
            self.conn.commit()
            rebuild_state_jd_directories(self.conn)
            self._refresh_item()

    def _edit_tag_label_with_icon(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT [order], label FROM state_jd_directories WHERE directory_id = ?",
            (self.directory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return
        order, current_label = row
        cursor.execute(
            "SELECT icon FROM state_jd_directory_icons WHERE directory_id = ?",
            (self.directory_id,),
        )
        icon_row = cursor.fetchone()
        icon_data = icon_row[0] if icon_row else None
        while True:
            dialog = EditTagDialog(current_label, icon_data, 3, order, self)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                new_order = dialog.get_order()
                new_label = dialog.get_label()
                new_icon_data = dialog.get_icon_data()
                cursor.execute(
                    "SELECT directory_id FROM state_jd_directories WHERE [order] = ? AND directory_id != ?",
                    (new_order, self.directory_id),
                )
                if cursor.fetchone():
                    self._warn(
                        "Constraint Violation",
                        f"Order {new_order} is already in use.",
                    )
                    current_label, icon_data, order = new_label, new_icon_data, new_order
                    continue
                if new_order != order:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_order')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_directory_order (event_id, directory_id, [order]) VALUES (?, ?, ?)",
                        (event_id, self.directory_id, new_order),
                    )
                if new_label != current_label:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_label')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_directory_label (event_id, directory_id, new_label) VALUES (?, ?, ?)",
                        (event_id, self.directory_id, new_label),
                    )
                if new_icon_data:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_icon')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_directory_icon (event_id, directory_id, icon) VALUES (?, ?, ?)",
                        (event_id, self.directory_id, new_icon_data),
                    )
                self.conn.commit()
                rebuild_state_jd_directories(self.conn)
                self._refresh_item()
                break
            else:
                break

    def open_tag_search(self):
        if not self.tag_search_overlay:
            self.tag_search_overlay = TagSearchOverlay(self, self.conn)
            self.tag_search_overlay.tagSelected.connect(self.apply_tag_to_directory)
            self.tag_search_overlay.closed.connect(self._tag_search_closed)
        for s in self.shortcuts:
            s.setEnabled(False)
        self.tag_search_overlay.open()

    def _tag_search_closed(self):
        for s in self.shortcuts:
            s.setEnabled(True)

    def apply_tag_to_directory(self, tag_uuid):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM state_jd_ext_tags WHERE tag_id = ?",
            (tag_uuid,),
        )
        if not cursor.fetchone():
            return
        cursor.execute(
            "SELECT 1 FROM state_jd_directory_tags WHERE directory_id = ? AND tag_id = ?",
            (self.directory_id, tag_uuid),
        )
        if cursor.fetchone():
            return
        add_directory_tag(self.conn, self.directory_id, tag_uuid)
        rebuild_state_directory_tags(self.conn)
        self._refresh_item()

    def open_remove_tag_search(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT dt.tag_id, et.label
            FROM state_jd_directory_tags dt
            JOIN state_jd_ext_tags et ON dt.tag_id = et.tag_id
            WHERE dt.directory_id = ?
            """,
            (self.directory_id,),
        )
        rows = [(r[0], r[1]) for r in cursor.fetchall() if r[1]]
        if not rows:
            return
        if not self.remove_tag_overlay:
            self.remove_tag_overlay = TagSearchOverlay(self, self.conn)
            self.remove_tag_overlay.tagSelected.connect(
                self._remove_selected_tag_from_directory
            )
            self.remove_tag_overlay.closed.connect(self._remove_tag_search_closed)
        for s in self.shortcuts:
            s.setEnabled(False)
        self.remove_tag_overlay.open(label_rows=rows)

    def _remove_tag_search_closed(self):
        for s in self.shortcuts:
            s.setEnabled(True)

    def _remove_selected_tag_from_directory(self, tag_uuid):
        remove_directory_tag(self.conn, self.directory_id, tag_uuid)
        rebuild_state_directory_tags(self.conn)
        self._refresh_item()

    def ascend_level(self):
        if self.parent_uuid is None:
            return
        from .jd_directory_list_page import JdDirectoryListPage

        new_page = JdDirectoryListPage(
            parent_uuid=self.parent_uuid,
            jd_area=self.current_jd_area,
            jd_id=self.current_jd_id,
            jd_ext=self.current_jd_ext,
            grandparent_uuid=self.grandparent_uuid,
            great_grandparent_uuid=self.great_grandparent_uuid,
        )
        target_id = self.directory_id
        for i, item in enumerate(new_page.items):
            if item.directory_id == target_id:
                new_page.set_selection(i)
                break
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)
