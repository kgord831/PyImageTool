from DataMatrix import RegularSpacedData
from widgets import InfoBar
import numpy as np
import sip
from PyQt5 import QtGui, QtCore, QtWidgets

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication([])
    # Generate data
    mat = np.arange(16).reshape((4, 4))
    mat2 = np.arange(4**4).reshape((4, 4, 4, 4))

    mydata = RegularSpacedData.from_numpy_array(mat)
    mydata2 = RegularSpacedData.from_numpy_array(mat2)

    myapp = QtWidgets.QWidget()
    myapp.setLayout(QtWidgets.QVBoxLayout())
    info_bar = InfoBar(mydata)
    myapp.layout().addWidget(info_bar)
    myapp.show()
    print(myapp.children())
    myapp.layout().removeWidget(info_bar)
    sip.delete(info_bar)
    print(myapp.children())
    info_bar = InfoBar(mydata2)
    myapp.layout().addWidget(info_bar)
    print(myapp.children())

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
        print(myapp.children())
