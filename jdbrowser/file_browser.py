import os
from PySide6 import QtWidgets, QtCore, QtGui

from .database import setup_database, create_tag, create_header
from .dialogs.input_tag_dialog import InputTagDialog
from .dialogs.header_dialog import HeaderDialog


class FileBrowser(QtWidgets.QWidget):
    """Minimal browser displaying items in a three level hierarchy."""

    def __init__(self, start_id: str | None = None) -> None:
        super().__init__()
        db_path = os.path.join(os.getcwd(), "jdbrowser.sqlite")
        self.conn = setup_database(db_path)
        self.current_parent: str | None = None
        self.parent_stack: list[str] = []
        self.order_stack: list[int] = []

        layout = QtWidgets.QVBoxLayout(self)
        self.list = QtWidgets.QListWidget()
        self.list.itemActivated.connect(self._enter_item)
        layout.addWidget(self.list)
        self.list.setFocus()

        # Shortcuts work regardless of which widget currently has focus
        QtGui.QShortcut(QtGui.QKeySequence("q"), self, activated=self.close)
        QtGui.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Backspace), self, activated=self._go_up
        )
        QtGui.QShortcut(QtGui.QKeySequence("t"), self, activated=self._new_tag)
        QtGui.QShortcut(QtGui.QKeySequence("h"), self, activated=self._new_header)

        self._refresh()

    # ------------------------------------------------------------------
    def _build_prefix(self, item_order: int) -> str:
        if not self.order_stack:
            return f"[{item_order:02d}]"
        if len(self.order_stack) == 1:
            return f"[{self.order_stack[0]:02d}.{item_order:02d}]"
        return f"[{self.order_stack[0]:02d}.{self.order_stack[1]:02d}+{item_order:04d}]"

    def _refresh(self) -> None:
        self.list.clear()
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT 'header' AS kind, header_id AS obj_id, item_order, label
            FROM state_headers WHERE parent_id IS ?
            UNION ALL
            SELECT 'tag', tag_id, item_order, label
            FROM state_tags WHERE parent_id IS ?
            ORDER BY item_order
            """,
            (self.current_parent, self.current_parent),
        )
        for kind, obj_id, order, label in cur.fetchall():
            prefix = self._build_prefix(order)
            item = QtWidgets.QListWidgetItem(f"{prefix} {label}")
            item.setData(QtCore.Qt.UserRole, (kind, obj_id, order))
            self.list.addItem(item)

    # ------------------------------------------------------------------
    def _enter_item(self, item: QtWidgets.QListWidgetItem) -> None:
        kind, obj_id, order = item.data(QtCore.Qt.UserRole)
        if len(self.parent_stack) >= 2:
            return
        self.parent_stack.append(obj_id)
        self.order_stack.append(order)
        self.current_parent = obj_id
        self._refresh()

    def _go_up(self) -> None:
        if not self.parent_stack:
            return
        self.parent_stack.pop()
        self.order_stack.pop()
        self.current_parent = self.parent_stack[-1] if self.parent_stack else None
        self._refresh()

    def _next_order(self) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT MAX(item_order) FROM state_headers WHERE parent_id IS ?",
            (self.current_parent,),
        )
        max_header = cur.fetchone()[0] or 0
        cur.execute(
            "SELECT MAX(item_order) FROM state_tags WHERE parent_id IS ?",
            (self.current_parent,),
        )
        max_tag = cur.fetchone()[0] or 0
        return max(max_header, max_tag) + 1

    def _new_tag(self) -> None:
        dlg = InputTagDialog(self._next_order(), parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            order, label = dlg.get_values()
            if order is not None and label:
                create_tag(self.conn, self.current_parent, order, label)
                self._refresh()

    def _new_header(self) -> None:
        dlg = HeaderDialog(order=self._next_order(), label="", parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            order, label = dlg.get_values()
            if not dlg.delete_pressed and order is not None and label:
                create_header(self.conn, self.current_parent, order, label)
                self._refresh()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        settings = QtCore.QSettings("xAI", "jdbrowser")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
        super().closeEvent(event)

