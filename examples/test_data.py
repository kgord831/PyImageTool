from DataMatrix import RegularSpacedData, RegularDataArray
import numpy as np
import xarray as xr

print('*'*20)
mat = np.arange(9).reshape(3, 3)
data_mat = RegularDataArray(mat, delta=np.array([3, 2]), coord_min=np.array([-1, -3]))
print(data_mat.data)
data_mat = data_mat.transpose({1: 0, 0: 1})
print(data_mat.data)

print('*'*20)

mat = np.arange(9).reshape(3, 3)
data_mat = RegularSpacedData.from_numpy_array(mat, delta=np.array([3, 2]), coord_min=np.array([-1, -3]))
print(data_mat.data, data_mat.axes[0])

print('*'*20)

mat = np.arange(9).reshape((3, 3))
data_mat = RegularSpacedData.from_numpy_array(mat, delta=np.array([3, 2]), coord_min=np.array([-1, -3]))
print(data_mat.data, data_mat.axes[0])
data_mat = data_mat.slice(1, slice(None))
print(data_mat.data, data_mat.axes[0])

print('*'*20)

data_mat.mat = np.zeros((4, 4))
data_mat = RegularSpacedData.from_numpy_array(mat, delta=np.array([3, 2]), coord_min=np.array([-1, -3]))
print(data_mat.data, data_mat.axes)

print('*'*20)

mat = np.zeros((3, 3))
darray = xr.DataArray(mat, dims=('x', 'y'), coords={'x': [0, 1, 2], 'y': [0, 1, 2]})
data_mat = RegularSpacedData.from_xarray_dataarray(darray)
print(data_mat.data, data_mat.axes)
