import os
from collections import defaultdict
from PySide6 import QtWidgets, QtGui, QtCore
import shiboken6
import jdbrowser
from .dialogs import EditTagDialog, SimpleEditTagDialog, InputTagDialog, DeleteTagDialog
from .dialogs.header_dialog import HeaderDialog
from .file_item import FileItem
from .header_item import HeaderItem
from .search_line_edit import SearchLineEdit
from .database import (
    create_jd_id_tag,
    rebuild_state_jd_id_tags,
    create_jd_id_header,
    update_jd_id_header,
    delete_jd_id_header,
    rebuild_state_jd_id_headers,
    delete_jd_id_tag,
)
from .constants import *

class JdIdPage(QtWidgets.QWidget):
    def __init__(self, parent_uuid=None, jd_area=None):
        super().__init__()
        self.parent_uuid = parent_uuid
        self.current_jd_area = jd_area
        self.current_jd_id = None
        if jdbrowser.main_window:
            jdbrowser.main_window.setWindowTitle(f"File Browser - [{jd_area:02d}]")
        self.cols = 10
        self.sections = []
        self.section_paths = []  # Store (jd_area, jd_id, jd_ext) for each section
        self.section_filenames = []  # Store .2do filenames for sorting
        self.header_orders = []
        self.sec_idx = 0
        self.idx_in_sec = 0
        self.desired_col = 0
        self.nav_stack = []
        self.in_search_mode = False
        self.prev_sec_idx = 0
        self.prev_idx_in_sec = 0
        self.search_matches = []
        self.current_match_idx = -1
        self.shortcuts = []
        self.search_shortcut_instances = []
        self.show_prefix = False
        # Load show_prefix and show_hidden state from QSettings
        settings = QtCore.QSettings("xAI", "jdbrowser")
        self.show_prefix = settings.value("show_prefix", False, type=bool)
        self.show_hidden = settings.value("show_hidden", False, type=bool)

        # Shared SQLite database connection
        self.conn = jdbrowser.conn

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT label FROM state_jd_area_tags WHERE tag_id = ?",
            (self.parent_uuid,),
        )
        row = cursor.fetchone()
        self.area_label = row[0] if row else ""

        app = QtWidgets.QApplication.instance()
        if app:
            app.setStyleSheet(
                app.styleSheet()
                + f"""
                QMessageBox {{
                    background-color: {BACKGROUND_COLOR};
                    color: {TEXT_COLOR};
                    border: 1px solid {BORDER_COLOR};
                }}
                QMessageBox QLabel {{
                    color: {TEXT_COLOR};
                }}
                QMessageBox QPushButton {{
                    background-color: {BUTTON_COLOR};
                    color: black;
                    border: none;
                    padding: 5px;
                    border-radius: 5px;
                }}
                QMessageBox QPushButton:hover {{
                    background-color: {HIGHLIGHT_COLOR};
                }}
                QMessageBox QPushButton:pressed {{
                    background-color: {HOVER_COLOR};
                }}
                """
            )

        self._setup_ui()
        self._setup_shortcuts()
        self.updateSelection()

    def set_selection(self, section_idx, item_idx):
        """Update the current selection to the specified section and item index."""
        if 0 <= section_idx < len(self.sections) and 0 <= item_idx < len(self.sections[section_idx]):
            self.sec_idx = section_idx
            self.idx_in_sec = item_idx
            self.updateSelection()

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

    def _is_hidden_item(self, name):
        """Check if an item should be hidden based on naming patterns."""
        if self.show_hidden:
            return False
        hidden_patterns = [
            '[00].png', '[00] #auto.png',
            '[.00].png', '[.00] #auto.png',
            '[+0000].png', '[+0000] #auto.png',
            '[0-META 0000-00-00 00.00.00].png', '[0-META 0000-00-00 00.00.00] #auto.png'
        ]
        return name.startswith('.') or name in hidden_patterns

    def _set_thumbnail(self):
        """Open a file dialog to select a .png image and set it as the thumbnail for the current tag."""
        if not self.sections or self.sec_idx >= len(self.sections) or self.idx_in_sec >= len(self.sections[self.sec_idx]):
            return
        current_item = self.sections[self.sec_idx][self.idx_in_sec]
        if not current_item.tag_id:  # Skip placeholder items
            return
        tag_id = current_item.tag_id
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png)")
        settings = QtCore.QSettings("xAI", "jdbrowser")
        last_dir = settings.value("last_thumbnail_dir", "", type=str)
        if last_dir:
            file_dialog.setDirectory(last_dir)
        file_dialog.setStyleSheet(f'''
            QFileDialog {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
            }}
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #e0c58f;
            }}
            QToolButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QToolButton:hover {{
                background-color: #e0c58f;
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
            QTreeView, QListView {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
            }}
            QTreeView::item:selected, QListView::item:selected {{
                background-color: {HIGHLIGHT_COLOR};
                color: {TEXT_COLOR};
            }}
            QTreeView::item:hover, QListView::item:hover {{
                background-color: {HOVER_COLOR};
            }}
            QComboBox {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                selection-background-color: {HIGHLIGHT_COLOR};
            }}
        ''')
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            settings.setValue("last_thumbnail_dir", os.path.dirname(file_path))
            pixmap = QtGui.QPixmap(file_path)
            if not pixmap.isNull():
                with open(file_path, 'rb') as f:
                    icon_data = f.read()
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_icon')")
                event_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO event_set_jd_id_tag_icon (event_id, tag_id, icon) VALUES (?, ?, ?)",
                    (event_id, tag_id, icon_data),
                )
                self.conn.commit()
                rebuild_state_jd_id_tags(self.conn)
                self._rebuild_ui()

    def _create_header(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_id_headers WHERE parent_uuid IS ?",
            (self.parent_uuid,),
        )
        max_order = cursor.fetchone()[0]
        default_order = max_order + 1 if max_order is not None else 0
        dialog = HeaderDialog(default_order, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted and not dialog.delete_pressed:
            order = dialog.get_order()
            label = dialog.get_label()
            if order is None:
                self._warn("Invalid Input", "Order must be an integer.")
                return
            header_id = create_jd_id_header(
                self.conn, self.parent_uuid, order, label
            )
            if header_id:
                rebuild_state_jd_id_headers(self.conn)
                self._rebuild_ui()
            else:
                self._warn(
                    "Constraint Violation", "Header order conflicts or invalid."
                )

    def _append_tag_to_section(self):
        """Append a tag to the current section with jd parts incremented appropriately."""
        if not self.sections or self.sec_idx >= len(self.sections):
            return
        cursor = self.conn.cursor()
        _, base, _ = self.section_paths[self.sec_idx]
        label = "NewTag"
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_id_tags WHERE parent_uuid IS ? AND [order] >= ? AND [order] < ?",
            (self.parent_uuid, base, base + 10),
        )
        max_order = cursor.fetchone()[0]
        new_order = max_order + 1 if max_order is not None else base
        new_tag_id = create_jd_id_tag(self.conn, self.parent_uuid, new_order, label)
        if new_tag_id:
            rebuild_state_jd_id_tags(self.conn)
            self._rebuild_ui(new_tag_id=new_tag_id)

    def _input_tag_dialog(self):
        """Open a dialog to input jd_area, jd_id, jd_ext, and label for a new tag."""
        if not self.sections or self.sec_idx >= len(self.sections):
            return
        # If the current selection is a placeholder, reuse the same behaviour as
        # the 'c' shortcut or right-click: pre-fill the dialog with the
        # placeholder's prefix values.
        if self.idx_in_sec < len(self.sections[self.sec_idx]):
            current_item = self.sections[self.sec_idx][self.idx_in_sec]
            if not current_item.tag_id:  # placeholder item
                self._edit_tag_label_with_icon()
                return
        cursor = self.conn.cursor()
        _, base, _ = self.section_paths[self.sec_idx]
        default_label = "NewTag"
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_id_tags WHERE parent_uuid IS ? AND [order] >= ? AND [order] < ?",
            (self.parent_uuid, base, base + 10),
        )
        max_order = cursor.fetchone()[0]
        default_order = max_order + 1 if max_order is not None else base
        dialog = InputTagDialog(default_order, default_label, parent=self)
        while True:
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                order, label = dialog.get_values()
                if order is None:
                    self._warn("Invalid Input", "Order must be an integer.")
                    continue
                new_tag_id = create_jd_id_tag(self.conn, self.parent_uuid, order, label)
                if new_tag_id:
                    rebuild_state_jd_id_tags(self.conn)
                    self._rebuild_ui(new_tag_id=new_tag_id)
                    break
                else:
                    self._warn(
                        "Constraint Violation",
                        f"Order {order} is already in use.",
                    )
            else:
                break

    def ascend_level(self):
        from .jd_area_page import JdAreaPage
        new_page = JdAreaPage()
        # Highlight the area we were viewing in the parent page
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

    def _edit_tag_label_with_icon(self):
        """Edit the current tag's label and thumbnail with a dialog showing the icon."""
        if not self.sections or self.sec_idx >= len(self.sections) or self.idx_in_sec >= len(self.sections[self.sec_idx]):
            return
        current_item = self.sections[self.sec_idx][self.idx_in_sec]
        if not current_item.tag_id:
            default_label = "NewTag"
            dialog = InputTagDialog(
                current_item.jd_id,
                default_label,
                parent=self,
            )
            while True:
                if dialog.exec() == QtWidgets.QDialog.Accepted:
                    order, label = dialog.get_values()
                    if order is None:
                        self._warn("Invalid Input", "Order must be an integer.")
                        continue
                    new_tag_id = create_jd_id_tag(self.conn, self.parent_uuid, order, label)
                    if new_tag_id:
                        rebuild_state_jd_id_tags(self.conn)
                        self._rebuild_ui(new_tag_id=new_tag_id)
                        break
                    else:
                        self._warn(
                            "Constraint Violation",
                            f"Order {order} is already in use.",
                        )
                else:
                    break
            return
        tag_id = current_item.tag_id
        cursor = self.conn.cursor()
        cursor.execute("SELECT [order], label FROM state_jd_id_tags WHERE tag_id = ?", (tag_id,))
        jd_id, current_label = cursor.fetchone()
        cursor.execute("SELECT icon FROM state_jd_id_tag_icons WHERE tag_id = ?", (tag_id,))
        icon_data = cursor.fetchone()
        icon_data = icon_data[0] if icon_data else None
        while True:
            dialog = EditTagDialog(current_label, icon_data, 1, jd_id, self)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                new_jd_id = dialog.get_order()
                new_label = dialog.get_label()
                new_icon_data = dialog.get_icon_data()
                cursor.execute(
                    "SELECT tag_id FROM state_jd_id_tags WHERE parent_uuid IS ? AND [order] = ? AND tag_id != ?",
                    (self.parent_uuid, new_jd_id, tag_id),
                )
                if cursor.fetchone():
                    self._warn(
                        "Constraint Violation",
                        f"Order {new_jd_id} is already in use.",
                    )
                    current_label, icon_data, jd_id = new_label, new_icon_data, new_jd_id
                    continue
                if new_jd_id != jd_id:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_order')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_id_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                        (event_id, tag_id, self.parent_uuid, new_jd_id),
                    )
                if new_label != current_label:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_label')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_id_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
                        (event_id, tag_id, new_label),
                    )
                if new_icon_data:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_icon')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_id_tag_icon (event_id, tag_id, icon) VALUES (?, ?, ?)",
                        (event_id, tag_id, new_icon_data),
                    )
                self.conn.commit()
                rebuild_state_jd_id_tags(self.conn)
                self._rebuild_ui()
                break
            else:
                break

    def _rename_tag_label(self):
        """Edit the current tag's label with a simple dialog."""
        if not self.sections or self.sec_idx >= len(self.sections) or self.idx_in_sec >= len(self.sections[self.sec_idx]):
            return
        current_item = self.sections[self.sec_idx][self.idx_in_sec]
        if not current_item.tag_id:  # Skip placeholder items
            return
        tag_id = current_item.tag_id
        cursor = self.conn.cursor()
        cursor.execute("SELECT label FROM state_jd_id_tags WHERE tag_id = ?", (tag_id,))
        current_label = cursor.fetchone()[0]
        dialog = SimpleEditTagDialog(current_label, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_label = dialog.get_label()
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_label')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_id_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
                (event_id, tag_id, new_label),
            )
            self.conn.commit()
            rebuild_state_jd_id_tags(self.conn)
            self._rebuild_ui()

    def _delete_tag(self):
        """Delete the current tag with a confirmation dialog."""
        if not self.sections or self.sec_idx >= len(self.sections) or self.idx_in_sec >= len(self.sections[self.sec_idx]):
            return
        current_item = self.sections[self.sec_idx][self.idx_in_sec]
        if not current_item.tag_id:  # Skip placeholder items
            return
        tag_id = current_item.tag_id
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT [order], label FROM state_jd_id_tags WHERE tag_id = ?",
            (tag_id,),
        )
        order, tag_name = cursor.fetchone()
        prefix = f"[{self.current_jd_area:02d}.{order:02d}]"
        display_name = f"{prefix} {tag_name}" if tag_name else prefix
        dialog = DeleteTagDialog(display_name, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            delete_jd_id_tag(self.conn, tag_id)
            rebuild_state_jd_id_tags(self.conn)
            # Preserve current indices; selection will land on placeholder
            current_item.tag_id = None
            self._rebuild_ui()

    def handle_item_drop(self, source_tag_id, target_item):
        """Handle drag-and-drop operations between items."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT [order] FROM state_jd_id_tags WHERE tag_id = ?",
            (source_tag_id,),
        )
        row = cursor.fetchone()
        if not row:
            return
        s_id = row[0]
        if target_item.tag_id is None:
            new_id = target_item.jd_id
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_id_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, source_tag_id, self.parent_uuid, new_id),
            )
        else:
            target_tag_id = target_item.tag_id
            if target_tag_id == source_tag_id:
                return
            cursor.execute(
                "SELECT [order] FROM state_jd_id_tags WHERE tag_id = ?",
                (target_tag_id,),
            )
            t_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_id_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, target_tag_id, self.parent_uuid, -1),
            )
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_id_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, source_tag_id, self.parent_uuid, t_id),
            )
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_id_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_id_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, target_tag_id, self.parent_uuid, s_id),
            )
        self.conn.commit()
        rebuild_state_jd_id_tags(self.conn)
        self._rebuild_ui(new_tag_id=source_tag_id)

    def _edit_header(self, header_item):
        dialog = HeaderDialog(header_item.jd_id, header_item.label, True, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            if dialog.delete_pressed:
                delete_jd_id_header(self.conn, header_item.header_id)
            else:
                order = dialog.get_order()
                label = dialog.get_label()
                if order is None:
                    self._warn("Invalid Input", "Order must be an integer.")
                    return
                if not update_jd_id_header(
                    self.conn, header_item.header_id, self.parent_uuid, order, label
                ):
                    self._warn("Invalid Input", "Header order conflicts or invalid.")
                    return
            rebuild_state_jd_id_headers(self.conn)
            self._rebuild_ui()

    def _setup_search_shortcuts(self):
        """Set up search mode shortcuts for the current search_input widget."""
        for shortcut in self.search_shortcut_instances:
            shortcut.deleteLater()
        self.search_shortcut_instances = []
        search_shortcuts = [
            (QtCore.Qt.Key_Escape, self.exit_search_mode_revert, None),
            (QtCore.Qt.Key_BracketLeft, self.exit_search_mode_revert, None, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_Return, self.exit_search_mode_select, None),
            (QtCore.Qt.Key_G, self.next_match, None, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_G, self.prev_match, None, QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier),
            (QtCore.Qt.Key_N, self.next_match, None, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_P, self.prev_match, None, QtCore.Qt.KeyboardModifier.ControlModifier),
        ]
        for mapping in search_shortcuts:
            key, func, arg = mapping[0], mapping[1], mapping[2]
            modifiers = mapping[3] if len(mapping) > 3 else QtCore.Qt.KeyboardModifier.NoModifier
            s = QtGui.QShortcut(QtGui.QKeySequence(key | modifiers), self.search_input)
            s.setEnabled(False)
            if arg is None:
                s.activated.connect(func)
            else:
                s.activated.connect(lambda f=func, a=arg: f(a))
            self.search_shortcut_instances.append(s)

    def _build_breadcrumb(self, crumbs):
        bar = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(0)
        bar.setStyleSheet(
            f"background-color: {BREADCRUMB_BG_COLOR}; color: black;"
        )
        for i, (text, handler) in enumerate(crumbs):
            if i:
                sep = QtWidgets.QLabel(" / ")
                sep.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                )
                layout.addWidget(sep)
            if handler:
                btn = QtWidgets.QPushButton(text)
                btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                btn.setFlat(True)
                btn.setStyleSheet(
                    "QPushButton { background-color: transparent; border: none; color: black; }"
                    "QPushButton:hover { text-decoration: underline; }"
                )
                btn.clicked.connect(handler)
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                )
                layout.addWidget(btn)
            else:
                label = QtWidgets.QLabel(text)
                label.setSizePolicy(
                    QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                )
                layout.addWidget(label)
        layout.addStretch(1)
        return bar

    def _setup_ui(self):
        if not hasattr(self, "scroll_area"):
            self.scroll_area = QtWidgets.QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.scroll_area.setStyleSheet("border: none; background-color: #000000;")
            scroll_area = self.scroll_area
            QtCore.QTimer.singleShot(
                100,
                lambda sa=scroll_area: shiboken6.isValid(sa)
                and sa.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded),
            )
            QtCore.QTimer.singleShot(
                100,
                lambda sa=scroll_area: shiboken6.isValid(sa)
                and sa.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded),
            )
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            crumb_text = f"{self.current_jd_area:02d} {self.area_label}".strip()
            self.breadcrumb_bar = self._build_breadcrumb([(crumb_text, self.ascend_level)])
            layout.addWidget(self.breadcrumb_bar)
            layout.addWidget(self.scroll_area)

            # Search input box
            self.search_input = SearchLineEdit(self)
            self.search_input.setFixedWidth(300)
            self.search_input.setFixedHeight(30)
            self.search_input.hide()
            self.search_input.textChanged.connect(self.perform_search)
            self._setup_search_shortcuts()
        else:
            old = self.scroll_area.takeWidget()
            if old:
                old.deleteLater()

        container = QtWidgets.QWidget()
        container.setStyleSheet("background-color: #000000;")
        mainLayout = QtWidgets.QVBoxLayout(container)
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(5, 15, 5, 5)

        self.sections = []
        self.section_paths = []
        self.section_filenames = []
        current_section = None
        section_index = 0
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT header_id, [order], label FROM state_jd_id_headers WHERE parent_uuid IS ? ORDER BY [order]",
            (self.parent_uuid,),
        )
        headers = cursor.fetchall()
        self.header_orders = sorted({0, *(order for _, order, _ in headers)})
        cursor.execute(
            "SELECT tag_id, [order], label FROM state_jd_id_tags WHERE parent_uuid IS ? ORDER BY [order]",
            (self.parent_uuid,),
        )
        tags = cursor.fetchall()
        cursor.execute("SELECT tag_id, icon FROM state_jd_id_tag_icons")
        icons = {row[0]: row[1] for row in cursor.fetchall()}

        def construct_prefix(order):
            return f"[{self.current_jd_area:02d}.{order:02d}]"

        items = []
        for header_id, order, label in headers:
            prefix = construct_prefix(order)
            items.append(("header", prefix, label, header_id, order))
        for tag_id, order, label in tags:
            prefix = construct_prefix(order)
            items.append(("tag", prefix, label, tag_id, order))

        # Sort numerically by order to ensure consistent ordering
        items.sort(
            key=lambda x: (
                x[4],
                0 if x[0] == "header" else 1,
                (x[2] or "").lower(),
            )
        )

        # Build sections and placeholders
        def placeholder_item(val, sec_idx, item_idx):
            pa, pi, pe = self.current_jd_area, val, None
            item = FileItem(None, None, pa, pi, pe, None, self, sec_idx, item_idx)
            item.updateLabel(self.show_prefix)
            return item

        section_index = 0

        headers_by_base = defaultdict(list)
        tags_by_base = defaultdict(list)
        for kind, prefix, label, obj_id, order in items:
            value = order
            base = (value // 10) * 10 if value is not None else 0
            if kind == "header":
                headers_by_base[base].append((obj_id, order, label, prefix))
            else:
                tags_by_base[base].append((obj_id, order, label))

        for base in range(0, 100, 10):
            for obj_id, order, label, prefix in headers_by_base.get(base, []):
                display = f"{prefix} {label}" if prefix else (label or "")
                header_item = HeaderItem(obj_id, self.current_jd_area, order, None, label, self, section_index, display)
                header_item.setMinimumWidth(self.scroll_area.viewport().width() - 10)
                mainLayout.addWidget(header_item)
                mainLayout.addSpacing(10)
            section = [
                placeholder_item(val, section_index, i)
                for i, val in enumerate(range(base, base + 10))
            ]
            for obj_id, order, label in tags_by_base.get(base, []):
                index = order - base
                icon_data = icons.get(obj_id)
                item = FileItem(
                    obj_id,
                    label,
                    self.current_jd_area,
                    order,
                    None,
                    icon_data,
                    self,
                    section_index,
                    index,
                )
                item.updateLabel(self.show_prefix)
                section[index] = item
            sectionWidget = QtWidgets.QWidget()
            sectionLayout = QtWidgets.QVBoxLayout(sectionWidget)
            sectionLayout.setSpacing(5)
            sectionLayout.setContentsMargins(0, 0, 0, 0)
            sectionLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            rowLayout = None
            for i, item in enumerate(section):
                if i % self.cols == 0:
                    if rowLayout:
                        sectionLayout.addLayout(rowLayout)
                    rowLayout = QtWidgets.QHBoxLayout()
                    rowLayout.setSpacing(2)
                    rowLayout.setContentsMargins(0, 0, 0, 0)
                    rowLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                rowLayout.addWidget(item)
            if rowLayout:
                sectionLayout.addLayout(rowLayout)
            sectionWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            mainLayout.addWidget(sectionWidget)
            mainLayout.setAlignment(sectionWidget, QtCore.Qt.AlignmentFlag.AlignLeft)
            self.sections.append(section)
            base_path = (self.current_jd_area, base, None)
            self.section_paths.append(base_path)
            self.section_filenames.append(None)
            section_index += 1

        mainLayout.addStretch()
        container.setStyleSheet(f'background-color: #000000;')
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.scroll_area.setWidget(container)

        self.search_input.move(self.width() - 310, self.height() - 40)

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

    def _rebuild_ui(self, new_tag_id=None):
        """Rebuild the UI to reflect the current state, selecting new_tag_id or current_tag_id."""
        current_tag_id = None
        if self.sections and 0 <= self.sec_idx < len(self.sections) and 0 <= self.idx_in_sec < len(self.sections[self.sec_idx]):
            current_tag_id = self.sections[self.sec_idx][self.idx_in_sec].tag_id
        old_widget = self.scroll_area.takeWidget()
        if old_widget:
            old_widget.deleteLater()
        self.sections = []
        self.section_paths = []
        self.section_filenames = []
        self._setup_ui()
        if new_tag_id or current_tag_id:
            target_tag_id = new_tag_id or current_tag_id
            found = False
            for s, sec in enumerate(self.sections):
                for i, item in enumerate(sec):
                    if item.tag_id == target_tag_id:
                        self.sec_idx = s
                        self.idx_in_sec = i
                        found = True
                        break
                if found:
                    break
        # Ensure indices remain within bounds
        if not self.sections:
            self.sec_idx = 0
            self.idx_in_sec = 0
        else:
            if self.sec_idx >= len(self.sections):
                self.sec_idx = len(self.sections) - 1
            if self.idx_in_sec >= len(self.sections[self.sec_idx]):
                self.idx_in_sec = len(self.sections[self.sec_idx]) - 1
        self.updateSelection()

    def toggle_hidden(self):
        """Toggle visibility of hidden items and save state."""
        self.show_hidden = not self.show_hidden
        settings = QtCore.QSettings("xAI", "jdbrowser")
        settings.setValue("show_hidden", self.show_hidden)
        self._rebuild_ui()

    def toggle_label_prefix(self):
        self.show_prefix = not self.show_prefix
        for sec in self.sections:
            for item in sec:
                item.updateLabel(self.show_prefix)
        self.updateSelection()
        settings = QtCore.QSettings("xAI", "jdbrowser")
        settings.setValue("show_prefix", self.show_prefix)

    def _setup_shortcuts(self):
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.normal_shortcuts = [
            (QtCore.Qt.Key_Right, self.moveHoriz, 1),
            (QtCore.Qt.Key_L, self.moveHoriz, 1),
            (QtCore.Qt.Key_Left, self.moveHoriz, -1),
            (QtCore.Qt.Key_H, self.moveHoriz, -1),
            (QtCore.Qt.Key_Down, self.moveVert, 1),
            (QtCore.Qt.Key_J, self.moveVert, 1),
            (QtCore.Qt.Key_Up, self.moveVert, -1),
            (QtCore.Qt.Key_K, self.moveVert, -1),
            (QtCore.Qt.Key_BracketLeft, self.moveToSectionStart, None),
            (QtCore.Qt.Key_BracketRight, self.moveToSectionEnd, None),
            (QtCore.Qt.Key_G, self.moveToAbsoluteFirst, None),
            (QtCore.Qt.Key_G, self.moveToAbsoluteLast, None, QtCore.Qt.KeyboardModifier.ShiftModifier),
            (QtCore.Qt.Key_U, self.moveVertMultiple, -3, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_D, self.moveVertMultiple, 3, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_PageUp, self.moveVertMultiple, -3),
            (QtCore.Qt.Key_PageDown, self.moveVertMultiple, 3),
            (QtCore.Qt.Key_Z, self.centerSelectedItem, None),
            (QtCore.Qt.Key_Y, self.copySelectedName, None),
            (QtCore.Qt.Key_Slash, self.enter_search_mode, None),
            (QtCore.Qt.Key_F, self.enter_search_mode, None, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_Tab, self.toggle_label_prefix, None),
            (QtCore.Qt.Key_0, self.firstInRow, None),
            (QtCore.Qt.Key_Dollar, self.lastInRow, None),
            (QtCore.Qt.Key_Home, self.firstInRow, None),
            (QtCore.Qt.Key_End, self.lastInRow, None),
            (QtCore.Qt.Key_H, self.toggle_hidden, None, QtCore.Qt.KeyboardModifier.ControlModifier),
            (QtCore.Qt.Key_S, self._create_header, None),
            (QtCore.Qt.Key_A, self._append_tag_to_section, None),
            (QtCore.Qt.Key_I, self._input_tag_dialog, None),
              (QtCore.Qt.Key_C, self._edit_tag_label_with_icon, None),
              (QtCore.Qt.Key_R, self._rename_tag_label, None),
              (QtCore.Qt.Key_F2, self._rename_tag_label, None),
              (QtCore.Qt.Key_D, self._delete_tag, None),
              (QtCore.Qt.Key_T, self._set_thumbnail, None),
              (QtCore.Qt.Key_Return, self.descend_level, None),
              (QtCore.Qt.Key_Enter, self.descend_level, None),
              (QtCore.Qt.Key_Backspace, self.ascend_level, None),
              (QtCore.Qt.Key_Up, self.ascend_level, None, QtCore.Qt.KeyboardModifier.AltModifier),
          ]
        quit_keys = ['Q', 'Ctrl+Q', 'Ctrl+W', 'Alt+F4']
        self.shortcuts = []
        for mapping in self.normal_shortcuts:
            key, func, arg = mapping[0], mapping[1], mapping[2]
            modifiers = mapping[3] if len(mapping) > 3 else QtCore.Qt.KeyboardModifier.NoModifier
            s = QtGui.QShortcut(QtGui.QKeySequence(key | modifiers), self)
            if arg is None:
                s.activated.connect(func)
            else:
                s.activated.connect(lambda f=func, a=arg: f(a))
            self.shortcuts.append(s)
        for seq in quit_keys:
            s = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
            s.activated.connect(jdbrowser.main_window.close)
            self.shortcuts.append(s)

    def enter_search_mode(self):
        if not self.in_search_mode:
            if not self.sections:
                return
            self.in_search_mode = True
            self.prev_sec_idx = self.sec_idx
            self.prev_idx_in_sec = self.idx_in_sec
            self.search_matches = []
            self.current_match_idx = -1
            self.search_input.clear()
            self.search_input.show()
            self.search_input.setFocus()
            for s in self.shortcuts:
                key_str = s.key().toString()
                if key_str and not any(key_str.lower() == seq.lower() for seq in ['Q', 'Ctrl+Q', 'Ctrl+W', 'Alt+F4']):
                    s.setEnabled(False)
            for s in self.search_shortcut_instances:
                s.setEnabled(True)
            self.perform_search("")

    def exit_search_mode_revert(self):
        if self.in_search_mode:
            self.in_search_mode = False
            self.search_input.hide()
            self.sec_idx = self.prev_sec_idx
            self.idx_in_sec = self.prev_idx_in_sec
            self.search_matches = []
            self.current_match_idx = -1
            for s in self.shortcuts:
                s.setEnabled(True)
            for s in self.search_shortcut_instances:
                s.setEnabled(False)
            for sec in self.sections:
                for item in sec:
                    item.isDimmed = False
                    item.updateStyle()
            self.updateSelection()

    def exit_search_mode_select(self):
        if self.in_search_mode:
            self.in_search_mode = False
            self.search_input.hide()
            if self.search_matches and self.current_match_idx >= 0:
                self.sec_idx, self.idx_in_sec = self.search_matches[self.current_match_idx]
            self.search_matches = []
            self.current_match_idx = -1
            for s in self.shortcuts:
                s.setEnabled(True)
            for s in self.search_shortcut_instances:
                s.setEnabled(False)
            for sec in self.sections:
                for item in sec:
                    item.isDimmed = False
                    item.updateStyle()
            self.updateSelection()

    def perform_search(self, query):
        if not self.sections:
            return
        query = query.lower()
        self.search_matches = []
        for s, sec in enumerate(self.sections):
            for i, item in enumerate(sec):
                if item.tag_id and query in item.display_name.lower():  # Skip placeholders
                    self.search_matches.append((s, i))
                item.isDimmed = query and (not item.tag_id or not query in item.display_name.lower())
                item.updateStyle()
        if self.search_matches:
            self.current_match_idx = 0
            self.sec_idx, self.idx_in_sec = self.search_matches[0]
        else:
            self.current_match_idx = -1
        self.updateSelection()

    def next_match(self):
        if self.in_search_mode and self.current_match_idx < len(self.search_matches) - 1:
            self.current_match_idx += 1
            self.sec_idx, self.idx_in_sec = self.search_matches[self.current_match_idx]
            self.updateSelection()

    def prev_match(self):
        if self.in_search_mode and self.current_match_idx > 0:
            self.current_match_idx -= 1
            self.sec_idx, self.idx_in_sec = self.search_matches[self.current_match_idx]
            self.updateSelection()

    def moveHoriz(self, delta):
        if not self.in_search_mode and self.sections:
            sec = self.sections[self.sec_idx]
            new = self.idx_in_sec + delta
            if 0 <= new < len(sec):
                self.idx_in_sec = new
                self.desired_col = self.idx_in_sec % self.cols
            self.updateSelection()

    def moveVert(self, direction):
        if not self.in_search_mode and self.sections:
            pref_col = self.desired_col
            sec_index = self.sec_idx
            idx = self.idx_in_sec
            cols = self.cols
            sec = self.sections[sec_index]
            row = idx // cols
            rows = (len(sec) + cols - 1) // cols
            if direction > 0:
                if row + 1 < rows:
                    r2 = row + 1
                    length = min(cols, len(sec) - r2 * cols)
                    self.idx_in_sec = r2 * cols + min(pref_col, length - 1)
                elif sec_index + 1 < len(self.sections):
                    sec2 = self.sections[sec_index + 1]
                    length = min(cols, len(sec2))
                    self.sec_idx += 1
                    self.idx_in_sec = min(pref_col, length - 1)
                self.updateSelection()
            else:
                if row > 0:
                    r2 = row - 1
                    length = min(cols, len(sec) - r2 * cols)
                    self.idx_in_sec = r2 * cols + min(pref_col, length - 1)
                elif sec_index > 0:
                    sec2 = self.sections[sec_index - 1]
                    rows2 = (len(sec2) + cols - 1) // cols
                    last = rows2 - 1
                    length = min(cols, len(sec2) - last * cols)
                    self.sec_idx -= 1
                    self.idx_in_sec = last * cols + min(pref_col, length - 1)
                self.updateSelection()

    def moveToSectionStart(self):
        if not self.in_search_mode and self.sections:
            base = self.section_paths[self.sec_idx][1]
            current_order = base + self.idx_in_sec
            target_order = 0
            header_index = 0
            for i, h in enumerate(self.header_orders):
                if h <= current_order:
                    target_order = h
                    header_index = i
                else:
                    break
            start_base = (target_order // 10) * 10
            start_idx = target_order - start_base
            if (
                self.idx_in_sec == start_idx
                and header_index > 0
            ):
                target_order = self.header_orders[header_index - 1]
                start_base = (target_order // 10) * 10
                start_idx = target_order - start_base
            sec_idx = next(
                (i for i, p in enumerate(self.section_paths) if p[1] == start_base),
                self.sec_idx,
            )
            self.sec_idx = sec_idx
            self.idx_in_sec = min(start_idx, len(self.sections[sec_idx]) - 1)
            self.desired_col = self.idx_in_sec % self.cols
            self.updateSelection()

    def moveToSectionEnd(self):
        if not self.in_search_mode and self.sections:
            base = self.section_paths[self.sec_idx][1]
            current_order = base + self.idx_in_sec
            next_index = None
            for i, h in enumerate(self.header_orders):
                if h > current_order:
                    next_index = i
                    break
            if next_index is None:
                self.sec_idx = len(self.sections) - 1
                self.idx_in_sec = len(self.sections[self.sec_idx]) - 1
            else:
                target_order = self.header_orders[next_index] - 1
                end_base = (target_order // 10) * 10
                end_idx = target_order - end_base
                if self.idx_in_sec == end_idx:
                    if next_index + 1 < len(self.header_orders):
                        target_order = self.header_orders[next_index + 1] - 1
                        end_base = (target_order // 10) * 10
                        end_idx = target_order - end_base
                    else:
                        self.sec_idx = len(self.sections) - 1
                        self.idx_in_sec = len(self.sections[self.sec_idx]) - 1
                        self.desired_col = self.idx_in_sec % self.cols
                        self.updateSelection()
                        return
                sec_idx = next(
                    (
                        i
                        for i, p in enumerate(self.section_paths)
                        if p[1] == end_base
                    ),
                    len(self.sections) - 1,
                )
                self.sec_idx = sec_idx
                self.idx_in_sec = min(end_idx, len(self.sections[sec_idx]) - 1)
            self.desired_col = self.idx_in_sec % self.cols
            self.updateSelection()

    def moveToAbsoluteFirst(self):
        if not self.in_search_mode and self.sections:
            self.sec_idx = 0
            self.idx_in_sec = 0
            self.desired_col = 0
            self.updateSelection()

    def moveToAbsoluteLast(self):
        if not self.in_search_mode and self.sections:
            self.sec_idx = len(self.sections) - 1
            sec = self.sections[self.sec_idx]
            self.idx_in_sec = len(sec) - 1
            self.desired_col = self.idx_in_sec % self.cols
            self.updateSelection()

    def moveVertMultiple(self, count):
        if not self.in_search_mode and self.sections:
            for _ in range(abs(count)):
                self.moveVert(1 if count > 0 else -1)

    def centerSelectedItem(self):
        if not self.in_search_mode and self.sections:
            current = self.sections[self.sec_idx][self.idx_in_sec]
            self.scroll_area.ensureWidgetVisible(current)
            viewport = self.scroll_area.viewport()
            viewport_height = viewport.height()
            widget_rect = current.rect()
            widget_pos = current.mapTo(self.scroll_area.widget(), widget_rect.topLeft())
            scroll_bar = self.scroll_area.verticalScrollBar()
            target_pos = widget_pos.y() - (viewport_height - widget_rect.height()) // 2
            scroll_bar.setValue(max(0, target_pos))
            self.updateSelection()

    def copySelectedName(self):
        if not self.in_search_mode and self.sections:
            current = self.sections[self.sec_idx][self.idx_in_sec]
            if current.tag_id:  # Skip placeholders
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(current.display_name)

    def firstInRow(self):
        if not self.in_search_mode and self.sections:
            row = self.idx_in_sec // self.cols
            self.idx_in_sec = row * self.cols
            self.desired_col = 0
            self.updateSelection()

    def lastInRow(self):
        if not self.in_search_mode and self.sections:
            sec = self.sections[self.sec_idx]
            row = self.idx_in_sec // self.cols
            length = min(self.cols, len(sec) - row * self.cols)
            self.idx_in_sec = row * self.cols + length - 1
            self.desired_col = length - 1
            self.updateSelection()

    def descend_level(self):
        if not self.sections:
            return
        if not (0 <= self.sec_idx < len(self.sections)):
            return
        sec = self.sections[self.sec_idx]
        if not (0 <= self.idx_in_sec < len(sec)):
            return
        current_item = sec[self.idx_in_sec]
        if not current_item.tag_id:
            return
        from .jd_ext_page import JdExtPage
        new_page = JdExtPage(
            parent_uuid=current_item.tag_id,
            jd_area=current_item.jd_area,
            jd_id=current_item.jd_id,
            grandparent_uuid=self.parent_uuid,
        )
        jdbrowser.current_page = new_page
        jdbrowser.main_window.setCentralWidget(new_page)

    def updateSelection(self):
        if self.sections and 0 <= self.sec_idx < len(self.sections) and 0 <= self.idx_in_sec < len(self.sections[self.sec_idx]):
            current = self.sections[self.sec_idx][self.idx_in_sec]
            self.scroll_area.ensureWidgetVisible(current)
            for s, sec in enumerate(self.sections):
                for i, item in enumerate(sec):
                    item.isSelected = (s == self.sec_idx and i == self.idx_in_sec)
                    item.updateStyle()

    def mousePressEvent(self, event):
        if self.in_search_mode:
            self.exit_search_mode_select()
        super().mousePressEvent(event)

    def closeEvent(self, event):
        super().closeEvent(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        self.search_input.move(self.width() - 310, self.height() - 40)
        # Update header widths on resize
        for widget in self.scroll_area.widget().findChildren(QtWidgets.QLabel):
            if widget.styleSheet().startswith(f'background-color: {BUTTON_COLOR}'):
                widget.setMinimumWidth(self.scroll_area.viewport().width() - 10)
        super().resizeEvent(event)
