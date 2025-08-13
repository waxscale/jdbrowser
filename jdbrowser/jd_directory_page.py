import os
import re
import weakref
from collections import deque
from datetime import datetime, timezone
from PySide6 import QtWidgets, QtCore, QtGui, QtMultimedia
from shiboken6 import isValid
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
from .search_line_edit import SearchLineEdit
from .config import read_config

# Mapping of common file extensions to FiraCode Nerd Font icons
FILE_TYPE_ICONS = {
    ".txt": "\uf15c",  # nf-fa-file_text_o
    ".md": "\ue73e",  # nf-oct-markdown
    ".csv": "\uf1c3",  # nf-fa-file_excel_o
    ".json": "\ufb25",  # nf-mdi-json
    ".py": "\ue606",  # nf-dev-python
    ".sh": "\uf489",  # nf-oct-terminal
    ".pdf": "\uf1c1",  # nf-fa-file_pdf_o
    ".zip": "\uf1c6",  # nf-fa-file_archive_o
    ".mp3": "\uf001",  # nf-fa-music
    ".wav": "\uf1c7",  # nf-fa-file_audio_o
    ".html": "\uf13b",  # nf-fa-html5
    ".css": "\uf13c",  # nf-fa-css3
    ".js": "\uf3b8",  # nf-dev-javascript
    ".svg": "\uf1c9",  # nf-fa-file_image_o
}
DEFAULT_FILE_ICON = "\uf15b"  # nf-fa-file_o


THUMBNAIL_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".webp",
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
}


class ThumbnailLoader(QtCore.QRunnable):
    def __init__(self, page, label, path):
        super().__init__()
        self.page_ref = weakref.ref(page)
        self.label_ref = weakref.ref(label)
        self.path = path

    def run(self):
        page = self.page_ref()
        label = self.label_ref()
        if not page or not label or not isValid(page) or not isValid(label):
            return
        pixmap = page._thumbnail_for_path(self.path)
        if pixmap and isValid(label):
            QtCore.QMetaObject.invokeMethod(
                label,
                "setPixmap",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(QtGui.QPixmap, pixmap),
            )

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
        self.repository_path = read_config()
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

        self._pending_thumbnails: deque[
            tuple[weakref.ReferenceType[QtWidgets.QLabel], str]
        ] = deque()
        self._thumb_pool = QtCore.QThreadPool()
        self._thumb_pool.setMaxThreadCount(1)

        self.in_search_mode = False
        self.prev_selected_is_directory = False
        self.prev_row = -1
        self.search_matches: list[int] = []
        self.current_match_idx = -1
        self.search_shortcut_instances: list[QtGui.QShortcut] = []

        self.section_bounds: list[tuple[int, int]] = []

        self._thumbs_started = False

        self._setup_ui()
        self._setup_shortcuts()
        self.set_selection(0)
        style = f"""
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
        """
        self.setStyleSheet(style)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._thumbs_started:
            self._thumbs_started = True
            QtCore.QTimer.singleShot(0, self._start_pending_thumbnails)

    # DirectoryItem expects a set_selection method on its page
    def set_selection(self, index):
        if index == 0:
            # Deselect any file items so only the directory entry is selected
            self.file_list.setCurrentItem(None)
            self.file_list.clearSelection()
        self.item.isSelected = index == 0
        self.item.updateStyle()

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
        if icon_data is None:
            icon_data = self._fallback_icon(order)

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

        # List of files within the directory
        self.file_list = QtWidgets.QListWidget()
        self.file_list.setIconSize(QtCore.QSize(120, 75))
        self.file_list.setMouseTracking(True)
        self.file_list.setStyleSheet(
            "QListWidget{background-color: transparent; border: none;}"
            "QListWidget::item{background-color: transparent; border: none; border-radius: 5px;}"
            f"QListWidget::item:hover{{background-color: {HOVER_COLOR};}}"
            f"QListWidget::item:selected{{background-color: {HIGHLIGHT_COLOR};}}"
            f"QListWidget::item:selected:hover{{background-color: {HIGHLIGHT_COLOR};}}"
        )
        self.file_list.setSpacing(2)
        self.file_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.file_list.currentItemChanged.connect(self._file_selection_changed)
        layout.addWidget(self.file_list)

        self._populate_files(order)

        self.search_input = SearchLineEdit(self)
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(30)
        self.search_input.hide()
        self.search_input.textChanged.connect(self.perform_search)
        self._setup_search_shortcuts()
        self.search_input.move(self.width() - 310, self.height() - 40)

    def _strip_prefix(self, text: str) -> str:
        return re.sub(r"^\[[^\]]*\]\s*", "", text).strip()

    def _populate_files(self, order: int) -> None:
        folder = self._format_order(order)
        path = os.path.join(self.repository_path, folder)
        if not os.path.isdir(path):
            return
        files = [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f))
        ]
        files.sort(key=lambda x: x.lower())
        self.section_bounds = []
        current_start = None
        for name in files:
            full_path = os.path.join(path, name)
            if name.lower().endswith(".2do"):
                if current_start is not None:
                    self.section_bounds.append(
                        (current_start, self.file_list.count() - 1)
                    )
                    current_start = None
                label = self._strip_prefix(os.path.splitext(name)[0])
                header = QtWidgets.QLabel(label)
                header.setAlignment(
                    QtCore.Qt.AlignmentFlag.AlignLeft
                    | QtCore.Qt.AlignmentFlag.AlignVCenter
                )
                font = header.font()
                font.setPointSize(int(font.pointSize() * 0.75))
                font.setBold(True)
                header.setFont(font)
                header.setStyleSheet(
                    f"background-color: {BUTTON_COLOR}; color: black; padding-left:5px; padding-right:5px;"
                )
                header.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
                )
                item = QtWidgets.QListWidgetItem(self.file_list)
                item.setSizeHint(header.sizeHint())
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                item.setData(QtCore.Qt.UserRole, "header")
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, header)
                continue
            widget = self._create_file_row(full_path, name)
            item = QtWidgets.QListWidgetItem(self.file_list)
            item.setSizeHint(widget.sizeHint())
            item.setData(QtCore.Qt.UserRole, name)
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, widget)
            if current_start is None:
                current_start = self.file_list.count() - 1
        if current_start is not None:
            self.section_bounds.append((current_start, self.file_list.count() - 1))

    def refresh_file_list(self) -> None:
        scrollbar = self.file_list.verticalScrollBar()
        scroll_pos = scrollbar.value()

        current_name = None
        current_item = self.file_list.currentItem()
        if current_item is not None:
            widget = self.file_list.itemWidget(current_item)
            if widget is not None:
                label_widget = widget.layout().itemAt(1).widget()
                if isinstance(label_widget, QtWidgets.QLabel):
                    current_name = label_widget.text()

        order = getattr(self.item, "order", None)
        if order is None:
            self.file_list.clear()
            return
        folder = self._format_order(order)
        path = os.path.join(self.repository_path, folder)
        if not os.path.isdir(path):
            self.file_list.clear()
            return

        files = [
            f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f))
        ]
        files.sort(key=lambda x: x.lower())

        self.file_list.clear()
        self.section_bounds = []
        self._pending_thumbnails = deque()
        self._thumb_pool.clear()
        current_start = None
        non_header_names = [n for n in files if not n.lower().endswith('.2do')]
        target_name = None
        if current_name:
            if current_name in non_header_names:
                target_name = current_name
            else:
                for n in non_header_names:
                    if n < current_name:
                        target_name = n
                    else:
                        break
        target_row = None
        for name in files:
            full_path = os.path.join(path, name)
            if name.lower().endswith('.2do'):
                if current_start is not None:
                    self.section_bounds.append(
                        (current_start, self.file_list.count() - 1)
                    )
                    current_start = None
                label = self._strip_prefix(os.path.splitext(name)[0])
                header = QtWidgets.QLabel(label)
                header.setAlignment(
                    QtCore.Qt.AlignmentFlag.AlignLeft
                    | QtCore.Qt.AlignmentFlag.AlignVCenter
                )
                font = header.font()
                font.setPointSize(int(font.pointSize() * 0.75))
                font.setBold(True)
                header.setFont(font)
                header.setStyleSheet(
                    f"background-color: {BUTTON_COLOR}; color: black; padding-left:5px; padding-right:5px;"
                )
                header.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
                )
                item = QtWidgets.QListWidgetItem(self.file_list)
                item.setSizeHint(header.sizeHint())
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                item.setData(QtCore.Qt.UserRole, 'header')
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, header)
                continue
            widget = self._create_file_row(full_path, name)
            item = QtWidgets.QListWidgetItem(self.file_list)
            item.setSizeHint(widget.sizeHint())
            item.setData(QtCore.Qt.UserRole, name)
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, widget)
            if current_start is None:
                current_start = self.file_list.count() - 1
            if target_name is not None and name == target_name:
                target_row = self.file_list.count() - 1
        if current_start is not None:
            self.section_bounds.append((current_start, self.file_list.count() - 1))

        if target_row is not None:
            self.file_list.setCurrentRow(target_row)
        else:
            self.file_list.setCurrentItem(None)

        QtCore.QTimer.singleShot(0, lambda: scrollbar.setValue(scroll_pos))
        QtCore.QTimer.singleShot(0, self._start_pending_thumbnails)

    def _is_header_row(self, row: int) -> bool:
        item = self.file_list.item(row)
        return bool(item and item.data(QtCore.Qt.UserRole) == "header")

    def _next_non_header_index(self, start: int, step: int) -> int | None:
        count = self.file_list.count()
        idx = start
        while 0 <= idx < count and self._is_header_row(idx):
            idx += step
        if 0 <= idx < count:
            return idx
        return None

    def _create_file_row(self, path: str, name: str) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        row.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        row.setStyleSheet("background-color: transparent;")
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(120, 75)
        icon_label.setStyleSheet("border: none; border-radius: 10px;")
        ext = os.path.splitext(name)[1].lower()
        if ext in THUMBNAIL_EXTS:
            placeholder = QtGui.QPixmap(120, 75)
            placeholder.fill(QtGui.QColor(SLATE_COLOR))
            icon_label.setPixmap(placeholder)
            self._pending_thumbnails.append((weakref.ref(icon_label), path))
        else:
            char = self._icon_for_extension(ext)
            pixmap = QtGui.QPixmap(120, 75)
            pixmap.fill(QtGui.QColor(SLATE_COLOR))
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            font = QtGui.QFont("FiraCode Nerd Font", 48)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(TEXT_COLOR))
            painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, char)
            painter.end()
            icon_label.setPixmap(self._rounded_pixmap(pixmap))
        layout.addWidget(icon_label)

        label = QtWidgets.QLabel(name)
        label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft
        )
        label.setStyleSheet(f"color: {TEXT_COLOR};")
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        layout.addWidget(label, 1)
        return row

    def _icon_for_extension(self, ext: str) -> str:
        return FILE_TYPE_ICONS.get(ext, DEFAULT_FILE_ICON)

    def _rounded_pixmap(self, pixmap: QtGui.QPixmap) -> QtGui.QPixmap:
        if pixmap.isNull():
            return pixmap
        scaled = pixmap.scaled(
            120,
            75,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        rounded = QtGui.QPixmap(120, 75)
        rounded.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(rounded)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, 120, 75, 10, 10)
        painter.setClipPath(path)
        painter.drawPixmap(
            (120 - scaled.width()) // 2,
            (75 - scaled.height()) // 2,
            scaled,
        )
        painter.end()
        return rounded

    def _video_thumbnail(self, path: str) -> QtGui.QPixmap | None:
        player = QtMultimedia.QMediaPlayer()
        sink = QtMultimedia.QVideoSink()
        player.setVideoSink(sink)
        thumb = {"pixmap": None}

        def handle_frame(frame: QtMultimedia.QVideoFrame):
            if frame.isValid() and thumb["pixmap"] is None:
                image = frame.toImage()
                thumb["pixmap"] = self._rounded_pixmap(
                    QtGui.QPixmap.fromImage(image)
                )
                player.stop()

        sink.videoFrameChanged.connect(handle_frame)
        player.setSource(QtCore.QUrl.fromLocalFile(path))
        player.play()

        loop = QtCore.QEventLoop()
        sink.videoFrameChanged.connect(loop.quit)
        QtCore.QTimer.singleShot(1000, loop.quit)
        loop.exec()
        player.stop()
        return thumb["pixmap"]

    def _thumbnail_for_path(self, path: str) -> QtGui.QPixmap | None:
        ext = os.path.splitext(path)[1].lower()
        if ext in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
            pixmap = QtGui.QPixmap(path)
            if not pixmap.isNull():
                return self._rounded_pixmap(pixmap)
            if ext == ".webp":
                return self._video_thumbnail(path)
            return None
        if ext in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
            return self._video_thumbnail(path)
        return None

    def _load_thumbnail_async(
        self, label: QtWidgets.QLabel, path: str
    ) -> None:
        runnable = ThumbnailLoader(self, label, path)
        self._thumb_pool.start(runnable)

    def _start_pending_thumbnails(self) -> None:
        if not self._pending_thumbnails:
            return
        label_ref, path = self._pending_thumbnails.popleft()
        label = label_ref()
        if label and isValid(label):
            self._load_thumbnail_async(label, path)
        if self._pending_thumbnails:
            QtCore.QTimer.singleShot(0, self._start_pending_thumbnails)

    def _open_terminal(self) -> None:
        order = getattr(self.item, "order", None)
        if order is None:
            return
        folder = self._format_order(order)
        path = os.path.join(self.repository_path, folder)
        if os.path.isdir(path):
            QtCore.QProcess.startDetached("kitty", [], path)

    def _open_thunar(self) -> None:
        order = getattr(self.item, "order", None)
        if order is None:
            return
        folder = self._format_order(order)
        path = os.path.join(self.repository_path, folder)
        if os.path.isdir(path):
            QtCore.QProcess.startDetached("thunar", [path])

    def move_selection(self, direction: int) -> None:
        if self.in_search_mode:
            return
        count = self.file_list.count()
        if count == 0:
            return
        current = self.file_list.currentRow()
        if current == -1:
            if direction > 0:
                index = self._next_non_header_index(0, 1)
                if index is not None:
                    self.file_list.setCurrentRow(index)
                    self.file_list.scrollToItem(self.file_list.item(index))
            return
        index = current + direction
        if index < 0:
            self.file_list.setCurrentItem(None)
            return
        if index >= count:
            index = count - 1
        index = self._next_non_header_index(index, 1 if direction > 0 else -1)
        if index is None:
            if direction < 0:
                self.file_list.setCurrentItem(None)
            return
        self.file_list.setCurrentRow(index)
        item = self.file_list.item(index)
        if item:
            self.file_list.scrollToItem(item)

    def move_selection_multiple(self, count: int) -> None:
        if self.in_search_mode or self.file_list.count() == 0:
            return
        for _ in range(abs(count)):
            self.move_selection(1 if count > 0 else -1)

    def move_to_start(self) -> None:
        if self.in_search_mode or self.file_list.count() == 0:
            return
        index = self._next_non_header_index(0, 1)
        if index is not None:
            self.file_list.setCurrentRow(index)
            self.file_list.scrollToItem(self.file_list.item(index))

    def move_to_end(self) -> None:
        if self.in_search_mode:
            return
        count = self.file_list.count()
        if count == 0:
            return
        index = self._next_non_header_index(count - 1, -1)
        if index is not None:
            self.file_list.setCurrentRow(index)
            self.file_list.scrollToItem(self.file_list.item(index))

    def centerSelectedItem(self) -> None:
        if self.in_search_mode:
            return
        if self._is_directory_selected():
            self.file_list.scrollToTop()
        else:
            item = self.file_list.currentItem()
            if item:
                self.file_list.scrollToItem(
                    item, QtWidgets.QAbstractItemView.PositionAtCenter
                )

    def move_to_section_start(self) -> None:
        if self.in_search_mode or not self.section_bounds:
            return
        current = self.file_list.currentRow()
        if current == -1:
            return
        for i, (start, end) in enumerate(self.section_bounds):
            if start <= current <= end:
                if current != start:
                    target = start
                    self.file_list.setCurrentRow(target)
                    self._scroll_with_header(target, -1)
                else:
                    if i > 0:
                        target = self.section_bounds[i - 1][0]
                        self.file_list.setCurrentRow(target)
                        self._scroll_with_header(target, -1)
                    else:
                        self.file_list.setCurrentItem(None)
                        self.file_list.scrollToTop()
                break

    def move_to_section_end(self) -> None:
        if self.in_search_mode or not self.section_bounds:
            return
        current = self.file_list.currentRow()
        if current == -1:
            end = self.section_bounds[0][1]
            self.file_list.setCurrentRow(end)
            self._scroll_with_header(end, 1)
            return
        for i, (start, end) in enumerate(self.section_bounds):
            if start <= current <= end:
                target = end if current != end else (
                    self.section_bounds[i + 1][1]
                    if i + 1 < len(self.section_bounds)
                    else end
                )
                self.file_list.setCurrentRow(target)
                self._scroll_with_header(target, 1)
                break

    def _scroll_with_header(self, row: int, direction: int) -> None:
        header_row = row + direction
        if 0 <= header_row < self.file_list.count():
            header_item = self.file_list.item(header_row)
            if header_item and header_item.data(QtCore.Qt.UserRole) == "header":
                position = (
                    QtWidgets.QAbstractItemView.PositionAtTop
                    if direction < 0
                    else QtWidgets.QAbstractItemView.PositionAtBottom
                )
                self.file_list.scrollToItem(header_item, position)
                return
        self.file_list.scrollToItem(self.file_list.item(row))

    def _file_selection_changed(
        self, current: QtWidgets.QListWidgetItem | None, _prev
    ) -> None:
        if not self.in_search_mode:
            self.item.isSelected = current is None
            self.item.updateStyle()

    def _is_directory_selected(self) -> bool:
        return self.file_list.currentItem() is None

    def _setup_search_shortcuts(self):
        for s in self.search_shortcut_instances:
            s.deleteLater()
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
        for key, func, arg, *mod in search_shortcuts:
            modifiers = mod[0] if mod else QtCore.Qt.KeyboardModifier.NoModifier
            s = QtGui.QShortcut(QtGui.QKeySequence(key | modifiers), self.search_input)
            s.setEnabled(False)
            if arg is None:
                s.activated.connect(func)
            else:
                s.activated.connect(lambda f=func, a=arg: f(a))
            self.search_shortcut_instances.append(s)

    def enter_search_mode(self):
        if not self.in_search_mode:
            if self.file_list.count() == 0:
                return
            self.in_search_mode = True
            self.prev_selected_is_directory = self.item.isSelected
            if self.prev_selected_is_directory:
                self.item.isSelected = False
                self.item.updateStyle()
                self.prev_row = -1
            else:
                self.prev_row = self.file_list.currentRow()
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
            self.item.isDimmed = False
            self.item.updateStyle()
            for i in range(self.file_list.count()):
                widget = self.file_list.itemWidget(self.file_list.item(i))
                if widget:
                    widget.setGraphicsEffect(None)
            if self.prev_selected_is_directory:
                self.set_selection(0)
            elif self.prev_row >= 0:
                self.file_list.setCurrentRow(self.prev_row)
            self.search_matches = []
            self.current_match_idx = -1
            for s in self.shortcuts:
                s.setEnabled(True)
            for s in self.search_shortcut_instances:
                s.setEnabled(False)
            self.setFocus()

    def exit_search_mode_select(self):
        if self.in_search_mode:
            self.in_search_mode = False
            self.search_input.hide()
            self.item.isDimmed = False
            self.item.updateStyle()
            for i in range(self.file_list.count()):
                widget = self.file_list.itemWidget(self.file_list.item(i))
                if widget:
                    widget.setGraphicsEffect(None)
            if self.search_matches and self.current_match_idx >= 0:
                idx = self.search_matches[self.current_match_idx]
                self.file_list.setCurrentRow(idx)
                self.file_list.scrollToItem(self.file_list.item(idx))
            elif self.prev_selected_is_directory:
                self.set_selection(0)
            elif self.prev_row >= 0:
                self.file_list.setCurrentRow(self.prev_row)
            self.search_matches = []
            self.current_match_idx = -1
            for s in self.shortcuts:
                s.setEnabled(True)
            for s in self.search_shortcut_instances:
                s.setEnabled(False)
            self.setFocus()

    def perform_search(self, query):
        query = query.lower()
        self.search_matches = []
        self.item.isDimmed = bool(query)
        self.item.updateStyle()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if widget:
                widget.setGraphicsEffect(None)
            data = item.data(QtCore.Qt.UserRole)
            if data == "header":
                continue
            name = str(data).lower()
            if query and query in name:
                self.search_matches.append(i)
            elif query and widget:
                effect = QtWidgets.QGraphicsOpacityEffect(widget)
                effect.setOpacity(0.4)
                widget.setGraphicsEffect(effect)
        if self.search_matches:
            self.current_match_idx = 0
            idx = self.search_matches[0]
            self.file_list.setCurrentRow(idx)
            self.file_list.scrollToItem(self.file_list.item(idx))
        else:
            self.current_match_idx = -1
            if query:
                self.file_list.setCurrentItem(None)

    def next_match(self):
        if self.in_search_mode and self.current_match_idx < len(self.search_matches) - 1:
            self.current_match_idx += 1
            idx = self.search_matches[self.current_match_idx]
            self.file_list.setCurrentRow(idx)
            self.file_list.scrollToItem(self.file_list.item(idx))

    def prev_match(self):
        if self.in_search_mode and self.current_match_idx > 0:
            self.current_match_idx -= 1
            idx = self.search_matches[self.current_match_idx]
            self.file_list.setCurrentRow(idx)
            self.file_list.scrollToItem(self.file_list.item(idx))

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
            (QtCore.Qt.Key_J, self.move_selection, 1),
            (QtCore.Qt.Key_Down, self.move_selection, 1),
            (QtCore.Qt.Key_K, self.move_selection, -1),
            (QtCore.Qt.Key_Up, self.move_selection, -1),
            (
                QtCore.Qt.Key_U,
                self.move_selection_multiple,
                -3,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
            (
                QtCore.Qt.Key_D,
                self.move_selection_multiple,
                3,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
            (QtCore.Qt.Key_PageUp, self.move_selection_multiple, -3),
            (QtCore.Qt.Key_PageDown, self.move_selection_multiple, 3),
            (QtCore.Qt.Key_Z, self.centerSelectedItem, None),
            (QtCore.Qt.Key_BracketLeft, self.move_to_section_start, None),
            (QtCore.Qt.Key_BracketRight, self.move_to_section_end, None),
            (QtCore.Qt.Key_G, self.move_to_start, None),
            (
                QtCore.Qt.Key_G,
                self.move_to_end,
                None,
                QtCore.Qt.KeyboardModifier.ShiftModifier,
            ),
            (QtCore.Qt.Key_Home, self.move_to_start, None),
            (QtCore.Qt.Key_End, self.move_to_end, None),
            (QtCore.Qt.Key_H, lambda: None, None),
            (QtCore.Qt.Key_Left, lambda: None, None),
            (QtCore.Qt.Key_L, lambda: None, None),
            (QtCore.Qt.Key_Right, lambda: None, None),
            (QtCore.Qt.Key_C, self._edit_tag_label_with_icon, None),
            (QtCore.Qt.Key_R, self._rename_selected, None),
            (QtCore.Qt.Key_F2, self._rename_selected, None),
            (QtCore.Qt.Key_F5, self.refresh_file_list, None),
            (QtCore.Qt.Key_E, self.open_tag_search, None),
            (QtCore.Qt.Key_X, self.open_remove_tag_search, None),
            (QtCore.Qt.Key_Equal, self._apply_unra_prefix, (True, False)),
            (
                QtCore.Qt.Key_Equal,
                self._apply_unra_prefix,
                (True, True),
                QtCore.Qt.KeyboardModifier.ShiftModifier,
            ),
            (QtCore.Qt.Key_Minus, self._apply_unra_prefix, (False, False)),
            (
                QtCore.Qt.Key_Minus,
                self._apply_unra_prefix,
                (False, True),
                QtCore.Qt.KeyboardModifier.ShiftModifier,
            ),
            (
                QtCore.Qt.Key_T,
                self._open_terminal,
                None,
                QtCore.Qt.KeyboardModifier.ShiftModifier,
            ),
            (
                QtCore.Qt.Key_D,
                self._open_thunar,
                None,
                QtCore.Qt.KeyboardModifier.ShiftModifier,
            ),
            (QtCore.Qt.Key_Slash, self.enter_search_mode, None),
            (
                QtCore.Qt.Key_F,
                self.enter_search_mode,
                None,
                QtCore.Qt.KeyboardModifier.ControlModifier,
            ),
        ]
        for i in range(10):
            mappings.append(
                (getattr(QtCore.Qt, f"Key_{i}"), self._apply_header_number, i)
            )
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
                if not isinstance(self.item.icon, QtWidgets.QLabel):
                    layout = self.item.layout()
                    layout.removeWidget(self.item.icon)
                    self.item.icon.deleteLater()
                    self.item.icon = QtWidgets.QLabel()
                    self.item.icon.mousePressEvent = self.item.mousePressEvent  # type: ignore[attr-defined]
                    self.item.icon.installEventFilter(self.item)
                    layout.insertWidget(0, self.item.icon)
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
            if not isinstance(self.item.icon, QtWidgets.QFrame):
                layout = self.item.layout()
                layout.removeWidget(self.item.icon)
                self.item.icon.deleteLater()
                self.item.icon = QtWidgets.QFrame()
                self.item.icon.mousePressEvent = self.item.mousePressEvent  # type: ignore[attr-defined]
                self.item.icon.installEventFilter(self.item)
                layout.insertWidget(0, self.item.icon)
            self.item.icon.setFixedSize(240, 150)
            self.item.icon.setStyleSheet(
                f"background-color: {SLATE_COLOR}; border-radius: 5px;"
            )
        self.item.updateStyle()

    def _rename_file(self) -> None:
        item = self.file_list.currentItem()
        if not item:
            return
        name = item.data(QtCore.Qt.UserRole)
        if not name or name == "header":
            return
        order = getattr(self.item, "order", None)
        if order is None:
            return
        folder = self._format_order(order)
        dir_path = os.path.join(self.repository_path, folder)
        old_path = os.path.join(dir_path, name)
        dialog = SimpleEditTagDialog(name, self)
        dialog.setWindowTitle("Rename File")
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_name = dialog.get_label()
            if not new_name or new_name == name:
                return
            new_path = os.path.join(dir_path, new_name)
            if os.path.exists(new_path):
                self._warn("Rename File", f"File {new_name} already exists.")
                return
            try:
                os.rename(old_path, new_path)
            except OSError as e:
                self._warn("Rename File", str(e))
                return
            self.refresh_file_list()
            for i in range(self.file_list.count()):
                it = self.file_list.item(i)
                if it.data(QtCore.Qt.UserRole) == new_name:
                    self.file_list.setCurrentRow(i)
                    self.file_list.scrollToItem(it)
                    break

    def _apply_unra_prefix(self, opts: tuple[bool, bool]) -> None:
        use_file_time, replace_entire = opts
        if self._is_directory_selected():
            return
        item = self.file_list.currentItem()
        if not item:
            return
        name = item.data(QtCore.Qt.UserRole)
        if not name or name == "header":
            return
        order = getattr(self.item, "order", None)
        if order is None:
            return
        folder = self._format_order(order)
        dir_path = os.path.join(self.repository_path, folder)
        old_path = os.path.join(dir_path, name)
        if use_file_time:
            stat = os.stat(old_path)
            ts = getattr(stat, "st_birthtime", stat.st_mtime)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            dt = datetime.now(tz=timezone.utc)
        ts_str = dt.strftime("%Y-%m-%d %H.%M.%S")
        rest = re.sub(r"^\[[^\]]*\]\s*", "", name)
        _, ext = os.path.splitext(rest)
        if replace_entire:
            if not ext and rest.startswith("."):
                ext = rest
            new_name = f"[5-UNRA {ts_str}]" + ext
        else:
            if not rest or rest.startswith("."):
                new_name = f"[5-UNRA {ts_str}]{rest}"
            else:
                new_name = f"[5-UNRA {ts_str}] {rest}"
        if new_name == name:
            return
        new_path = os.path.join(dir_path, new_name)
        if os.path.exists(new_path):
            self._warn("Rename File", f"File {new_name} already exists.")
            return
        try:
            os.rename(old_path, new_path)
        except OSError as e:
            self._warn("Rename File", str(e))
            return
        self.refresh_file_list()
        for i in range(self.file_list.count()):
            it = self.file_list.item(i)
            if it.data(QtCore.Qt.UserRole) == new_name:
                self.file_list.setCurrentRow(i)
                self.file_list.scrollToItem(it)
                break

    def _apply_header_number(self, number: int) -> None:
        if self._is_directory_selected():
            return
        item = self.file_list.currentItem()
        if not item:
            return
        name = item.data(QtCore.Qt.UserRole)
        if not name or name == "header":
            return
        order = getattr(self.item, "order", None)
        if order is None:
            return
        folder = self._format_order(order)
        dir_path = os.path.join(self.repository_path, folder)
        files = [f for f in os.listdir(dir_path) if f.lower().endswith(".2do")]
        files.sort(key=lambda x: x.lower())
        header_prefix = None
        for fname in files:
            if fname.startswith(f"[{number}"):
                match = re.match(r"\[(\d-[^ \]]+)", fname)
                if match:
                    header_prefix = match.group(1)
                    break
        if not header_prefix:
            return
        old_path = os.path.join(dir_path, name)
        m = re.match(r"^\[(.*?)\]\s*(.*)$", name)
        if m:
            inner = m.group(1)
            rest_name = m.group(2)
            parts = inner.split(" ", 1)
            first_part = parts[0]
            remainder = parts[1] if len(parts) > 1 else ""
            if not re.match(r"^\d-[^ \]]+$", first_part):
                return
            timestamp = remainder.strip()
        else:
            rest_name = name
            timestamp = None
        if not timestamp:
            stat = os.stat(old_path)
            ts = getattr(stat, "st_birthtime", stat.st_mtime)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            timestamp = dt.strftime("%Y-%m-%d %H.%M.%S")
        new_inner = f"{header_prefix} {timestamp}".rstrip()
        if rest_name:
            if rest_name.startswith('.'):
                new_name = f"[{new_inner}]{rest_name}"
            else:
                new_name = f"[{new_inner}] {rest_name}"
        else:
            new_name = f"[{new_inner}]"
        new_path = os.path.join(dir_path, new_name)
        if os.path.exists(new_path):
            self._warn("Rename File", f"File {new_name} already exists.")
            return
        try:
            os.rename(old_path, new_path)
        except OSError as e:
            self._warn("Rename File", str(e))
            return
        self.refresh_file_list()
        for i in range(self.file_list.count()):
            it = self.file_list.item(i)
            if it.data(QtCore.Qt.UserRole) == new_name:
                self.file_list.setCurrentRow(i)
                self.file_list.scrollToItem(it)
                break

    def _rename_selected(self) -> None:
        if self._is_directory_selected():
            self._rename_tag_label()
        else:
            self._rename_file()

    def _rename_tag_label(self):
        if not self._is_directory_selected():
            return
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
        if not self._is_directory_selected():
            return
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

    def resizeEvent(self, event):
        self.search_input.move(self.width() - 310, self.height() - 40)
        if self.tag_search_overlay and self.tag_search_overlay.isVisible():
            self.tag_search_overlay.reposition()
        if self.remove_tag_overlay and self.remove_tag_overlay.isVisible():
            self.remove_tag_overlay.reposition()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if self.in_search_mode:
            self.exit_search_mode_select()
        super().mousePressEvent(event)

    def open_tag_search(self):
        if not self._is_directory_selected():
            return
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
        if not self._is_directory_selected():
            return
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
