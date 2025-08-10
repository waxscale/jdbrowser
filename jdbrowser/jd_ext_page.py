import os
from collections import defaultdict
from PySide6 import QtWidgets, QtGui, QtCore
import jdbrowser
from .dialogs import EditTagDialog, SimpleEditTagDialog, InputTagDialog, DeleteTagDialog
from .dialogs.header_dialog import HeaderDialog
from .file_item import FileItem
from .header_item import HeaderItem
from .search_line_edit import SearchLineEdit
from .database import (
    create_jd_ext_tag,
    delete_jd_ext_tag,
    rebuild_state_jd_ext_tags,
    setup_database,
    create_jd_ext_header,
    update_jd_ext_header,
    delete_jd_ext_header,
    rebuild_state_jd_ext_headers,
)
from .constants import *

class JdExtPage(QtWidgets.QWidget):
    def __init__(self, parent_uuid, jd_area, jd_id, grandparent_uuid):
        super().__init__()
        if jdbrowser.main_window:
            jdbrowser.main_window.setWindowTitle(f"File Browser - [{jd_area:02d}.{jd_id:02d}]")
        self.parent_uuid = parent_uuid
        self.grandparent_uuid = grandparent_uuid
        self.current_jd_area = jd_area
        self.current_jd_id = jd_id
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
        # Load show_hidden state from QSettings
        settings = QtCore.QSettings("xAI", "jdbrowser")
        self.show_hidden = settings.value("show_hidden", False, type=bool)

        # Initialize SQLite database
        xdg_data_home = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        db_dir = os.path.join(xdg_data_home, 'jdbrowser')
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, 'tag.db')
        self.conn = setup_database(self.db_path)

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
                cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_icon')")
                event_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO event_set_jd_ext_tag_icon (event_id, tag_id, icon) VALUES (?, ?, ?)",
                    (event_id, tag_id, icon_data),
                )
                self.conn.commit()
                rebuild_state_jd_ext_tags(self.conn)
                self._rebuild_ui()

    def _create_header(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_ext_headers WHERE parent_uuid IS ?",
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
            header_id = create_jd_ext_header(
                self.conn, self.parent_uuid, order, label
            )
            if header_id:
                rebuild_state_jd_ext_headers(self.conn)
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
        _, _, base = self.section_paths[self.sec_idx]
        label = "NewTag"
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_ext_tags WHERE parent_uuid IS ? AND [order] >= ? AND [order] < ?",
            (self.parent_uuid, base, base + 10),
        )
        max_order = cursor.fetchone()[0]
        new_order = max_order + 1 if max_order is not None else base
        new_tag_id = create_jd_ext_tag(self.conn, self.parent_uuid, new_order, label)
        if new_tag_id:
            rebuild_state_jd_ext_tags(self.conn)
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
        _, _, base = self.section_paths[self.sec_idx]
        default_label = "NewTag"
        cursor.execute(
            "SELECT MAX([order]) FROM state_jd_ext_tags WHERE parent_uuid IS ? AND [order] >= ? AND [order] < ?",
            (self.parent_uuid, base, base + 10),
        )
        max_order = cursor.fetchone()[0]
        default_order = max_order + 1 if max_order is not None else base
        dialog = InputTagDialog(
            default_order,
            default_label,
            parent=self,
        )
        while True:
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                order, label = dialog.get_values()
                if order is None:
                    self._warn("Invalid Input", "Order must be an integer.")
                    continue
                new_tag_id = create_jd_ext_tag(self.conn, self.parent_uuid, order, label)
                if new_tag_id:
                    rebuild_state_jd_ext_tags(self.conn)
                    self._rebuild_ui(new_tag_id=new_tag_id)
                    break
                else:
                    self._warn(
                        "Constraint Violation",
                        f"Order {order:04d} is already in use.",
                    )
            else:
                break

    def ascend_level(self):
        from .jd_id_page import JdIdPage

        new_page = JdIdPage(parent_uuid=self.grandparent_uuid, jd_area=self.current_jd_area)
        self.conn.close()
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
                current_item.jd_ext,
                default_label,
                parent=self,
            )
            while True:
                if dialog.exec() == QtWidgets.QDialog.Accepted:
                    order, label = dialog.get_values()
                    if order is None:
                        self._warn("Invalid Input", "Order must be an integer.")
                        continue
                    new_tag_id = create_jd_ext_tag(self.conn, self.parent_uuid, order, label)
                    if new_tag_id:
                        rebuild_state_jd_ext_tags(self.conn)
                        self._rebuild_ui(new_tag_id=new_tag_id)
                        break
                    else:
                        self._warn(
                            "Constraint Violation",
                            f"Order {order:04d} is already in use.",
                        )
                else:
                    break
            return
        tag_id = current_item.tag_id
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT [order], label FROM state_jd_ext_tags WHERE tag_id = ?",
            (tag_id,),
        )
        jd_ext, current_label = cursor.fetchone()
        cursor.execute(
            "SELECT icon FROM state_jd_ext_tag_icons WHERE tag_id = ?",
            (tag_id,),
        )
        icon_data = cursor.fetchone()
        icon_data = icon_data[0] if icon_data else None
        while True:
            dialog = EditTagDialog(current_label, icon_data, 2, jd_ext, self)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                new_jd_ext = dialog.get_order()
                new_label = dialog.get_label()
                new_icon_data = dialog.get_icon_data()
                cursor.execute(
                    "SELECT tag_id FROM state_jd_ext_tags WHERE parent_uuid IS ? AND [order] = ? AND tag_id != ?",
                    (self.parent_uuid, new_jd_ext, tag_id),
                )
                if cursor.fetchone():
                    self._warn(
                        "Constraint Violation",
                        f"Order {new_jd_ext:04d} is already in use.",
                    )
                    current_label, icon_data, jd_ext = new_label, new_icon_data, new_jd_ext
                    continue
                if new_jd_ext != jd_ext:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_order')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_ext_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                        (event_id, tag_id, self.parent_uuid, new_jd_ext),
                    )
                if new_label != current_label:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_label')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_ext_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
                        (event_id, tag_id, new_label),
                    )
                if new_icon_data:
                    cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_icon')")
                    event_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO event_set_jd_ext_tag_icon (event_id, tag_id, icon) VALUES (?, ?, ?)",
                        (event_id, tag_id, new_icon_data),
                    )
                self.conn.commit()
                rebuild_state_jd_ext_tags(self.conn)
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
        cursor.execute(
            "SELECT label FROM state_jd_ext_tags WHERE tag_id = ?",
            (tag_id,),
        )
        current_label = cursor.fetchone()[0]
        dialog = SimpleEditTagDialog(current_label, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_label = dialog.get_label()
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_label')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_ext_tag_label (event_id, tag_id, new_label) VALUES (?, ?, ?)",
                (event_id, tag_id, new_label),
            )
            self.conn.commit()
            rebuild_state_jd_ext_tags(self.conn)
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
            "SELECT [order], label FROM state_jd_ext_tags WHERE tag_id = ?",
            (tag_id,),
        )
        jd_ext, tag_name = cursor.fetchone()
        prefix = f"[{self.current_jd_area:02d}.{self.current_jd_id:02d}+{jd_ext:04d}]"
        display_name = f"{prefix} {tag_name}" if tag_name else prefix
        dialog = DeleteTagDialog(display_name, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            delete_jd_ext_tag(self.conn, tag_id)
            rebuild_state_jd_ext_tags(self.conn)
            # Preserve current indices; selection will land on placeholder
            current_item.tag_id = None
            self._rebuild_ui()

    def handle_item_drop(self, source_tag_id, target_item):
        """Handle drag-and-drop operations between items."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT [order] FROM state_jd_ext_tags WHERE tag_id = ?",
            (source_tag_id,),
        )
        row = cursor.fetchone()
        if not row:
            return
        s_ext = row[0]
        if target_item.tag_id is None:
            new_ext = target_item.jd_ext
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_ext_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, source_tag_id, self.parent_uuid, new_ext),
            )
        else:
            target_tag_id = target_item.tag_id
            if target_tag_id == source_tag_id:
                return
            cursor.execute(
                "SELECT [order] FROM state_jd_ext_tags WHERE tag_id = ?",
                (target_tag_id,),
            )
            t_ext = cursor.fetchone()[0]
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_ext_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, target_tag_id, self.parent_uuid, -1),
            )
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_ext_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, source_tag_id, self.parent_uuid, t_ext),
            )
            cursor.execute("INSERT INTO events (event_type) VALUES ('set_jd_ext_tag_order')")
            event_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO event_set_jd_ext_tag_order (event_id, tag_id, parent_uuid, [order]) VALUES (?, ?, ?, ?)",
                (event_id, target_tag_id, self.parent_uuid, s_ext),
            )
        self.conn.commit()
        rebuild_state_jd_ext_tags(self.conn)
        self._rebuild_ui(new_tag_id=source_tag_id)

    def _edit_header(self, header_item):
        dialog = HeaderDialog(header_item.jd_ext, header_item.label, True, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            if dialog.delete_pressed:
                delete_jd_ext_header(self.conn, header_item.header_id)
            else:
                order = dialog.get_order()
                label = dialog.get_label()
                if order is None:
                    self._warn("Invalid Input", "Order must be an integer.")
                    return
                if not update_jd_ext_header(
                    self.conn,
                    header_item.header_id,
                    self.parent_uuid,
                    order,
                    label,
                ):
                    self._warn("Invalid Input", "Header order conflicts or invalid.")
                    return
            rebuild_state_jd_ext_headers(self.conn)
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

    def _setup_ui(self):
        if not hasattr(self, "scroll_area"):
            self.scroll_area = QtWidgets.QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
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
        mainLayout = QtWidgets.QVBoxLayout(container)
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(5, 5, 5, 5)

        self.sections = []
        self.section_paths = []
        self.section_filenames = []
        current_section = None
        section_index = 0
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT header_id, [order], label FROM state_jd_ext_headers WHERE parent_uuid IS ? ORDER BY [order]",
            (self.parent_uuid,),
        )
        headers = cursor.fetchall()
        self.header_orders = sorted({0, *(order for _, order, _ in headers)})
        cursor.execute(
            "SELECT tag_id, [order], label FROM state_jd_ext_tags WHERE parent_uuid IS ? ORDER BY [order]",
            (self.parent_uuid,),
        )
        tags = cursor.fetchall()
        cursor.execute("SELECT tag_id, icon FROM state_jd_ext_tag_icons")
        icons = {row[0]: row[1] for row in cursor.fetchall()}

        def construct_prefix(order):
            return f"[{self.current_jd_area:02d}.{self.current_jd_id:02d}+{order:04d}]"

        # Organize headers and tags by their exact order values
        headers_by_order = defaultdict(list)
        for header_id, order, label in headers:
            prefix = construct_prefix(order)
            headers_by_order[order].append((header_id, order, label, prefix))
        tags = sorted(tags, key=lambda x: x[1])

        # Build sections and placeholders
        def placeholder_item(val, sec_idx, item_idx):
            pa, pi, pe = self.current_jd_area, self.current_jd_id, val
            item = FileItem(None, None, pa, pi, pe, None, self, sec_idx, item_idx)
            item.updateLabel(self.show_prefix)
            return item

        section_index = 0
        current_section = None
        section_base = None
        next_index = 0

        def add_section(section):
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

        def start_section(base, base_path, filename_id):
            nonlocal current_section, section_base, next_index
            current_section = []
            self.section_paths.append(base_path)
            self.section_filenames.append(filename_id)
            section_base = base
            next_index = 0

        def add_placeholders_until(end_index):
            nonlocal next_index
            for i in range(next_index, end_index):
                val = section_base + i
                current_section.append(placeholder_item(val, section_index, i))
            next_index = end_index

        def flush_section():
            nonlocal current_section, section_index, section_base, next_index
            if current_section is None:
                return
            if not current_section:
                val = section_base
                current_section.append(placeholder_item(val, section_index, 0))
            else:
                add_placeholders_until(next_index + 1)
            add_section(current_section)
            section_index += 1
            current_section = None
            section_base = None
            next_index = 0
        section_starts = sorted({0, *headers_by_order.keys()})
        tag_idx = 0
        for i, base in enumerate(section_starts):
            next_start = section_starts[i + 1] if i + 1 < len(section_starts) else None
            last_header_id = None
            for obj_id, order, label, prefix in headers_by_order.get(base, []):
                display = f"{prefix} {label}" if prefix else (label or "")
                header_item = HeaderItem(
                    obj_id,
                    self.current_jd_area,
                    self.current_jd_id,
                    order,
                    label,
                    self,
                    section_index,
                    display,
                )
                header_item.setMinimumWidth(self.scroll_area.viewport().width() - 10)
                mainLayout.addWidget(header_item)
                mainLayout.addSpacing(10)
                last_header_id = obj_id
            start_section(base, (self.current_jd_area, self.current_jd_id, base), last_header_id)
            while tag_idx < len(tags) and (next_start is None or tags[tag_idx][1] < next_start):
                obj_id, order, label = tags[tag_idx]
                index = order - base
                add_placeholders_until(index)
                icon_data = icons.get(obj_id)
                item = FileItem(
                    obj_id,
                    label,
                    self.current_jd_area,
                    self.current_jd_id,
                    order,
                    icon_data,
                    self,
                    section_index,
                    index,
                )
                item.updateLabel(self.show_prefix)
                current_section.append(item)
                next_index = index + 1
                tag_idx += 1
            flush_section()

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
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
        QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
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
            base = self.section_paths[self.sec_idx][2]
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
                (i for i, p in enumerate(self.section_paths) if p[2] == start_base),
                self.sec_idx,
            )
            self.sec_idx = sec_idx
            self.idx_in_sec = min(start_idx, len(self.sections[sec_idx]) - 1)
            self.desired_col = self.idx_in_sec % self.cols
            self.updateSelection()

    def moveToSectionEnd(self):
        """Jump to the last item of the current section or the next section."""
        if self.in_search_mode or not self.sections:
            return

        last_index = len(self.sections[self.sec_idx]) - 1

        if self.idx_in_sec >= last_index:
            if self.sec_idx + 1 < len(self.sections):
                self.sec_idx += 1
                self.idx_in_sec = len(self.sections[self.sec_idx]) - 1
        else:
            self.idx_in_sec = last_index

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
        from .jd_directory_list_page import JdDirectoryListPage
        new_page = JdDirectoryListPage(
            parent_uuid=current_item.tag_id,
            jd_area=current_item.jd_area,
            jd_id=current_item.jd_id,
            jd_ext=current_item.jd_ext,
            grandparent_uuid=self.parent_uuid,
            great_grandparent_uuid=self.grandparent_uuid,
        )
        self.conn.close()
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
        self.conn.close()
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
