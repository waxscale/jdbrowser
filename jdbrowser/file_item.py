from PySide6 import QtWidgets, QtGui, QtCore
from .constants import (
    SURFACE_COLOR,
    SURFACE2_COLOR,
    TEXT_COLOR,
    MUTED_COLOR,
    PLACEHOLDER_COLOR,
    PLACEHOLDER_TEXT_COLOR,
    SLATE_COLOR,
)

class FileItem(QtWidgets.QWidget):
    def __init__(self, tag_id, name, jd_area, jd_id, jd_ext, icon_data, page, section_idx, item_idx):
        super().__init__()
        self.tag_id = tag_id  # None for placeholder items
        self.name = name if name is not None else ""
        self.jd_area = jd_area
        self.jd_id = jd_id
        self.jd_ext = jd_ext
        self.isSelected = False
        self.isHover = False
        self.isDimmed = False
        self.page = page  # Reference to the parent page instance
        self.section_idx = section_idx  # Store section index
        self.item_idx = item_idx  # Store item index within section
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)
        self.setAcceptDrops(True)
        self.drag_start_pos = None

        # Construct display label
        if self.jd_area is not None:
            if self.jd_id is None:
                self.prefix = f"[{self.jd_area:02d}]"
            elif self.jd_ext is None:
                self.prefix = f"[{self.jd_area:02d}.{self.jd_id:02d}]"
            else:
                self.prefix = f"[{self.jd_area:02d}.{self.jd_id:02d}+{self.jd_ext:04d}]"
        else:
            self.prefix = ""
        self.display_name = self.name or ""

        # Fix vertical size policy
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(2, 2, 2, 2)

        # Container box for image with drop shadow and border
        self.box = QtWidgets.QFrame()
        self.box.setFixedSize(120, 75)
        self.box.setStyleSheet(
            f"background-color: {SURFACE_COLOR}; border: 1px solid {SURFACE2_COLOR}; border-radius: 16px;"
        )
        box_layout = QtWidgets.QVBoxLayout(self.box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Icon: Load from database BLOB or use slate/placeholder color
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
                scaled_pixmap = pixmap.scaled(
                    120,
                    75,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.icon.setPixmap(rounded_pixmap)
                self.icon.setFixedSize(120, 75)
                self.icon.setStyleSheet("background-color: transparent;")
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(120, 75)
                color = PLACEHOLDER_COLOR if self.tag_id is None else SLATE_COLOR
                self.icon.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(120, 75)
            color = PLACEHOLDER_COLOR if self.tag_id is None else SLATE_COLOR
            self.icon.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        self.icon.setAutoFillBackground(True)
        box_layout.addWidget(self.icon)

        shadow = QtWidgets.QGraphicsDropShadowEffect(self.box)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 6)
        shadow.setColor(QtGui.QColor(0, 0, 0, 153))
        self.box.setGraphicsEffect(shadow)

        layout.addWidget(self.box, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Label (single line, empty for placeholders)
        self.label = QtWidgets.QLabel(self.display_name)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.label.setFixedWidth(120)
        self.label.setWordWrap(False)
        font = self.label.font()
        font.setPointSize(int(font.pointSize() * 0.9))
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {MUTED_COLOR};")
        self.label.setAutoFillBackground(True)
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.updateLabel(False)

        # Fixed height: icon + single line label + spacings and margins
        fm = self.label.fontMetrics()
        label_height = fm.height()
        spacing = layout.spacing()
        margins = layout.contentsMargins()
        total_height = 75 + label_height + spacing + margins.top() + margins.bottom()
        self.setFixedHeight(total_height)

        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
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
        # Prioritize isSelected over isHover for background
        if self.isSelected:
            box_style = (
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(125,207,255,0.12), stop:1 "
                f"{SURFACE2_COLOR}); border:1px solid rgba(125,207,255,0.6);"
            )
            label_color = TEXT_COLOR
        elif self.isHover:
            box_style = (
                f"background-color: {SURFACE_COLOR}; border:1px solid rgba(125,207,255,0.55);"
            )
            label_color = TEXT_COLOR
        else:
            box_style = (
                f"background-color: {SURFACE_COLOR}; border:1px solid {SURFACE2_COLOR};"
            )
            label_color = PLACEHOLDER_TEXT_COLOR if self.tag_id is None else MUTED_COLOR

        opacity = 0.4 if self.isDimmed else 1.0
        self.opacity_effect.setOpacity(opacity)
        self.box.setStyleSheet(box_style + " border-radius: 16px;")
        self.label.setStyleSheet(f"color: {label_color};")

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
        """Select on left-click; right-click edits or creates a tag."""
        if self.page:
            if event.button() == QtCore.Qt.LeftButton:
                self.drag_start_pos = event.position().toPoint()
                self.page.set_selection(self.section_idx, self.item_idx)
            elif event.button() == QtCore.Qt.RightButton:
                self.page.set_selection(self.section_idx, self.item_idx)
                self.page._edit_tag_label_with_icon()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self.tag_id is None
            or not (event.buttons() & QtCore.Qt.LeftButton)
            or self.drag_start_pos is None
        ):
            super().mouseMoveEvent(event)
            return
        if (
            event.position().toPoint() - self.drag_start_pos
        ).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return
        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        mime.setText(self.tag_id)
        drag.setMimeData(mime)

        pixmap = self.grab()
        if not pixmap.isNull():
            transparent = QtGui.QPixmap(pixmap.size())
            transparent.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(transparent)
            painter.setOpacity(0.6)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            drag.setPixmap(transparent)
            drag.setHotSpot(self.drag_start_pos)

        drag.exec(QtCore.Qt.MoveAction)
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText() and self.page:
            source_tag_id = event.mimeData().text()
            self.page.handle_item_drop(source_tag_id, self)
            event.acceptProposedAction()
        else:
            event.ignore()

