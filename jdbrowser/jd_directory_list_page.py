import os
import re
from PySide6 import QtWidgets, QtGui, QtCore
import jdbrowser
from .directory_item import DirectoryItem
from .recent_directory_item import RecentDirectoryItem
from .database import (
    setup_database,
    rebuild_state_jd_directories,
    create_jd_directory,
    add_directory_tag,
    remove_directory_tag,
    rebuild_state_directory_tags,
)
from .dialogs import EditTagDialog, SimpleEditTagDialog, RemoveDirectoryTagDialog
from .constants import *
from .config import read_config
from .search_line_edit import SearchLineEdit
from .tag_search_overlay import TagSearchOverlay

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

        xdg_data_home = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        db_dir = os.path.join(xdg_data_home, "jdbrowser")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "tag.db")
        self.conn = setup_database(self.db_path)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label FROM state_jd_ext_tags WHERE tag_id = ?",
            (self.parent_uuid,),
        )
        row = cursor.fetchone()
        self.ext_label = row[0] if row else ""

        cursor.execute(
            "SELECT label FROM state_jd_id_tags WHERE tag_id = ?",
            (self.grandparent_uuid,),
        )
        row = cursor.fetchone()
        self.id_label = row[0] if row else ""

        cursor.execute(
            "SELECT label FROM state_jd_area_tags WHERE tag_id = ?",
            (self.great_grandparent_uuid,),
        )
        row = cursor.fetchone()
        self.area_label = row[0] if row else ""

        self.items = []
        self.main_count = 0
        self.selected_index = None
        self.show_prefix = False
        settings = QtCore.QSettings("xAI", "jdbrowser")
        self.show_prefix = settings.value("show_prefix", False, type=bool)
        self.repository_path = read_config()

        self.in_search_mode = False
        self.prev_selected_index = None
        self.search_matches = []
        self.current_match_idx = -1
        self.shortcuts = []
        self.search_shortcut_instances = []
        self.tag_search_overlay = None
        self.remove_tag_overlay = None
        self.recent_items = []
        self.recent_wrapper = None
        self.recent_frame = None
        self.untagged_items = []
        self.untagged_wrapper = None
        self.untagged_frame = None

        self._setup_ui()
        self._setup_shortcuts()

    def _format_order(self, order):
        formatted = f"{order:016d}"
        return "_".join(formatted[i:i+4] for i in range(0, 16, 4))

    def _fallback_icon(self, order):
        folder = self._format_order(order)
        path = os.path.join(self.repository_path, folder)
        for name in (
            "[0-META 0000-00-00 00.00.00].png",
            "[0-META 0000-00-00 00.00.00] #auto.png",
        ):
            img_path = os.path.join(path, name)
            if os.path.isfile(img_path):
                with open(img_path, "rb") as f:
                    return f.read()
        return None

    def ascend_level(self):
        from .jd_ext_page import JdExtPage

        new_page = JdExtPage(
            parent_uuid=self.grandparent_uuid,
            jd_area=self.current_jd_area,
            jd_id=self.current_jd_id,
            grandparent_uuid=self.great_grandparent_uuid,
        )
        # Ensure the item we descended from becomes selected when returning
        target_tag_id = self.parent_uuid
        found = False
        for s, sec in enumerate(new_page.sections):
            for i, item in enumerate(sec):
                if item.tag_id == target_tag_id:
                    new_page.sec_idx = s
                    new_page.idx_in_sec = i
                    found = True
                    break
            if found:
                break
        new_page.updateSelection()
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)

    def ascend_to_id(self):
        from .jd_id_page import JdIdPage

        new_page = JdIdPage(
            parent_uuid=self.great_grandparent_uuid, jd_area=self.current_jd_area
        )
        target_tag_id = self.grandparent_uuid
        found = False
        for s, sec in enumerate(new_page.sections):
            for i, item in enumerate(sec):
                if item.tag_id == target_tag_id:
                    new_page.sec_idx = s
                    new_page.idx_in_sec = i
                    found = True
                    break
            if found:
                break
        new_page.updateSelection()
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)

    def ascend_to_area(self):
        from .jd_area_page import JdAreaPage

        new_page = JdAreaPage()
        target_tag_id = self.great_grandparent_uuid
        found = False
        for s, sec in enumerate(new_page.sections):
            for i, item in enumerate(sec):
                if item.tag_id == target_tag_id:
                    new_page.sec_idx = s
                    new_page.idx_in_sec = i
                    found = True
                    break
            if found:
                break
        new_page.updateSelection()
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)

    def descend_level(self):
        if self.selected_index is None or not self.items:
            return
        if not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        from .jd_directory_page import JdDirectoryPage

        new_page = JdDirectoryPage(
            current_item.directory_id,
            parent_uuid=self.parent_uuid,
            jd_area=self.current_jd_area,
            jd_id=self.current_jd_id,
            jd_ext=self.current_jd_ext,
            grandparent_uuid=self.grandparent_uuid,
            great_grandparent_uuid=self.great_grandparent_uuid,
            ext_label=self.ext_label,
        )
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)

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

    def _setup_search_shortcuts(self):
        """Set up search mode shortcuts for the current search_input widget."""
        for shortcut in self.search_shortcut_instances:
            shortcut.deleteLater()
        self.search_shortcut_instances = []
        search_shortcuts = [
            (QtCore.Qt.Key_Escape, self.exit_search_mode_revert, None),
            (
                QtCore.Qt.Key_BracketLeft,
                self.exit_search_mode_revert,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
            (QtCore.Qt.Key_Return, self.exit_search_mode_select, None),
            (
                QtCore.Qt.Key_G,
                self.next_match,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
            (
                QtCore.Qt.Key_G,
                self.prev_match,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier
                | QtCore.Qt.KeyboardModifier.ShiftModifier,
            ),
            (
                QtCore.Qt.Key_N,
                self.next_match,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
            (
                QtCore.Qt.Key_P,
                self.prev_match,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
        ]
        for mapping in search_shortcuts:
            key, func, arg = mapping[0], mapping[1], mapping[2]
            modifiers = (
                mapping[3]
                if len(mapping) > 3
                else QtCore.Qt.KeyboardModifier.NoModifier
            )
            s = QtGui.QShortcut(QtGui.QKeySequence(key | modifiers), self.search_input)
            s.setEnabled(False)
            if arg is None:
                s.activated.connect(func)
            else:
                s.activated.connect(lambda f=func, a=arg: f(a))
            self.search_shortcut_instances.append(s)

    def _strip_prefix(self, text: str) -> str:
        return re.sub(r"^\[[^\]]*\]\s*", "", text).strip()

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
                sep.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                )
                layout.addWidget(sep)
            if handler:
                btn = QtWidgets.QPushButton(text)
                btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                btn.setFlat(True)
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: transparent; border: none; color: {BREADCRUMB_ACTIVE_COLOR}; font-weight: bold; }}"
                    "QPushButton:hover { text-decoration: underline; }"
                )
                btn.clicked.connect(handler)
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                )
                layout.addWidget(btn)
            else:
                label = QtWidgets.QLabel(text)
                label.setStyleSheet(
                    f"color: {BREADCRUMB_INACTIVE_COLOR}; font-weight: bold;"
                )
                label.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                )
                layout.addWidget(label)
        layout.addStretch(1)
        return bar

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        crumb_area = self._strip_prefix(self.area_label)
        crumb_id = self._strip_prefix(self.id_label)
        crumb_ext = self._strip_prefix(self.ext_label)
        self.breadcrumb_bar = self._build_breadcrumb(
            [
                ("Home", self.ascend_to_area),
                (crumb_area, self.ascend_to_id),
                (crumb_id, self.ascend_level),
                (crumb_ext, None),
            ]
        )
        layout.addWidget(self.breadcrumb_bar)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #000000;")
        layout.addWidget(self.scroll_area)

        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("background-color: #000000;")
        self.scroll_area.setWidget(self.container)
        self.vlayout = QtWidgets.QVBoxLayout(self.container)
        self.vlayout.setContentsMargins(5, 5, 5, 5)
        self.vlayout.setSpacing(5)

        self._load_directories()
        if self.items:
            self.set_selection(0)

        # Search input box
        self.search_input = SearchLineEdit(self)
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(30)
        self.search_input.hide()
        self.search_input.textChanged.connect(self.perform_search)
        self._setup_search_shortcuts()

        style = f'''
        * {{ font-family: 'FiraCode Nerd Font'; }}
        QWidget {{ background-color: #000000; }}
        QMainWindow {{ background-color: #000000; }}
        QScrollArea {{ border: none; background-color: #000000; }}
        QScrollBar:vertical {{
            width: 8px;
            background: #000000;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER_COLOR};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        QScrollBar:horizontal {{
            height: 8px;
            background: #000000;
        }}
        QScrollBar::handle:horizontal {{
            background: {BORDER_COLOR};
            min-width: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
        '''
        self.setStyleSheet(style)
        self.search_input.move(self.width() - 310, self.height() - 40)

    def _clear_items(self):
        while self.vlayout.count():
            item = self.vlayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.items = []
        self.main_count = 0
        self.recent_items = []
        self.recent_wrapper = None
        self.recent_frame = None
        self.untagged_items = []
        self.untagged_wrapper = None
        self.untagged_frame = None

    def _load_directories(self):
        self._clear_items()
        self.selected_index = None
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT d.directory_id, d.label, d.[order], i.icon
            FROM state_jd_directories d
            JOIN state_jd_directory_tags dt ON d.directory_id = dt.directory_id
            LEFT JOIN state_jd_directory_icons i ON d.directory_id = i.directory_id
            WHERE dt.tag_id = ?
            ORDER BY d.[order]
            """,
            (self.parent_uuid,),
        )
        rows = cursor.fetchall()
        for row in rows:
            directory_id, label, order, icon_data = row
            icon_data = icon_data or self._fallback_icon(order)
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
                (directory_id,),
            )
            tag_rows = cursor.fetchall()
            tags = [tuple(t) for t in tag_rows]
            index = len(self.items)
            item = DirectoryItem(directory_id, label, order, icon_data, self, index, tags)
            item.updateLabel(self.show_prefix)
            self.vlayout.addWidget(item)
            self.items.append(item)
        self.main_count = len(self.items)
        self._load_recent_directories()
        self._load_untagged_directories()
        self.vlayout.addStretch(1)

    def _load_recent_directories(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT e.directory_id, d.label, d.[order], i.icon
            FROM event_create_jd_directory e
            JOIN state_jd_directories d ON e.directory_id = d.directory_id
            LEFT JOIN state_jd_directory_icons i ON d.directory_id = i.directory_id
            LEFT JOIN state_jd_directory_tags t ON d.directory_id = t.directory_id
                AND t.tag_id = ?
            WHERE t.tag_id IS NULL
            ORDER BY e.event_id DESC
            LIMIT 5
            """,
            (self.parent_uuid,),
        )
        rows = cursor.fetchall()
        if not rows:
            return
        self.recent_items = []
        self.recent_wrapper = QtWidgets.QWidget()
        outer_layout = QtWidgets.QVBoxLayout(self.recent_wrapper)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(5)

        title = QtWidgets.QLabel("Recent Directories")
        title_font = title.font()
        title_font.setPointSize(int(title_font.pointSize() * 0.9))
        title.setFont(title_font)
        title.setStyleSheet(f"color: {BREADCRUMB_INACTIVE_COLOR};")
        outer_layout.addWidget(title, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.recent_frame = QtWidgets.QFrame()
        self.recent_frame.setStyleSheet("background-color: #000; border: none;")
        self.recent_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        v_layout = QtWidgets.QVBoxLayout(self.recent_frame)
        v_layout.setContentsMargins(10, 10, 10, 10)
        v_layout.setSpacing(5)
        for directory_id, label, order, icon_data in rows:
            icon_data = icon_data or self._fallback_icon(order)
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
                (directory_id,),
            )
            tag_rows = cursor.fetchall()
            tags = [tuple(t) for t in tag_rows]
            index = len(self.items)
            item = RecentDirectoryItem(
                directory_id, label, order, icon_data, self, index, tags
            )
            item.updateLabel(self.show_prefix)
            v_layout.addWidget(item)
            self.recent_items.append(item)
            self.items.append(item)
        outer_layout.addWidget(self.recent_frame)
        self.vlayout.addWidget(
            self.recent_wrapper, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        QtCore.QTimer.singleShot(0, self._update_recent_width)

    def _load_untagged_directories(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT e.directory_id, d.label, d.[order], i.icon
            FROM event_create_jd_directory e
            JOIN state_jd_directories d ON e.directory_id = d.directory_id
            LEFT JOIN state_jd_directory_icons i ON d.directory_id = i.directory_id
            LEFT JOIN state_jd_directory_tags t ON d.directory_id = t.directory_id
            WHERE t.directory_id IS NULL
            ORDER BY e.event_id DESC
            LIMIT 5
            """
        )
        rows = cursor.fetchall()
        if not rows:
            return
        self.untagged_items = []
        self.untagged_wrapper = QtWidgets.QWidget()
        outer_layout = QtWidgets.QVBoxLayout(self.untagged_wrapper)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(5)

        title = QtWidgets.QLabel("Untagged Directories")
        title_font = title.font()
        title_font.setPointSize(int(title_font.pointSize() * 0.9))
        title.setFont(title_font)
        title.setStyleSheet(f"color: {BREADCRUMB_INACTIVE_COLOR};")
        outer_layout.addWidget(title, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.untagged_frame = QtWidgets.QFrame()
        self.untagged_frame.setStyleSheet("background-color: #000; border: none;")
        self.untagged_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        v_layout = QtWidgets.QVBoxLayout(self.untagged_frame)
        v_layout.setContentsMargins(10, 10, 10, 10)
        v_layout.setSpacing(5)
        for directory_id, label, order, icon_data in rows:
            icon_data = icon_data or self._fallback_icon(order)
            index = len(self.items)
            item = RecentDirectoryItem(
                directory_id, label, order, icon_data, self, index, []
            )
            item.updateLabel(self.show_prefix)
            v_layout.addWidget(item)
            self.untagged_items.append(item)
            self.items.append(item)
        outer_layout.addWidget(self.untagged_frame)
        self.vlayout.addWidget(
            self.untagged_wrapper, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        QtCore.QTimer.singleShot(0, self._update_recent_width)

    def _update_recent_width(self):
        width = int(self.width() * 0.6)
        if self.recent_wrapper:
            self.recent_wrapper.setFixedWidth(width)
        if self.untagged_wrapper:
            self.untagged_wrapper.setFixedWidth(width)

    def set_selection(self, index):
        if not (0 <= index < len(self.items)):
            return
        self.selected_index = index
        for i, item in enumerate(self.items):
            item.isSelected = i == index
            item.updateStyle()
        if 0 <= self.selected_index < len(self.items):
            self.scroll_area.ensureWidgetVisible(self.items[self.selected_index])

    def move_selection(self, direction):
        if self.in_search_mode or not self.items:
            return
        if self.selected_index is None:
            index = 0 if direction > 0 else len(self.items) - 1
        else:
            index = self.selected_index + direction
            index = max(0, min(index, len(self.items) - 1))
        self.set_selection(index)

    def move_selection_multiple(self, count):
        if self.in_search_mode or not self.items:
            return
        for _ in range(abs(count)):
            self.move_selection(1 if count > 0 else -1)

    def move_to_start(self):
        if self.in_search_mode or not self.items:
            return
        self.set_selection(0)

    def move_to_end(self):
        if self.in_search_mode or not self.items:
            return
        self.set_selection(len(self.items) - 1)

    def move_to_section_start(self):
        if self.in_search_mode or not self.items:
            return
        bounds = []
        if self.main_count:
            bounds.append((0, self.main_count - 1))
        if self.recent_items:
            start = self.main_count
            bounds.append((start, start + len(self.recent_items) - 1))
        if self.untagged_items:
            start = self.main_count + len(self.recent_items)
            bounds.append((start, start + len(self.untagged_items) - 1))
        if not bounds:
            return
        if self.selected_index is None:
            self.set_selection(bounds[0][0])
            return
        idx = self.selected_index
        current = 0
        for i, (s, e) in enumerate(bounds):
            if s <= idx <= e:
                current = i
                start = s
                break
        if idx != start:
            self.set_selection(start)
        elif current > 0:
            self.set_selection(bounds[current - 1][0])

    def move_to_section_end(self):
        if self.in_search_mode or not self.items:
            return
        bounds = []
        if self.main_count:
            bounds.append((0, self.main_count - 1))
        if self.recent_items:
            start = self.main_count
            bounds.append((start, start + len(self.recent_items) - 1))
        if self.untagged_items:
            start = self.main_count + len(self.recent_items)
            bounds.append((start, start + len(self.untagged_items) - 1))
        if not bounds:
            return
        if self.selected_index is None:
            self.set_selection(bounds[-1][1])
            return
        idx = self.selected_index
        current = 0
        for i, (s, e) in enumerate(bounds):
            if s <= idx <= e:
                current = i
                end = e
                break
        if idx != end:
            self.set_selection(end)
        elif current + 1 < len(bounds):
            self.set_selection(bounds[current + 1][1])

    def _add_directory(self):
        if self.selected_index is not None and self.selected_index >= self.main_count:
            item = self.items[self.selected_index]
            directory_id = item.directory_id
            add_directory_tag(self.conn, directory_id, self.parent_uuid)
            rebuild_state_directory_tags(self.conn)
            rebuild_state_jd_directories(self.conn)
            self._load_directories()
            for i, it in enumerate(self.items):
                if it.directory_id == directory_id:
                    self.set_selection(i)
                    break
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX([order]) FROM state_jd_directories")
        result = cursor.fetchone()
        max_order = result[0] if result and result[0] is not None else 0
        new_order = max_order + 1

        os.makedirs(self.repository_path, exist_ok=True)
        folder_name = "_".join(f"{new_order:016d}"[i : i + 4] for i in range(0, 16, 4))
        folder_path = os.path.join(self.repository_path, folder_name)

        if os.path.exists(folder_path):
            pattern = re.compile(r"^\d{4}_\d{4}_\d{4}_\d{4}$")
            highest = max(
                (
                    int(name.replace("_", ""))
                    for name in os.listdir(self.repository_path)
                    if os.path.isdir(os.path.join(self.repository_path, name))
                    and pattern.fullmatch(name)
                ),
                default=0,
            )
            new_order = highest + 1
            folder_name = "_".join(
                f"{new_order:016d}"[i : i + 4] for i in range(0, 16, 4)
            )
            folder_path = os.path.join(self.repository_path, folder_name)

        os.makedirs(folder_path, exist_ok=True)

        directory_id = create_jd_directory(self.conn, new_order, "")
        if directory_id:
            add_directory_tag(self.conn, directory_id, self.parent_uuid)
        rebuild_state_jd_directories(self.conn)
        rebuild_state_directory_tags(self.conn)
        self._load_directories()
        if self.items:
            self.set_selection(len(self.items) - 1)

    def _rename_tag_label(self):
        """Edit the current directory's label with a simple dialog."""
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        directory_id = current_item.directory_id
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label FROM state_jd_directories WHERE directory_id = ?",
            (directory_id,),
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
                (event_id, directory_id, new_label),
            )
            self.conn.commit()
            rebuild_state_jd_directories(self.conn)
            self._load_directories()
            for i, item in enumerate(self.items):
                if item.directory_id == directory_id:
                    self.set_selection(i)
                    break

    def _edit_tag_label_with_icon(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        directory_id = current_item.directory_id
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT [order], label FROM state_jd_directories WHERE directory_id = ?",
            (directory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return
        order, current_label = row
        cursor.execute(
            "SELECT icon FROM state_jd_directory_icons WHERE directory_id = ?",
            (directory_id,),
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
                    (new_order, directory_id),
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
                        (event_id, directory_id, new_order),
                    )
                if new_label != current_label:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_label')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_directory_label (event_id, directory_id, new_label) VALUES (?, ?, ?)",
                        (event_id, directory_id, new_label),
                    )
                if new_icon_data:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_directory_icon')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_directory_icon (event_id, directory_id, icon) VALUES (?, ?, ?)",
                        (event_id, directory_id, new_icon_data),
                    )
                self.conn.commit()
                rebuild_state_jd_directories(self.conn)
                self._load_directories()
                for i, item in enumerate(self.items):
                    if item.directory_id == directory_id:
                        self.set_selection(i)
                        break
                break
            else:
                break

    def _remove_tag_from_directory(self):
        """Remove the current jd_ext tag from the selected directory."""
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        # Recent and untagged directories are guaranteed not to have the current
        # tag, so pressing "d" on them should be a no-op.
        if current_item in self.recent_items or current_item in self.untagged_items:
            return
        directory_id = current_item.directory_id
        dialog = RemoveDirectoryTagDialog(current_item.label_text, self.ext_label, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            remove_directory_tag(self.conn, directory_id, self.parent_uuid)
            rebuild_state_directory_tags(self.conn)
            idx = self.selected_index
            self._load_directories()
            if self.items:
                if idx is None or idx >= len(self.items):
                    idx = len(self.items) - 1
                self.set_selection(idx)
            else:
                self.selected_index = None

    def enter_search_mode(self):
        if not self.in_search_mode:
            if not self.items:
                return
            self.in_search_mode = True
            self.prev_selected_index = self.selected_index
            self.search_matches = []
            self.current_match_idx = -1
            self.search_input.clear()
            self.search_input.show()
            self.search_input.setFocus()
            for s in self.shortcuts:
                key_str = s.key().toString()
                if key_str and not any(
                    key_str.lower() == seq.lower() for seq in self.quit_sequences
                ):
                    s.setEnabled(False)
            for s in self.search_shortcut_instances:
                s.setEnabled(True)
            self.perform_search("")

    def exit_search_mode_revert(self):
        if self.in_search_mode:
            self.in_search_mode = False
            self.search_input.hide()
            self.search_matches = []
            self.current_match_idx = -1
            for s in self.shortcuts:
                s.setEnabled(True)
            for s in self.search_shortcut_instances:
                s.setEnabled(False)
            for item in self.items:
                item.isDimmed = False
                item.updateStyle()
            if self.prev_selected_index is not None:
                self.set_selection(self.prev_selected_index)

    def exit_search_mode_select(self):
        if self.in_search_mode:
            self.in_search_mode = False
            self.search_input.hide()
            if self.search_matches and self.current_match_idx >= 0:
                self.set_selection(self.search_matches[self.current_match_idx])
            elif self.prev_selected_index is not None:
                self.set_selection(self.prev_selected_index)
            self.search_matches = []
            self.current_match_idx = -1
            for s in self.shortcuts:
                s.setEnabled(True)
            for s in self.search_shortcut_instances:
                s.setEnabled(False)
            for item in self.items:
                item.isDimmed = False
                item.updateStyle()

    def perform_search(self, query):
        if not self.items:
            return
        query = query.lower()
        self.search_matches = []
        for i, item in enumerate(self.items):
            tags_text = " ".join(t_label for _, t_label, _, _ in item.tags)
            combined = f"{item.label_text} {tags_text}".lower()
            if query and query in combined:
                self.search_matches.append(i)
                item.isDimmed = False
            else:
                item.isDimmed = bool(query)
            item.updateStyle()
        if self.search_matches:
            self.current_match_idx = 0
            self.set_selection(self.search_matches[0])
        else:
            self.current_match_idx = -1

    def next_match(self):
        if self.in_search_mode and self.current_match_idx < len(self.search_matches) - 1:
            self.current_match_idx += 1
            self.set_selection(self.search_matches[self.current_match_idx])

    def prev_match(self):
        if self.in_search_mode and self.current_match_idx > 0:
            self.current_match_idx -= 1
            self.set_selection(self.search_matches[self.current_match_idx])

    def toggle_label_prefix(self):
        self.show_prefix = not self.show_prefix
        for item in self.items:
            item.updateLabel(self.show_prefix)
        if self.selected_index is not None:
            self.set_selection(self.selected_index)
        settings = QtCore.QSettings("xAI", "jdbrowser")
        settings.setValue("show_prefix", self.show_prefix)

    def mousePressEvent(self, event):
        if self.in_search_mode:
            self.exit_search_mode_select()
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        self.search_input.move(self.width() - 310, self.height() - 40)
        if self.tag_search_overlay and self.tag_search_overlay.isVisible():
            self.tag_search_overlay.reposition()
        self._update_recent_width()
        super().resizeEvent(event)

    def open_tag_search(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        if not self.tag_search_overlay:
            self.tag_search_overlay = TagSearchOverlay(self, self.conn)
            self.tag_search_overlay.tagSelected.connect(self.apply_tag_to_selected_directory)
            self.tag_search_overlay.closed.connect(self._tag_search_closed)
        for s in self.shortcuts:
            s.setEnabled(False)
        self.tag_search_overlay.open()

    def _tag_search_closed(self):
        for s in self.shortcuts:
            s.setEnabled(True)

    def apply_tag_to_selected_directory(self, tag_uuid):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM state_jd_ext_tags WHERE tag_id = ?",
            (tag_uuid,),
        )
        if not cursor.fetchone():
            return
        cursor.execute(
            "SELECT 1 FROM state_jd_directory_tags WHERE directory_id = ? AND tag_id = ?",
            (current_item.directory_id, tag_uuid),
        )
        if cursor.fetchone():
            return
        add_directory_tag(self.conn, current_item.directory_id, tag_uuid)
        rebuild_state_directory_tags(self.conn)
        idx = self.selected_index
        self._load_directories()
        if idx is not None and idx < len(self.items):
            self.set_selection(idx)

    def open_remove_tag_search(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT dt.tag_id, et.label
            FROM state_jd_directory_tags dt
            JOIN state_jd_ext_tags et ON dt.tag_id = et.tag_id
            WHERE dt.directory_id = ?
            """,
            (current_item.directory_id,),
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
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            return
        current_item = self.items[self.selected_index]
        remove_directory_tag(self.conn, current_item.directory_id, tag_uuid)
        rebuild_state_directory_tags(self.conn)
        idx = self.selected_index
        self._load_directories()
        if idx is not None and idx < len(self.items):
            self.set_selection(idx)

    def _setup_shortcuts(self):
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        mappings = [
            (QtCore.Qt.Key_Return, self.descend_level, None),
            (QtCore.Qt.Key_Enter, self.descend_level, None),
            (QtCore.Qt.Key_J, self.move_selection, 1),
            (QtCore.Qt.Key_Down, self.move_selection, 1),
            (QtCore.Qt.Key_K, self.move_selection, -1),
            (QtCore.Qt.Key_Up, self.move_selection, -1),
            (QtCore.Qt.Key_U, self.move_selection_multiple, -11, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_D, self.move_selection_multiple, 11, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_PageUp, self.move_selection_multiple, -11),
            (QtCore.Qt.Key_PageDown, self.move_selection_multiple, 11),
            (QtCore.Qt.Key_BracketLeft, self.move_to_section_start, None),
            (QtCore.Qt.Key_BracketRight, self.move_to_section_end, None),
            (QtCore.Qt.Key_G, self.move_to_start, None),
            (QtCore.Qt.Key_G, self.move_to_end, None, QtCore.Qt.KeyboardModifier.ShiftModifier),
            (QtCore.Qt.Key_Home, self.move_to_start, None),
            (QtCore.Qt.Key_End, self.move_to_end, None),
            (QtCore.Qt.Key_H, lambda: None, None),
            (QtCore.Qt.Key_Left, lambda: None, None),
            (QtCore.Qt.Key_L, lambda: None, None),
            (QtCore.Qt.Key_Right, lambda: None, None),
            (QtCore.Qt.Key_Backspace, self.ascend_level, None),
            (
                QtCore.Qt.Key_Up,
                self.ascend_level,
                None,
                QtCore.Qt.KeyboardModifier.AltModifier,
            ),
            (QtCore.Qt.Key_AsciiTilde, self.ascend_to_area, None),
            (QtCore.Qt.Key_A, self._add_directory, None),
            (QtCore.Qt.Key_C, self._edit_tag_label_with_icon, None),
            (QtCore.Qt.Key_R, self._rename_tag_label, None),
            (QtCore.Qt.Key_F2, self._rename_tag_label, None),
            (QtCore.Qt.Key_D, self._remove_tag_from_directory, None),
            (QtCore.Qt.Key_E, self.open_tag_search, None),
            (QtCore.Qt.Key_X, self.open_remove_tag_search, None),
            (QtCore.Qt.Key_Tab, self.toggle_label_prefix, None),
            (QtCore.Qt.Key_Slash, self.enter_search_mode, None),
            (
                QtCore.Qt.Key_F,
                self.enter_search_mode,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
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
        self.quit_sequences = ["Q", "Ctrl+Q", "Ctrl+W", "Alt+F4"]
        for seq in self.quit_sequences:
            s = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
            s.activated.connect(jdbrowser.main_window.close)
            self.shortcuts.append(s)
