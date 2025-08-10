from difflib import get_close_matches
from PySide6 import QtWidgets, QtCore
from .constants import BACKGROUND_COLOR, TEXT_COLOR, BORDER_COLOR, HIGHLIGHT_COLOR


class TagSearchOverlay(QtWidgets.QFrame):
    """Overlay search box with fuzzy find for tag labels."""

    tagSelected = QtCore.Signal(str)
    closed = QtCore.Signal()

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BACKGROUND_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
            }}
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: none;
                padding: 6px;
                font-family: 'FiraCode Nerd Font';
            }}
            QListWidget {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border-top: 1px solid {BORDER_COLOR};
                outline: none;
                font-family: 'FiraCode Nerd Font';
            }}
            QListWidget::item:selected {{
                background-color: {HIGHLIGHT_COLOR};
                color: {TEXT_COLOR};
            }}
            """
        )
        self.setFixedWidth(500)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QtWidgets.QLineEdit()
        layout.addWidget(self.input)
        self.list = QtWidgets.QListWidget()
        self.list.setFixedHeight(6 * 30)
        layout.addWidget(self.list)

        self.all_labels = []
        self.label_map = {}

        self.input.textChanged.connect(self.update_results)
        self.input.installEventFilter(self)

    def open(self):
        self._load_labels()
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
        cursor.execute(
            """
            SELECT label FROM state_jd_area_tags
            UNION
            SELECT label FROM state_jd_id_tags
            UNION
            SELECT label FROM state_jd_ext_tags
            UNION
            SELECT label FROM state_jd_directory_tags
            """
        )
        labels = [r[0] for r in cursor.fetchall() if r[0]]
        self.label_map = {lbl.lower(): lbl for lbl in sorted(set(labels), key=lambda s: s.lower())}
        self.all_labels = list(self.label_map.keys())

    def update_results(self, text):
        if text:
            matches_lower = get_close_matches(text.lower(), self.all_labels, n=6, cutoff=0)
            results = [self.label_map[m] for m in matches_lower]
        else:
            results = list(self.label_map.values())[:6]
        self.list.clear()
        for label in results:
            self.list.addItem(label)
        if results:
            self.list.setCurrentRow(0)

    def move_selection(self, delta):
        count = self.list.count()
        if count == 0:
            return
        row = (self.list.currentRow() + delta) % count
        self.list.setCurrentRow(row)

    def select_current(self):
        item = self.list.currentItem()
        if item:
            self.tagSelected.emit(item.text())
        self.close_overlay()

    def close_overlay(self):
        self.hide()
        self.closed.emit()

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key in (QtCore.Qt.Key_Down, QtCore.Qt.Key_J, QtCore.Qt.Key_Tab) and not (mods & QtCore.Qt.ShiftModifier):
                self.move_selection(1)
                return True
            if key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_K, QtCore.Qt.Key_Backtab) or (
                key == QtCore.Qt.Key_Tab and mods & QtCore.Qt.ShiftModifier
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
