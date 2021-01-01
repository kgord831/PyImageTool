import numpy as np
from scipy.interpolate import interp1d
import os
import fnmatch
from PIL import Image

height = 12
width = 64

colorbar = np.empty((height, width, 3), dtype=np.uint8)
for filename in os.listdir('cmaps'):
    if fnmatch.fnmatch(filename, '*.npy'):
        mat = np.load('cmaps' + os.sep + filename)
        rows, cols = mat.shape
        if cols != 3:
            print(filename + " unsupported file format.")
        cmap_name = os.path.splitext(filename)[0]
        if colorbar.shape[1] > mat.shape[0]:
            f = interp1d(np.arange(mat.shape[0], np.newaxis)/mat.shape[0]*colorbar.shape[1], mat[:, :], axis=0, fill_value='extrapolate')
            colorbar[:, :, :] = f(np.arange(colorbar.shape[1]))[np.newaxis, :, :]
        else:
            stepsize = rows//width
            colorbar[:, :, :] = mat[np.newaxis, ::stepsize, :]
        colorbar_ico = Image.fromarray(colorbar)
        colorbar_ico.save('cmaps' + os.sep + cmap_name + '.jpg', 'jpeg')
