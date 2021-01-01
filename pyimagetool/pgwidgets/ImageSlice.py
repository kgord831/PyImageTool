import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
import warnings
import numpy as np
from functools import partial

from pyimagetool.DataMatrix import RegularDataArray
from pyimagetool.cmaps import CMap
from pyimagetool.pgwidgets import ImageBase
from pyimagetool.CMapEditor import CMapDialog


class ImageSlice(ImageBase):

    def __init__(self, dat: RegularDataArray = None, **kwargs):
        """2D image view with extra features.

        :param lut: Name of colormap to initialize with
        :type lut: str
        """
        super().__init__(dat, **kwargs)

        # -------------
        # Colormap menu
        # -------------
        self.cmap_menu = QtWidgets.QMenu('Color Map')
        # Reset colormap
        self.cmap_reset_action = QtWidgets.QAction('Reset')
        self.cmap_reset_action.triggered.connect(self.cmap_reset)
        self.cmap_menu.addAction(self.cmap_reset_action)
        # Scale to view
        self.cmap_to_view_action = QtWidgets.QAction('Scale to view')
        self.cmap_to_view_action.triggered.connect(self.cmap_to_range)
        self.cmap_menu.addAction(self.cmap_to_view_action)
        # Change colormap
        self.change_cmap_menu = QtWidgets.QMenu('Change colormap')
        self.change_cmap_actions = []
        def callback_prototype(imgbase, cmap_name="viridis"):
            ct = CMap().load_ct(cmap_name)
            imgbase.baselut = ct
            imgbase.set_lut(ct)
        for name in CMap().cmaps:
            action = QtWidgets.QAction(name)
            action.triggered.connect(partial(callback_prototype, self, name))
            self.change_cmap_actions.append(action)
            self.change_cmap_menu.addAction(action)
        self.cmap_menu.addMenu(self.change_cmap_menu)
        # Edit colormap
        self.edit_cmap_action = QtWidgets.QAction('Edit Color Map')
        self.edit_cmap_action.triggered.connect(self.edit_cmap)
        self.cmap_menu.addAction(self.edit_cmap_action)
        self.menu.addMenu(self.cmap_menu)

        # self.cmap_editor = QtWidgets.QWidget()
        self.build_cmap_form()

    def edit_cmap(self):
        dialog = CMapDialog(self.data)
        r = dialog.exec()
        if r == 1:
            lut = dialog.widget.get_lut()
            self.img.setLookupTable(lut)

    def build_cmap_form(self):
        pass

    def cmap_reset(self):
        self.img.setLookupTable(self.baselut)
        self.img.setLevels([np.min(self.data.values), np.max(self.data.values)])

    def cmap_to_range(self):
        [[xmin, xmax], [ymin, ymax]] = self.vb.viewRange()
        mat = self.data.sel(slice(xmin, xmax), slice(ymin, ymax)).values
        if mat.size < 2:
            return
        self.img.setLevels([np.min(mat), np.max(mat)])


def test():
    import sys
    from pyimagetool.data import triple_cross_2d, arpes_data_2d
    app = QtGui.QApplication([])

    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()
    window.setLayout(layout)
    pg_view = pg.GraphicsLayoutWidget(window)
    image_slice1 = ImageSlice(triple_cross_2d())
    image_slice2 = ImageSlice(arpes_data_2d())
    pg_view.addItem(image_slice1)
    pg_view.addItem(image_slice2)

    layout.addWidget(pg_view)

    window.resize(400, 400)
    window.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()