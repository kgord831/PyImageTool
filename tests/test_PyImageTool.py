import pytest
import numpy as np
from PyQt5 import QtWidgets, QtCore
from pyimagetool import ImageTool, RegularDataArray


class TestRegularDataArray:
    @staticmethod
    def make_5d():
        mat = np.arange(3*4*5*6*7*8).reshape((3, 4, 5, 6, 7, 8))
        dat = RegularDataArray(mat, delta=[2, 3, 4, 5, 6, 7], coord_min=[-1, -2, -3, -4, -5, -6])
        return dat

    def test_numpy_1d(self):
        # 1D Tests
        x = np.arange(9)
        y = RegularDataArray(x)
        assert len(y.delta) == 1
        assert y.delta[0] == 1
        assert y.coord_min[0] == 0
        y = RegularDataArray(x, axes=[3*np.arange(9) + 3])
        assert y.delta[0] == 3
        assert y.offset[0] == 3

    def test_numpy_2d(self):
        # 2D Tests
        mat = np.arange(20).reshape(4, 5)
        dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1])
        assert dat.dims == ('x', 'y')
        dat_cr = dat.sel({'x': slice(8, 13), 'y': slice(5, 17)})
        assert np.all(dat_cr.values == np.array([[6, 7, 8], [11, 12, 13]]))
        assert dat_cr.offset[0] == 9
        assert dat_cr.delta[0] == 3
        dat_cr = dat.isel({'x': slice(0, 3), 'y': slice(0, 2)})
        assert np.all(dat_cr.values == np.array([[0, 1], [5, 6], [10, 11]]))

    def test_constructor(self):
        mat = np.arange(20).reshape(4, 5)
        dat = RegularDataArray(mat, delta=[3, 5], coord_min=[6, 1], dims=('mydim_x', 'mydim_y'))
        assert dat.dims == ('mydim_x', 'mydim_y')
        dat_cr = dat.sel({'mydim_x': slice(8, 13), 'mydim_y': slice(5, 17)})
        dat = RegularDataArray(dat_cr)
        assert np.all(dat_cr.values == dat.values)

    def test_transpose(self):
        dat = self.make_5d()
        assert dat.dims == ('x', 'y', 'z', 't', 'dim_4', 'dim_5')
        dat = dat.transpose({0: 2, 1: 3, 2: 0, 3: 1, 4: 5, 5: 4})
        assert dat.dims == ('z', 't', 'x', 'y', 'dim_5', 'dim_4')

    def test_scaleindex(self):
        dat = self.make_5d()
        assert dat.scale_to_index(2, 1) == pytest.approx(1)
        assert dat.scale_to_index(2, 3) == pytest.approx(1.5)
        assert dat.index_to_scale(2, 2) == pytest.approx(5)
        assert dat.index_to_scale(2, 2.5) == pytest.approx(7)


class TestImageTool:
    @staticmethod
    def make_regular_data():
        # Generate data
        mat = np.array([[[9, 1],
                         [2, 3]],
                        [[5, 5],
                         [1, 1]],
                        [[1, 1],
                         [0, 0]],
                        [[3, 2],
                         [1, 8]]])
        delta = [2, 5, 7]
        coord_min = [0, 1, 2]
        return RegularDataArray.from_numpy_array(mat, dims=('x4', 'y2', 'z2'), delta=delta, coord_min=coord_min)

    @staticmethod
    def make_numpy_data():
        # Generate data
        mat = np.array([[[9, 1],
                         [2, 3]],
                        [[5, 5],
                         [1, 1]],
                        [[1, 1],
                         [0, 0]],
                        [[3, 2],
                         [1, 8]]])
        return mat

    def test_imagetool_numpy_show(self, qtbot):
        mat = self.make_numpy_data()
        it = ImageTool(mat)
        it.show()
        # qtbot.stopForInteraction()

    def test_imagetool_regular_show(self, qtbot):
        dat = self.make_regular_data()
        it = ImageTool(dat)
        it.show()
        # qtbot.stopForInteraction()

    def test_imagetool_numpy(self, qtbot):
        mat = self.make_numpy_data()
        it = ImageTool(mat)
        assert it.pg_win.lineplots_data['x'][1] == 'h'
        assert np.all(it.pg_win.lineplots_data['x'][0].xData == np.arange(4))
        assert np.all(it.pg_win.lineplots_data['x'][0].yData == mat[:, 0, 0])
        assert it.pg_win.lineplots_data['y'][1] == 'v'
        assert np.all(it.pg_win.lineplots_data['y'][0].xData == mat[0, :, 0])
        assert np.all(it.pg_win.lineplots_data['y'][0].yData == np.arange(2))
        assert it.pg_win.lineplots_data['z'][1] == 'v'
        assert np.all(it.pg_win.lineplots_data['z'][0].xData == mat[0, 0, :])
        assert np.all(it.pg_win.lineplots_data['z'][0].yData == np.arange(2))

    def test_imagetool_regular(self, qtbot):
        dat = self.make_regular_data()
        it = ImageTool(dat)
        assert it.pg_win.lineplots_data['x'][1] == 'h'
        assert np.all(it.pg_win.lineplots_data['x'][0].xData == dat.axes[0])
        assert np.all(it.pg_win.lineplots_data['x'][0].yData == dat.values[:, 0, 0])
        assert it.pg_win.lineplots_data['y'][1] == 'v'
        assert np.all(it.pg_win.lineplots_data['y'][0].xData == dat.values[0, :, 0])
        assert np.all(it.pg_win.lineplots_data['y'][0].yData == dat.axes[1])
        assert it.pg_win.lineplots_data['z'][1] == 'v'
        assert np.all(it.pg_win.lineplots_data['z'][0].xData == dat.values[0, 0, :])
        assert np.all(it.pg_win.lineplots_data['z'][0].yData == dat.axes[2])

    def test_imagetool_cursor(self, qtbot):
        dat = self.make_regular_data()
        it = ImageTool(dat)
        it.info_bar.cursor_i[0].setValue(2)
        it.info_bar.cursor_i[1].setValue(1)
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData, dat.values[:, 1, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData, dat.values[2, :, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData, dat.values[2, 1, :])
        it.info_bar.cursor_i[0].setValue(1)
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData, dat.values[:, 1, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData, dat.values[1, :, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData, dat.values[1, 1, :])

    def test_imagetool_bin(self, qtbot):
        dat = self.make_regular_data()
        it = ImageTool(dat)
        # Set cursor index to (2, 1, 0), and bin in index by 2, so we average over three elements in x
        it.info_bar.cursor_i[0].setValue(2)
        it.info_bar.cursor_i[1].setValue(1)
        it.info_bar.bin_i[0].setValue(2)
        assert it.info_bar.bin_c[0].value() == pytest.approx(2*dat.delta[0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData, dat.values[:, 1, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData,
                                       np.mean(dat.values[1:4, :, 0:1], axis=(0, 2)))
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData,
                                       np.mean(dat.values[1:4, 1:2, :], axis=(0, 1)))
        # Confirm that updating the bin width double spinbox property updates the bin width integer spinbox
        it.info_bar.bin_c[0].setValue(4.1)
        it.info_bar.bin_c[0].editingFinished.emit()
        assert it.info_bar.bin_i[0].value() == 2
        # Place the cursor at x = 3, and the index of x = 1.5 => 2
        # Set the bin width index to 1. This guarantees no binning.
        it.info_bar.cursor_c[0].setValue(3)
        it.info_bar.cursor_c[0].editingFinished.emit()
        it.info_bar.bin_i[0].setValue(1)
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData, dat.values[:, 1, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData,
                                       np.mean(dat.values[2:3, :, 0:1], axis=(0, 2)))
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData,
                                       np.mean(dat.values[2:3, 1:2, :], axis=(0, 1)))
        # Cursor still at 3. Now the bin width is slightly larger than delta, and there will be averaging.
        it.info_bar.bin_c[0].setValue(2.1)
        it.info_bar.bin_c[0].editingFinished.emit()
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData, dat.values[:, 1, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData,
                                       np.mean(dat.values[1:3, :, 0:1], axis=(0, 2)))
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData,
                                       np.mean(dat.values[1:3, 1:2, :], axis=(0, 1)))

    def test_imagetool_transpose(self, qtbot):
        dat = self.make_regular_data()
        it = ImageTool(dat)
        it.show()
        qtbot.waitForWindowShown(it)
        it.info_bar.cursor_i[0].setValue(2)
        it.info_bar.cursor_i[1].setValue(1)
        it.info_bar.bin_i[0].setValue(2)
        dat = dat.transpose({0: 1, 1: 0, 2: 2})
        it.transpose_data({0: 1, 1: 0, 2: 2})
        assert it.info_bar.cursor_labels[0].text() == 'y2'
        assert it.info_bar.cursor_labels[1].text() == 'x4'
        assert it.info_bar.cursor_labels[2].text() == 'z2'
        it.info_bar.bin_i[1].setValue(2)
        qtbot.waitSignal(it.info_bar.bin_i[1].valueChanged)
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].xData, dat.axes[0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].yData, dat.axes[1])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].yData, dat.axes[2])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData,
                                       np.mean(dat.values[:, 0:2, 0:1], axis=(1, 2)))
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData, dat.values[0, :, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData,
                                       np.mean(dat.values[0:1, 0:2, :], axis=(0, 1)))
