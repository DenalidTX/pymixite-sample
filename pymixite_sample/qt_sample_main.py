import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic

from pymixite_sample.ui_control import UIInitializer


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_widget = uic.loadUi("qt_sample.ui", self)
        UIInitializer.setup(self.root_widget)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
