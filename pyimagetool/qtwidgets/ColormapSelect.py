from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from pyimagetool.cmaps import CMap


class ColormapForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout management
        self.main_layout = QtWidgets.QFormLayout()
        self.setLayout(self.main_layout)

        for name in CMap().cmaps:
            pixmap = CMap().load_pixmap(name)
            ct = QtWidgets.QLabel('blue')
            ct.setPixmap(pixmap)
            self.main_layout.addRow(QtWidgets.QLabel(name), ct)


class ColormapSelect(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout management
        self.main_layout = QtWidgets.QgridLayout()


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication([])

    window = ColormapForm()

    window.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
