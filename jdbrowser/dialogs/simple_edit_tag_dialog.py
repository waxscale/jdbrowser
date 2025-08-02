from PySide6 import QtWidgets
from ..constants import *

class SimpleEditTagDialog(QtWidgets.QDialog):
    def __init__(self, current_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Tag")
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Label input
        self.label_input = QtWidgets.QLineEdit(current_label)
        self.label_input.setPlaceholderText("Enter tag label")
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

        # Buttons
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

        self.setStyleSheet(f'background-color: {BACKGROUND_COLOR};')

    def get_label(self):
        return self.label_input.text()