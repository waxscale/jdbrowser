from PySide6 import QtWidgets, QtGui
from ..constants import *

class InputTagDialog(QtWidgets.QDialog):
    def __init__(self, default_jd_area=None, default_jd_id=None, default_jd_ext=None, default_label="", level=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Tag")
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(5)
        row.setContentsMargins(0, 0, 0, 0)
        self.jd_area_input = QtWidgets.QLineEdit("" if default_jd_area is None else str(default_jd_area))
        self.jd_id_input = QtWidgets.QLineEdit("" if default_jd_id is None else str(default_jd_id))
        self.jd_ext_input = QtWidgets.QLineEdit("" if default_jd_ext is None else str(default_jd_ext))
        for w, placeholder in (
            (self.jd_area_input, "jd_area"),
            (self.jd_id_input, "jd_id"),
            (self.jd_ext_input, "jd_ext"),
        ):
            w.setPlaceholderText(placeholder)
            w.setValidator(QtGui.QIntValidator())
            w.setStyleSheet(f'''
                QLineEdit {{
                    background-color: {BACKGROUND_COLOR};
                    color: {TEXT_COLOR};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 5px;
                    padding: 5px;
                }}
            ''')
            w.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        if level == 0:
            row.addWidget(self.jd_area_input, 1)
        elif level == 1:
            row.addWidget(self.jd_area_input, 1)
            row.addWidget(self.jd_id_input, 1)
        else:
            row.addWidget(self.jd_area_input, 1)
            row.addWidget(self.jd_id_input, 1)
            row.addWidget(self.jd_ext_input, 1)
        layout.addLayout(row)

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

    def get_values(self):
        try:
            jd_area = int(self.jd_area_input.text()) if self.jd_area_input.text() else None
            jd_id = int(self.jd_id_input.text()) if self.jd_id_input.text() else None
            jd_ext = int(self.jd_ext_input.text()) if self.jd_ext_input.text() else None
        except ValueError:
            jd_area, jd_id, jd_ext = None, None, None
        return jd_area, jd_id, jd_ext, self.label_input.text()

