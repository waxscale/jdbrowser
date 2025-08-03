from PySide6 import QtWidgets, QtGui, QtCore
from .constants import *


class FileItem(QtWidgets.QWidget):
    """Widget representing a tag in the browser."""

    def __init__(
        self,
        tag_id,
        name,
        prefix,
        parent_id,
        item_order,
        icon_data,
        file_browser,
        section_idx,
        item_idx,
    ):
        super().__init__()
        self.tag_id = tag_id
        self.name = name or ""
        self.prefix = prefix or ""
        self.parent_id = parent_id
        self.item_order = item_order
        self.isSelected = False
        self.isHover = False
        self.isDimmed = False
        self.file_browser = file_browser
        self.section_idx = section_idx
        self.item_idx = item_idx
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)
        self.setAcceptDrops(True)
        self.drag_start_pos = None

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
                rounded_pixmap = QtGui.QPixmap(120, 75)
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 120, 75, 5, 5)
                painter.setClipPath(path)
                scaled_pixmap = pixmap.scaled(120, 75, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.icon.setPixmap(rounded_pixmap)
                self.icon.setFixedSize(120, 75)
                self.icon.setStyleSheet('background-color: transparent;')
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(120, 75)
                color = PLACEHOLDER_COLOR if self.tag_id is None else SLATE_COLOR
                self.icon.setStyleSheet(f'background-color: {color}; border-radius: 5px;')
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(120, 75)
            color = PLACEHOLDER_COLOR if self.tag_id is None else SLATE_COLOR
            self.icon.setStyleSheet(f'background-color: {color}; border-radius: 5px;')
        self.icon.setAutoFillBackground(True)
        layout.addWidget(self.icon, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.label = QtWidgets.QLabel(self.display_name)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.label.setFixedWidth(120)
        self.label.setWordWrap(False)
        font = self.label.font()
        font.setPointSize(int(font.pointSize() * 0.9))
        self.label.setFont(font)
        self.label.setStyleSheet(f'color: {TEXT_COLOR};')
        self.label.setAutoFillBackground(True)
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.updateLabel(False)

        fm = self.label.fontMetrics()
        total_height = 75 + fm.height() + layout.spacing() + layout.contentsMargins().top() + layout.contentsMargins().bottom()
        self.setFixedHeight(total_height)

        self.updateStyle()

    def updateLabel(self, show_prefix):
        if self.tag_id is None:
            text = self.prefix if show_prefix else ""
        else:
            if self.name == "":
                text = self.prefix if show_prefix else ""
            else:
                text = self.prefix if show_prefix else self.name
        self.display_name = text
        self.label.setText(text)

    def updateStyle(self):
        if self.isSelected:
            bg = HIGHLIGHT_COLOR
        elif self.isHover:
            bg = HOVER_COLOR
        else:
            bg = 'transparent'
        opacity = 0.4 if self.isDimmed else 1.0
        icon_effect = QtWidgets.QGraphicsOpacityEffect(self.icon)
        icon_effect.setOpacity(opacity)
        self.icon.setGraphicsEffect(icon_effect)
        label_effect = QtWidgets.QGraphicsOpacityEffect(self.label)
        label_effect.setOpacity(opacity)
        self.label.setGraphicsEffect(label_effect)
        self.setStyleSheet(f'background-color: {bg}; border-radius: 5px;')

