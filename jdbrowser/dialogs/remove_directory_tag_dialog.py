from PySide6 import QtWidgets
from ..constants import *

class RemoveDirectoryTagDialog(QtWidgets.QDialog):
    def __init__(self, directory_name, tag_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Remove")
        self.setFixedWidth(600)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        message = (
            f"Are you sure you want to remove the tag '{tag_name}' from the directory '{directory_name}'?"
        )
        self.message = QtWidgets.QLabel(message)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(f"color: {TEXT_COLOR};")
        self.message.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        layout.addWidget(self.message)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.setStyleSheet(
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
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        self.adjustSize()

