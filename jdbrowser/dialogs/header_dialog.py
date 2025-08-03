from PySide6 import QtWidgets, QtGui
from ..constants import *


class HeaderDialog(QtWidgets.QDialog):
    def __init__(
        self,
        jd_area=0,
        jd_id=None,
        jd_ext=None,
        label="HEADER",
        show_delete=False,
        parent=None,
        level=0,
    ):
        super().__init__(parent)
        self.setWindowTitle("Section Header")
        self.delete_pressed = False
        self.setFixedWidth(300)

        # Store the incoming values so they can be returned for levels that hide
        # those fields.
        self.level = level
        self.jd_area = jd_area
        self.jd_id = jd_id
        self.jd_ext = jd_ext

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Single prefix input depending on the level being edited. The width of
        # the field is set to expand to 100% of the dialog width.
        if level == 0:
            prefix_val = jd_area
            placeholder = "jd_area"
        elif level == 1:
            prefix_val = jd_id
            placeholder = "jd_id"
        else:
            prefix_val = jd_ext
            placeholder = "jd_ext"

        self.prefix_input = QtWidgets.QLineEdit(
            "" if prefix_val is None else str(prefix_val)
        )
        self.prefix_input.setValidator(QtGui.QIntValidator())
        self.prefix_input.setPlaceholderText(placeholder)
        self.prefix_input.setStyleSheet(
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
        self.prefix_input.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        layout.addWidget(self.prefix_input)

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

        self.prefix_input.setFocus()
        self.prefix_input.selectAll()

    def _on_delete(self):
        self.delete_pressed = True
        self.accept()

    def get_values(self):
        try:
            prefix_val = (
                int(self.prefix_input.text()) if self.prefix_input.text() else None
            )
        except ValueError:
            prefix_val = None

        jd_area, jd_id, jd_ext = self.jd_area, self.jd_id, self.jd_ext

        if self.level == 0:
            jd_area = prefix_val
        elif self.level == 1:
            jd_id = prefix_val
        else:
            jd_ext = prefix_val

        return jd_area, jd_id, jd_ext, self.label_input.text()

