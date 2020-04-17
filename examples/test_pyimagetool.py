import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
from ..pyimagetool.DataMatrix import RegularDataArray
from ..pyimagetool.ImageTool import ImageTool


def gen_data():
    # Generate data
    Nx = 40
    Ny = 60
    Nz = 100
    Nt = 1
    x, y, z, t = np.linspace(-5, 5, Nx), np.linspace(-8, 8, Ny), np.linspace(-10, 10, Nz), np.linspace(-5, 5, Nt)
    if Nt == 1:
        t = 1
    X, Y, Z, T = np.meshgrid(x, y, z, t, indexing='ij')
    mat = np.exp(-0.02*(X**2 + Y**2 + Z**2 + T**2))*(np.cos(X) + np.cos(Y) + np.cos(Z))
    mat = mat.squeeze()
    axes = [x, y, z]
    if Nt > 1:
        axes.append(t)
    return RegularDataArray.from_numpy_array(mat, axes=axes)


# Start Qt event loop unless running in interactive mode.
app = QtWidgets.QApplication([])
# Generate data
my_data = gen_data()

image_tool = ImageTool(my_data, layout=ImageTool.LayoutComplete)
# transpose = TransposeAxesWidget(my_data)

image_tool.show()
# transpose.show()

if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtWidgets.QApplication.instance().exec_()
