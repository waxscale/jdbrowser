import os
from PySide6 import QtWidgets, QtCore
from .database import setup_database, create_tag, create_header


class FileBrowser(QtWidgets.QWidget):
    """Very small browser displaying items in a three level hierarchy."""

    def __init__(self, start_id=None):
        super().__init__()
        db_path = os.path.join(os.getcwd(), "jdbrowser.sqlite")
        self.conn = setup_database(db_path)
        self.current_parent = None
        self.parent_stack = []
        self.order_stack = []

        layout = QtWidgets.QVBoxLayout(self)
        self.list = QtWidgets.QListWidget()
        self.list.itemActivated.connect(self._enter_item)
        layout.addWidget(self.list)

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
            "SELECT header_id, parent_id, item_order, label FROM state_headers WHERE parent_id IS ? ORDER BY item_order",
            (self.current_parent,),
        )
        for header_id, parent_id, order, label in cur.fetchall():
            prefix = self._build_prefix(order)
            item = QtWidgets.QListWidgetItem(f"{prefix} {label}")
            item.setData(QtCore.Qt.UserRole, ("header", header_id, order))
            self.list.addItem(item)

        cur.execute(
            "SELECT tag_id, parent_id, item_order, label FROM state_tags WHERE parent_id IS ? ORDER BY item_order",
            (self.current_parent,),
        )
        for tag_id, parent_id, order, label in cur.fetchall():
            prefix = self._build_prefix(order)
            item = QtWidgets.QListWidgetItem(f"{prefix} {label}")
            item.setData(QtCore.Qt.UserRole, ("tag", tag_id, order))
            self.list.addItem(item)

    # ------------------------------------------------------------------
    def _enter_item(self, item: QtWidgets.QListWidgetItem):
        kind, obj_id, order = item.data(QtCore.Qt.UserRole)
        if len(self.parent_stack) >= 2:
            return
        self.parent_stack.append(obj_id)
        self.order_stack.append(order)
        self.current_parent = obj_id
        self._refresh()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Backspace and self.parent_stack:
            self.parent_stack.pop()
            self.order_stack.pop()
            self.current_parent = self.parent_stack[-1] if self.parent_stack else None
            self._refresh()
        else:
            super().keyPressEvent(event)

