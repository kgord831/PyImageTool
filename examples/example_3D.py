import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
from pyimagetool import ImageTool
from pyimagetool import RegularDataArray


def gen_data():
    # Generate data
    e = np.linspace(-1.5, 0.2, 101)
    kx = np.linspace(-1, 1, 101)
    ky = np.linspace(-1.3, 1.8, 101)
    Kx, Ky, E = np.meshgrid(kx, ky, e, indexing='ij')
    spp = 0.1
    mat = spp/((E - np.sqrt(Kx**2 + Ky**2) + 0.4)**2 + spp**2) + spp/((E + np.sqrt(Kx**2 + Ky**2) + 0.4)**2 + spp**2)
    mat *= 1/(np.exp(E/0.05) + 1)
    mat += np.random.random(mat.shape)*np.max(mat)*0.1
    axes = [kx, ky, e]
    return RegularDataArray(mat, axes=axes)


# def from_file():
#     import h5py
#     f = h5py.File(r'Mn1610_02_00034.h5', 'r')
#     counts = np.array(f['data']['counts'])
#     exposure = np.array(f['data']['exposure'])
#     counts[exposure <= 0] = 0
#     dat_mat = counts
#     dat_mat[exposure > 0] /= exposure[exposure > 0]
#     dat_mat[np.isnan(dat_mat)] = 0
#     delta = [f['data'][axis].attrs['delta'] for axis in ['axis0', 'axis1', 'axis2']]
#     coord_min = [f['data'][axis].attrs['offset'] for axis in ['axis0', 'axis1', 'axis2']]
#     f.close()
#
#     mydata = RegularDataArray(dat_mat, delta=delta, coord_min=coord_min)
#     return mydata


# Start Qt event loop unless running in interactive mode.
app = QtWidgets.QApplication([])
# Generate data
my_data = gen_data()
# my_data = from_file()
# my_data = my_data.sel({'x': slice(-6, 6.62), 'y': slice(-12.4, 17.33), 'z': slice(20.93, 21.59)})

image_tool = ImageTool(my_data, layout=ImageTool.LayoutComplete)

image_tool.show()

if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtWidgets.QApplication.instance().exec_()
