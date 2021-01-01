import pytest
import numpy as np
from pyimagetool import RegularDataArray

class TestRegularDataArray:
    @staticmethod
    def make_5d():
        mat = np.arange(3*4*5*6*7*8).reshape((3, 4, 5, 6, 7, 8))
        dat = RegularDataArray(mat, delta=[2, 3, 4, 5, 6, 7], coord_min=[-1, -2, -3, -4, -5, -6])
        return dat

    @staticmethod
    def make_2d():
        mat = np.arange(20).reshape(4, 5)
        dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1])
        return dat

    def test_numpy_1d(self):
        # 1D Tests
        x = np.arange(9)
        y = RegularDataArray(x)
        assert len(y.delta) == 1
        assert y.delta[0] == 1
        assert y.coord_min[0] == 0
        y = RegularDataArray(x, delta=[3], coord_min=[3])
        assert y.delta[0] == 3
        assert y.offset[0] == 3
        assert np.allclose(y.axes[0], np.arange(9)*3 + 3)
        y = RegularDataArray(x, coord_min=10, delta=-5)
        assert y.delta[0] == pytest.approx(5)
        assert y.coord_min[0] == pytest.approx(-30)
        assert np.allclose(y.axes[0], np.arange(9)*5 - 30)
        assert np.allclose(y.values, x[::-1])

    def test_numpy_2d(self):
        # 2D Tests
        mat = np.arange(20).reshape(4, 5)
        dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1])
        assert dat.dims == ('x', 'y')
        assert np.allclose(dat.axes[0], np.arange(4)*3 + 6)
        assert np.allclose(dat.axes[1], np.arange(5)*5 + 1)
        dat_cr = dat.sel(slice(8, 13), slice(5, 17))
        assert np.allclose(dat_cr.values, np.array([[6, 7, 8], [11, 12, 13]]))
        assert dat_cr.offset[0] == 9
        assert dat_cr.delta[0] == 3
        dat_cr = dat.isel(slice(0, 3), slice(0, 2))
        assert np.allclose(dat_cr.values, np.array([[0, 1], [5, 6], [10, 11]]))
        dat = RegularDataArray(mat, delta=[-3, 5], coord_min=[12, 1])
        assert np.allclose(dat.axes[0], np.arange(4)*3 + 3)
        assert np.allclose(dat.values, mat[::-1, :])

    # def test_constructor(self):
    #     mat = np.arange(20).reshape(4, 5)
    #     dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1], dims=('mydim_x', 'mydim_y'))
    #     assert dat.dims == ('mydim_x', 'mydim_y')
    #     dat_cr = dat.sel(slice(8, 13), slice(5, 17))
    #     dat = RegularDataArray(dat_cr)
    #     assert np.all(dat_cr.values == dat.values)

    def test_isel(self):
        mat = np.arange(20).reshape(4, 5)
        dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1])
        dat_cr = dat.isel(slice(1, 3), slice(1, 4))
        assert np.allclose(dat_cr.values, mat[1:3, 1:4])
        assert dat_cr.coord_min[0] == pytest.approx(9)
        assert dat_cr.coord_min[1] == pytest.approx(6)
        assert dat_cr.coord_max[0] == pytest.approx(12)
        assert dat_cr.coord_max[1] == pytest.approx(16)
        assert np.allclose(dat_cr.axes[0], np.arange(2)*3 + 9)
        assert np.allclose(dat_cr.axes[1], np.arange(3)*5 + 6)
        dat_cr = dat.isel(0, None)
        assert np.allclose(dat_cr.values, mat[0, :].reshape(1, -1))
        dat_cr = dat.isel(-1, slice(None))
        assert np.allclose(dat_cr.values, mat[-1, :].reshape(1, -1))
        dat_cr = dat.isel(slice(None), 0)
        assert np.allclose(dat_cr.values, mat[:, 0].reshape(-1, 1))
        dat_cr = dat.isel(slice(None), -1)
        assert np.allclose(dat_cr.values, mat[:, -1].reshape(-1, 1))
        dat_cr = dat.isel(slice(-2, -1), slice(None))
        assert np.allclose(dat_cr.values, mat[-2:-1, :].reshape(1, -1))

    def test_sel(self):
        mat = np.arange(20).reshape(4, 5)
        dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1])
        dat_cr = dat.sel(slice(8, 13), slice(5, 17))
        assert np.allclose(dat_cr.values, mat[1:3, 1:4])
        assert dat_cr.coord_min[0] == pytest.approx(9)
        assert dat_cr.coord_min[1] == pytest.approx(6)
        assert dat_cr.coord_max[0] == pytest.approx(12)
        assert dat_cr.coord_max[1] == pytest.approx(16)
        assert np.allclose(dat_cr.axes[0], np.arange(2)*3 + 9)
        assert np.allclose(dat_cr.axes[1], np.arange(3)*5 + 6)
        dat_cr = dat.sel(slice(-5, 7), slice(24, 100))
        assert np.allclose(dat_cr.values, mat[0, -1].reshape(1, 1))

    def test_flatten(self):
        dat = self.make_2d()
        dat_cr = dat.isel(0, None)
        dat_cr = dat_cr.flatten()
        assert np.allclose(dat_cr.values, dat.values[0, :])

    def test_transpose(self):
        dat = self.make_5d()
        assert dat.dims == ('x', 'y', 'z', 't', 'dim4', 'dim5')
        dat = dat.transpose([2, 3, 0, 1, 5, 4])
        assert dat.dims == ('z', 't', 'x', 'y', 'dim5', 'dim4')

    def test_scaleindex(self):
        dat = self.make_5d()
        assert dat.scale_to_index(2, 1) == pytest.approx(1)
        assert dat.scale_to_index(2, 3) == pytest.approx(1.5)
        assert dat.index_to_scale(2, 2) == pytest.approx(5)
        assert dat.index_to_scale(2, 2.5) == pytest.approx(7)

    def test_mean(self):
        dat = self.make_2d()
        dat_mean = dat.mean(0)
        assert dat_mean.shape == (1, 5)
        assert dat_mean.coord_min[0] == pytest.approx(10.5)
        assert dat_mean.coord_min[1] == pytest.approx(1.0)
        assert np.allclose(dat_mean.values, dat.values.mean(axis=0).reshape(1, 5))
        dat_mean = dat.mean((0, 1))
        assert dat_mean.shape == (1, 1)
        assert dat_mean.coord_min[1] == pytest.approx(11.0)
        assert np.allclose(dat_mean.values, dat.values.mean(axis=(0,1)).reshape(1, 1))

