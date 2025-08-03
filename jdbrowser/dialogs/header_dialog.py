from PySide6 import QtWidgets, QtGui
from ..constants import *


class HeaderDialog(QtWidgets.QDialog):
    """Dialog for creating or editing headers."""

    def __init__(
        self,
        order: int | None = 0,
        label: str = "HEADER",
        show_delete: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Section Header")
        self.delete_pressed = False
        self.setFixedWidth(300)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.order_input = QtWidgets.QLineEdit("" if order is None else str(order))
        self.order_input.setValidator(QtGui.QIntValidator())
        self.order_input.setPlaceholderText("order")
        self.order_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            """
        )
        layout.addWidget(self.order_input)

        self.label_input = QtWidgets.QLineEdit(label)
        self.label_input.setPlaceholderText("Label")
        self.label_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            """
        )
        layout.addWidget(self.label_input)

        btn_row = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("OK")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        for b in (ok_btn, cancel_btn):
            b.setStyleSheet(
                f"""
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
                """
            )
            b.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
            )
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        if show_delete:
            self.delete_button = QtWidgets.QPushButton("Delete")
            self.delete_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {DELETE_BUTTON_COLOR};
                    color: black;
                    border: none;
                    padding: 5px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: #ff8ba7;
                }}
                """
            )
            self.delete_button.clicked.connect(self._on_delete)
            self.delete_button.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
            )
            layout.addWidget(self.delete_button)

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
            """
        )

        self.order_input.setFocus()
        self.order_input.selectAll()

    def _on_delete(self):
        self.delete_pressed = True
        self.accept()

    def get_values(self):
        try:
            order_val = int(self.order_input.text()) if self.order_input.text() else None
        except ValueError:
            order_val = None
        return order_val, self.label_input.text()

