from PySide6 import QtWidgets, QtGui, QtCore
from .constants import *

class FileItem(QtWidgets.QWidget):
    def __init__(self, tag_id, name, jd_area, jd_id, jd_ext, icon_data, parent_path, file_browser, section_idx, item_idx):
        super().__init__()
        self.tag_id = tag_id  # None for placeholder items
        self.name = name if name is not None else ""
        self.jd_area = jd_area
        self.jd_id = jd_id
        self.jd_ext = jd_ext
        self.isSelected = False
        self.isHover = False
        self.isDimmed = False
        self.file_browser = file_browser  # Reference to FileBrowser instance
        self.section_idx = section_idx  # Store section index
        self.item_idx = item_idx  # Store item index within section
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)

        # Construct display label
        if self.jd_area is not None:
            if self.jd_id is None:
                prefix = f"[{self.jd_area:02d}]"
            elif self.jd_ext is None:
                prefix = f"[{self.jd_area:02d}.{self.jd_id:02d}]"
            else:
                prefix = f"[{self.jd_area:02d}.{self.jd_id:02d}+{self.jd_ext:04d}]"
            self.display_name = f"{prefix} {self.name}" if self.name else prefix
        else:
            self.display_name = self.name

        # Fix vertical size policy
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        # Icon: Load from database BLOB or use slate placeholder
        if icon_data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                self.icon = QtWidgets.QLabel()
                rounded_pixmap = QtGui.QPixmap(240, 150)
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled_pixmap = pixmap.scaled(240, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.icon.setPixmap(rounded_pixmap)
                self.icon.setFixedSize(240, 150)
                self.icon.setStyleSheet('background-color: transparent;')
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(240, 150)
                self.icon.setStyleSheet(f'background-color: {SLATE_COLOR}; border-radius: 10px;')
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(240, 150)
            self.icon.setStyleSheet(f'background-color: {SLATE_COLOR}; border-radius: 10px;')
        self.icon.setAutoFillBackground(True)
        layout.addWidget(self.icon, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Label (single line, empty for placeholders)
        self.label = QtWidgets.QLabel(self.display_name)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.label.setFixedWidth(240)
        self.label.setWordWrap(False)
        self.label.setStyleSheet(f'color: {TEXT_COLOR};')
        self.label.setAutoFillBackground(True)
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Fixed height: icon + single line label + spacings and margins
        fm = self.label.fontMetrics()
        label_height = fm.height()
        spacing = layout.spacing()
        margins = layout.contentsMargins()
        total_height = 150 + label_height + spacing + margins.top() + margins.bottom()
        self.setFixedHeight(total_height)

        self.updateStyle()

    def updateStyle(self):
        # Prioritize isSelected over isHover for background
        if self.isSelected:
            bg = HIGHLIGHT_COLOR
        elif self.isHover:
            bg = HOVER_COLOR
        else:
            bg = 'transparent'
        # Apply dimming for non-matching items using QGraphicsOpacityEffect
        opacity = 0.4 if self.isDimmed else 1.0
        icon_effect = QtWidgets.QGraphicsOpacityEffect(self.icon)
        icon_effect.setOpacity(opacity)
        self.icon.setGraphicsEffect(icon_effect)
        label_effect = QtWidgets.QGraphicsOpacityEffect(self.label)
        label_effect.setOpacity(opacity)
        self.label.setGraphicsEffect(label_effect)
        icon_style = f'background-color: {SLATE_COLOR}; border-radius: 10px;' if isinstance(self.icon, QtWidgets.QFrame) else 'background-color: transparent;'
        self.setStyleSheet(f'background-color: {bg}; border-radius: 10px;')
        self.icon.setStyleSheet(icon_style)
        self.label.setStyleSheet(f'color: {TEXT_COLOR};')

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

    def mousePressEvent(self, event):
        """Select this item when clicked, including placeholders."""
        if event.button() == QtCore.Qt.LeftButton and self.file_browser:
            self.file_browser.set_selection(self.section_idx, self.item_idx)
        super().mousePressEvent(event)