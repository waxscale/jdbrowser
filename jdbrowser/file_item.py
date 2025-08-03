from PySide6 import QtWidgets, QtGui, QtCore
from .constants import *


class FileItem(QtWidgets.QWidget):
    """Simplified widget representing a tag item."""

    def __init__(self, tag_id, name, jd_id, icon_data, file_browser, index):
        super().__init__()
        self.tag_id = tag_id
        self.name = name or ""
        self.jd_id = jd_id
        self.file_browser = file_browser
        self.index = index
        self.isSelected = False
        self.isHover = False
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)

        self.prefix = f"[{jd_id:02d}]" if jd_id is not None else ""
        self.display_name = self.name or ""

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        if icon_data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                self.icon = QtWidgets.QLabel()
                rounded = QtGui.QPixmap(120, 75)
                rounded.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 120, 75, 5, 5)
                painter.setClipPath(path)
                scaled = pixmap.scaled(
                    120,
                    75,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                self.icon.setPixmap(rounded)
                self.icon.setFixedSize(120, 75)
                self.icon.setStyleSheet("background-color: transparent;")
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(120, 75)
                self.icon.setStyleSheet(
                    f"background-color: {SLATE_COLOR}; border-radius: 5px;"
                )
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(120, 75)
            self.icon.setStyleSheet(
                f"background-color: {SLATE_COLOR}; border-radius: 5px;"
            )
        self.icon.setAutoFillBackground(True)
        layout.addWidget(self.icon, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.label = QtWidgets.QLabel(self.display_name)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.label.setFixedWidth(120)
        self.label.setWordWrap(False)
        font = self.label.font()
        font.setPointSize(int(font.pointSize() * 0.9))
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.updateLabel(False)

        fm = self.label.fontMetrics()
        total_height = (
            75
            + fm.height()
            + layout.spacing()
            + layout.contentsMargins().top()
            + layout.contentsMargins().bottom()
        )
        self.setFixedHeight(total_height)
        self.updateStyle()

    def updateLabel(self, show_prefix: bool) -> None:
        text = self.prefix if show_prefix else self.name
        self.display_name = text
        self.label.setText(text)

    def updateStyle(self) -> None:
        if self.isSelected:
            bg = HIGHLIGHT_COLOR
        elif self.isHover:
            bg = HOVER_COLOR
        else:
            bg = "transparent"
        self.setStyleSheet(f"background-color: {bg}; border-radius: 5px;")

    def enterEvent(self, event):
        self.isHover = True
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.isHover = False
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.tag_id and self.file_browser:
            self.file_browser.enter_directory(self.tag_id)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if (
            self.file_browser
            and event.button() == QtCore.Qt.RightButton
            and self.tag_id
        ):
            self.file_browser._edit_tag(self.tag_id)
        super().mousePressEvent(event)

