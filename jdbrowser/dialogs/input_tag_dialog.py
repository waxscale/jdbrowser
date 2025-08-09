from PySide6 import QtWidgets, QtGui
from ..constants import *


class InputTagDialog(QtWidgets.QDialog):
    def __init__(self, default_order=None, default_label="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Tag")
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.order_input = QtWidgets.QLineEdit("" if default_order is None else str(default_order))
        self.order_input.setPlaceholderText("Order")
        self.order_input.setValidator(QtGui.QIntValidator())
        self.order_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        self.order_input.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout.addWidget(self.order_input)

        self.label_input = QtWidgets.QLineEdit(default_label)
        self.label_input.setPlaceholderText("Label")
        self.label_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        layout.addWidget(self.label_input)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.setStyleSheet(f'''
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
        ''')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(f'''
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
        ''')

        self.label_input.setFocus()
        self.label_input.selectAll()

    def get_values(self):
        try:
            order = int(self.order_input.text()) if self.order_input.text() else None
        except ValueError:
            order = None
        return order, self.label_input.text()

