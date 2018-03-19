#!/usr/bin/env python2
import sys
from PyQt5.QtCore import QLocale, QTranslator
from PyQt5.QtWidgets import QApplication
from input import MainWindow

__version__ = "0.26"

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
