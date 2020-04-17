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


def from_file():
    import h5py
    f = h5py.File('Mn1610_02_00034.h5', 'r')
    counts = np.array(f['data']['counts'])
    exposure = np.array(f['data']['exposure'])
    counts[exposure <= 0] = 0
    dat_mat = counts
    dat_mat[exposure > 0] /= exposure[exposure > 0]
    # dat_mat[np.isnan(dat_mat)] = 0
    delta = [f['data'][axis].attrs['delta'] for axis in ['axis0', 'axis1', 'axis2']]
    coord_min = [f['data'][axis].attrs['offset'] for axis in ['axis0', 'axis1', 'axis2']]
    f.close()

    mydata = RegularDataArray(dat_mat, delta=delta, coord_min=coord_min)
    return mydata


# Start Qt event loop unless running in interactive mode.
app = QtWidgets.QApplication([])
# Generate data
my_data = from_file()
my_data = my_data.sel({'x': slice(-6, 6.62), 'y': slice(-12.4, 17.33), 'z': slice(20.93, 21.59)})

image_tool = ImageTool(my_data, layout=ImageTool.LayoutComplete)
# transpose = TransposeAxesWidget(my_data)

image_tool.show()
# transpose.show()

if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtWidgets.QApplication.instance().exec_()
