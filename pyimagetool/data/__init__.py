from pathlib import Path
import numpy as np

from ..DataMatrix import RegularDataArray


data_dir = Path(__file__).parent


def arpes_data_3d():
    """3D data from an ARPES experiment"""
    dat = np.load(str(Path(data_dir, 'arpes.npy')))
    return RegularDataArray(dat, delta=[0.1, 0.0621, 0.000758], coord_min=[-7.0, -22.5, 20.9])


def arpes_data_2d():
    """2D data from an ARPES experiment"""
    dat = np.load(str(Path(data_dir, 'example_2D.npy')))
    return RegularDataArray(dat, delta=[0.1, 0.0621], coord_min=[-7.0, -22.5])


def triple_cross_2d():
    x = np.linspace(-3, 3, 101)
    y = np.linspace(-5, 5, 101)
    X, Y = np.meshgrid(x, y, indexing='ij')
    gamma1 = 2
    gamma2 = 0.9
    gamma3 = 0.8
    img = gamma1**2/((Y - X**2)**2 + gamma1**2)\
          + gamma2**2/((Y + (1 + X**2))**2 + gamma2**2)\
          + gamma3**2/((Y - np.cos(X))**2 + gamma3**2)
    img += np.random.rand(*img.shape)*(img.max()/20)
    return RegularDataArray(img, delta=[x[1] - x[0], y[1] - y[0]], coord_min=[x[0], y[0]])


def oscillating_gaussian_4d():
    # Generate data
    Nx = 40
    Ny = 60
    Nz = 100
    Nt = 10
    x, y, z, t = np.linspace(-5, 5, Nx), np.linspace(-8, 8, Ny), np.linspace(-10, 10, Nz), np.linspace(-5, 5, Nt)
    if Nt == 1:
        t = 1
    X, Y, Z, T = np.meshgrid(x, y, z, t, indexing='ij')
    mat = np.exp(-0.02*(X**2 + Y**2 + Z**2 + T**2))*(np.cos(X) + np.cos(Y) + np.cos(Z))
    mat = mat.squeeze()
    delta = [x[1] - x[0], y[1] - y[0], z[1] - z[0], t[1] - t[0]]
    coord_min = [x[0], y[0], z[0], t[0]]
    return RegularDataArray(mat, delta=delta, coord_min=coord_min)
