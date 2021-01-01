from .DataMatrix import RegularDataArray
from .ImageTool import ImageTool
from .PGImageTool import PGImageTool

__all__ = ['ImageTool', 'RegularDataArray']


def imagetool(data):
    from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
    import sys
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtGui.QApplication([])
        tool = ImageTool(data, layout=PGImageTool.LayoutComplete)
        tool.show()
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtWidgets.QApplication.instance().exec_()
        return tool
    else:
        tool = ImageTool(data, layout=PGImageTool.LayoutComplete)
        tool.show()
        return tool
