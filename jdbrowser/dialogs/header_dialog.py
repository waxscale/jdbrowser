from PySide6 import QtWidgets, QtGui
from ..constants import *

class HeaderDialog(QtWidgets.QDialog):
    def __init__(self, jd_area=0, jd_id=None, jd_ext=None, label="HEADER", show_delete=False, parent=None, level=0):
        super().__init__(parent)
        self.setWindowTitle("Section Header")
        self.delete_pressed = False
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(5)
        row.setContentsMargins(0, 0, 0, 0)
        self.jd_area_input = QtWidgets.QLineEdit(str(jd_area))
        self.jd_area_input.setValidator(QtGui.QIntValidator())
        self.jd_area_input.setPlaceholderText("jd_area")
        self.jd_id_input = QtWidgets.QLineEdit("" if jd_id is None else str(jd_id))
        self.jd_id_input.setValidator(QtGui.QIntValidator())
        self.jd_id_input.setPlaceholderText("jd_id")
        self.jd_ext_input = QtWidgets.QLineEdit("" if jd_ext is None else str(jd_ext))
        self.jd_ext_input.setValidator(QtGui.QIntValidator())
        self.jd_ext_input.setPlaceholderText("jd_ext")
        for w in (self.jd_area_input, self.jd_id_input, self.jd_ext_input):
            w.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {BACKGROUND_COLOR};
                    color: {TEXT_COLOR};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 5px;
                    padding: 5px;
                }}
            """)
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

        self.label_input = QtWidgets.QLineEdit(label)
        self.label_input.setPlaceholderText("Label")
        self.label_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        layout.addWidget(self.label_input)

        btn_row = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("OK")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        for b in (ok_btn, cancel_btn):
            b.setStyleSheet(f"""
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
            """)
            b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        if show_delete:
            self.delete_button = QtWidgets.QPushButton("Delete")
            self.delete_button.setStyleSheet(f"""
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
            """)
            self.delete_button.clicked.connect(self._on_delete)
            self.delete_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            layout.addWidget(self.delete_button)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
        """)
        if level == 0:
            self.jd_area_input.setFocus()
            self.jd_area_input.selectAll()
        elif level == 1:
            self.jd_id_input.setFocus()
            self.jd_id_input.selectAll()
        else:
            self.jd_ext_input.setFocus()
            self.jd_ext_input.selectAll()

    def _on_delete(self):
        self.delete_pressed = True
        self.accept()

    def get_values(self):
        try:
            jd_area = int(self.jd_area_input.text()) if self.jd_area_input.text() else None
            jd_id = int(self.jd_id_input.text()) if self.jd_id_input.text() else None
            jd_ext = int(self.jd_ext_input.text()) if self.jd_ext_input.text() else None
        except ValueError:
            jd_area, jd_id, jd_ext = None, None, None
        return jd_area, jd_id, jd_ext, self.label_input.text()

