from PySide6 import QtCore, QtWidgets


class FlowLayout(QtWidgets.QLayout):
    """A simple flow layout that arranges child widgets like words on a page."""

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.itemList = []
        if parent is not None:
            parent.setLayout(self)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing if spacing >= 0 else 5)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QtCore.QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        """Return the minimum bounding box for all items.

        Using ``item.minimumSize()`` results in zero height for widgets like
        ``QPushButton`` which do not have an explicit minimum set, causing the
        entire layout to collapse.  ``sizeHint`` reflects the implicit size Qt
        would like to give the widget, so we expand the accumulated rectangle
        using that instead to ensure our tag pills are visible.
        """
        size = QtCore.QSize()
        for item in self.itemList:
            size = size.expandedTo(item.sizeHint())
        margins = self.contentsMargins()
        size += QtCore.QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )
        return size

    def doLayout(self, rect, testOnly):
        margins = self.contentsMargins()
        x = rect.x() + margins.left()
        y = rect.y() + margins.top()
        lineHeight = 0
        right_limit = rect.right() - margins.right()
        for item in self.itemList:
            widget = item.widget()
            spaceX = self.spacing()
            spaceY = self.spacing()
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > right_limit and lineHeight > 0:
                x = rect.x() + margins.left()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        return y + lineHeight + margins.bottom() - rect.y()
