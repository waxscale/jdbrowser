from difflib import get_close_matches
from PySide6 import QtWidgets, QtCore, QtGui
from .constants import (
    TEXT_COLOR,
    TAG_COLOR,
    HIGHLIGHT_COLOR,
    HOVER_COLOR,
    SLATE_COLOR,
)


class TagSearchOverlay(QtWidgets.QFrame):
    """Overlay search box with fuzzy find for tag labels."""

    tagSelected = QtCore.Signal(str)
    closed = QtCore.Signal()

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFixedWidth(600)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self._input_style_core = (
            f"background-color: {SLATE_COLOR};"
            f" color: {TEXT_COLOR};"
            f" border: 2px solid {HIGHLIGHT_COLOR};"
            " border-top-left-radius: 10px;"
            " border-top-right-radius: 10px;"
            " padding: 12px;"
            " font-family: 'FiraCode Nerd Font';"
            " font-size: 24px;"
        )
        self.input_style_no_results = (
            "QLineEdit {"
            + self._input_style_core
            + " border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;}"
        )
        self.input_style_with_results = (
            "QLineEdit {"
            + self._input_style_core
            + " border-bottom: none; border-bottom-left-radius: 0; border-bottom-right-radius: 0;}"
        )

        self.list_style = f"""
            QListWidget {{
                background-color: {SLATE_COLOR};
                color: {TEXT_COLOR};
                border: 2px solid {HIGHLIGHT_COLOR};
                border-top: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                outline: none;
                font-family: 'FiraCode Nerd Font';
                font-size: 18px;
            }}
            QListWidget::item {{
                padding: 8px 4px;
            }}
            QListWidget::item:hover {{
                background-color: {HOVER_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {TAG_COLOR};
                color: {TEXT_COLOR};
            }}
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QtWidgets.QLineEdit()
        self.input.setStyleSheet(self.input_style_no_results)
        layout.addWidget(self.input)

        self.list = QtWidgets.QListWidget()
        self.list.setStyleSheet(self.list_style)
        self.list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.hide()
        self.list.itemClicked.connect(self._item_clicked)
        layout.addWidget(self.list)

        self.item_height = QtGui.QFontMetrics(QtGui.QFont("FiraCode Nerd Font", 18)).height() + 16
        self.max_results = 5

        self.all_labels = []
        self.label_map = {}

        self.input.textChanged.connect(self.update_results)
        self.input.installEventFilter(self)

    def open(self, label_rows=None):
        if label_rows is None:
            self._load_labels()
        else:
            self._set_labels(label_rows)
        self.input.clear()
        self.update_results("")
        self.reposition()
        self.show()
        self.input.setFocus()

    def reposition(self):
        parent = self.parent()
        if parent:
            x = (parent.width() - self.width()) // 2
            y = 80
            self.move(x, y)

    def _load_labels(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT tag_id, label FROM state_jd_ext_tags")
        rows = [(r[0], r[1]) for r in cursor.fetchall() if r[1]]
        self._set_labels(rows)

    def _set_labels(self, rows):
        self.label_map = {
            lbl.lower(): (lbl, tag_id)
            for tag_id, lbl in sorted(rows, key=lambda s: s[1].lower())
        }
        self.all_labels = list(self.label_map.keys())

    def update_results(self, text):
        if text:
            matches_lower = get_close_matches(
                text.lower(), self.all_labels, n=self.max_results, cutoff=0
            )
            results = [self.label_map[m] for m in matches_lower]
        else:
            results = list(self.label_map.values())[: self.max_results]

        self.list.clear()
        if results:
            for label, tag_id in results:
                item = QtWidgets.QListWidgetItem(label)
                item.setData(QtCore.Qt.UserRole, tag_id)
                self.list.addItem(item)
            count = len(results)
            self.list.setFixedHeight(min(count, self.max_results) * self.item_height)
            self.list.show()
            self.input.setStyleSheet(self.input_style_with_results)
            self.list.setCurrentRow(0)
        else:
            self.list.hide()
            self.input.setStyleSheet(self.input_style_no_results)
        self.adjustSize()

    def move_selection(self, delta):
        count = self.list.count()
        if count == 0:
            return
        row = (self.list.currentRow() + delta) % count
        self.list.setCurrentRow(row)

    def select_current(self):
        item = self.list.currentItem()
        if item:
            self.tagSelected.emit(item.data(QtCore.Qt.UserRole))
        self.close_overlay()

    def _item_clicked(self, item):
        if item:
            self.tagSelected.emit(item.data(QtCore.Qt.UserRole))
        self.close_overlay()

    def close_overlay(self):
        self.hide()
        self.closed.emit()

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if (
                key in (QtCore.Qt.Key_Down, QtCore.Qt.Key_Tab) and not (mods & QtCore.Qt.ShiftModifier)
            ) or (key == QtCore.Qt.Key_J and mods & QtCore.Qt.ControlModifier):
                self.move_selection(1)
                return True
            if (
                key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Backtab)
                or (key == QtCore.Qt.Key_Tab and mods & QtCore.Qt.ShiftModifier)
                or (key == QtCore.Qt.Key_K and mods & QtCore.Qt.ControlModifier)
            ):
                self.move_selection(-1)
                return True
            if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                self.select_current()
                return True
            if key == QtCore.Qt.Key_Escape:
                self.close_overlay()
                return True
        return super().eventFilter(obj, event)
