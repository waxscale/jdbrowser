import sys
import signal
import re
from typing import Union

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QSettings, QPoint, QSize
from PySide6.QtGui import QFont

import jdbrowser
from jdbrowser.jd_area_page import JdAreaPage
from jdbrowser.jd_id_page import JdIdPage
from jdbrowser.jd_ext_page import JdExtPage

# Allow Ctrl+C (SIGINT) to quit the Qt application
signal.signal(signal.SIGINT, lambda sig, frame: QApplication.quit())

if __name__ == '__main__':
    start_id = sys.argv[1] if len(sys.argv) > 1 else None
    if start_id and not re.match(r'^\d{2}(\.\d{2})?$', start_id):
        print('Error:', start_id, 'is not a valid id. Use XX or XX.YY.')
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setFont(QFont('FiraCode Nerd Font'))

    class MainWindow(QMainWindow):
        def closeEvent(self, event):
            settings = QSettings("xAI", "jdbrowser")
            settings.setValue("pos", self.pos())
            settings.setValue("size", self.size())
            super().closeEvent(event)

    main_window = MainWindow()
    main_window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    jdbrowser.main_window = main_window

    jdbrowser.current_page = JdAreaPage()
    current_page: Union[JdAreaPage, JdIdPage, JdExtPage] = jdbrowser.current_page
    main_window.setCentralWidget(current_page)

    settings = QSettings("xAI", "jdbrowser")
    if settings.contains("pos") and settings.contains("size"):
        main_window.move(settings.value("pos", type=QPoint))
        main_window.resize(settings.value("size", type=QSize))
    else:
        main_window.resize(1000, 600)
        screen = app.primaryScreen().geometry()
        main_window.move((screen.width() - 1000) // 2, (screen.height() - 600) // 2)

    main_window.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    sys.exit(app.exec())
