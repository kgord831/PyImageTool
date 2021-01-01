import pytest
import numpy as np
from PyQt5 import QtWidgets, QtCore
from pyimagetool import ImageTool, RegularDataArray


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
        return RegularDataArray(mat, dims=('x4', 'y2', 'z2'), delta=delta, coord_min=coord_min)

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
        qtbot.addWidget(it)
        assert len(it.info_bar.cursor_i) == 3
        it.show()

    def test_imagetool_regular_show(self, qtbot):
        dat = self.make_regular_data()
        it = ImageTool(dat)
        qtbot.addWidget(it)
        assert len(it.info_bar.cursor_i) == 3
        it.show()

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
        qtbot.waitSignal(it.pg_win.cursor._binwidth[0].value_set, timeout=3000)
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
        qtbot.addWidget(it)
        it.info_bar.cursor_i[0].setValue(2)
        it.info_bar.cursor_i[1].setValue(1)
        it.info_bar.bin_i[0].setValue(2)
        dat = dat.transpose([1, 0, 2])
        it.info_bar.transpose_request.emit([1, 0, 2])
        # dat = dat.transpose({0: 1, 1: 0, 2: 2})
        # it.info_bar.transpose_request.emit({0: 1, 1: 0, 2: 2})
        assert it.info_bar.cursor_labels[0].text() == 'y2'
        assert it.info_bar.cursor_labels[1].text() == 'x4'
        assert it.info_bar.cursor_labels[2].text() == 'z2'
        it.info_bar.bin_i[1].setValue(2)
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].xData, dat.axes[0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].yData, dat.axes[1])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].yData, dat.axes[2])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['x'][0].yData,
                                       np.mean(dat.values[:, 0:2, 0:1], axis=(1, 2)))
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['y'][0].xData, dat.values[0, :, 0])
        np.testing.assert_almost_equal(it.pg_win.lineplots_data['z'][0].xData,
                                       np.mean(dat.values[0:1, 0:2, :], axis=(0, 1)))
