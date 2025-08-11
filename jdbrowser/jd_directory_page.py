import os
from PySide6 import QtWidgets, QtCore
import jdbrowser
from .constants import *
from .database import setup_database
from .directory_item import DirectoryItem

class JdDirectoryPage(QtWidgets.QWidget):
    def __init__(self, directory_id):
        super().__init__()
        self.directory_id = directory_id
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

        self._setup_ui()

        self.setStyleSheet(
            """
            QWidget { background-color: #000000; }
            """
        )

    # DirectoryItem expects a set_selection method on its page
    def set_selection(self, index):
        pass

    def _format_directory_id(self, directory_id):
        d = directory_id.replace('-', '').replace('_', '').upper()
        parts = [d[i:i+4] for i in range(0, min(len(d), 16), 4)]
        return '_'.join(parts)

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

        crumb = self._format_directory_id(self.directory_id)
        self.breadcrumb_bar = self._build_breadcrumb([(crumb, None)])
        layout.addWidget(self.breadcrumb_bar)

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

        self.item = DirectoryItem(
            self.directory_id, label, order, icon_data, self, 0, tags
        )
        self.item.updateLabel(self.show_prefix)
        self.item.isSelected = False
        self.item.updateStyle()
        layout.addWidget(self.item, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
