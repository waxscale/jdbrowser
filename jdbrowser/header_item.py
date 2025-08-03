from PySide6 import QtWidgets, QtCore
from .constants import BUTTON_COLOR

class HeaderItem(QtWidgets.QLabel):
    def __init__(self, header_id, jd_area, jd_id, jd_ext, label, file_browser, section_idx, text):
        super().__init__(text)
        self.header_id = header_id
        self.jd_area = jd_area
        self.jd_id = jd_id
        self.jd_ext = jd_ext
        self.label = label
        self.file_browser = file_browser
        self.section_idx = section_idx
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        font = self.font()
        font.setPointSize(int(font.pointSize() * 0.75))
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(f'background-color: {BUTTON_COLOR}; color: black; padding-left:5px; padding-right:5px;')
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        fm = self.fontMetrics()
        self.setFixedHeight(fm.height() + 3)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton and self.file_browser:
            self.file_browser._edit_header(self)
        super().mousePressEvent(event)
