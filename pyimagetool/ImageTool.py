from .widgets import InfoBar
from .PGImageTool import PGImageTool
from .DataMatrix import RegularDataArray
from pyqtgraph.Qt import QtCore, QtWidgets
from functools import partial
from typing import Union
import pyqtgraph as pg
import numpy as np
import xarray as xr
import warnings


class ImageTool(QtWidgets.QWidget):
    LayoutSimple = PGImageTool.LayoutSimple
    LayoutComplete = PGImageTool.LayoutComplete
    LayoutRaster = PGImageTool.LayoutRaster

    def __init__(self, data: Union[RegularDataArray, np.array, xr.DataArray],
                 layout: int = PGImageTool.LayoutSimple, parent=None):
        """Create an ImageTool QWidget.
        :param data: A RegularDataArray, numpy.array, or xarray.DataArray
        :param layout: An int that defines the layout. See PGImageTool for layout definitions
        :param parent: QWidget that will be this widget's parent
        """
        super().__init__(parent)
        # Warn user about nan
        if hasattr(data, 'values'):
            d = data.values
        else:
            d = data
        if np.any(np.isnan(d)):
            warnings.warn('Input data contains NaNs. All NaN will be set to 0.')
            d[np.isnan(d)] = 0
        # Create data
        self.data: RegularDataArray = RegularDataArray(data)
        self.it_layout: int = layout
        # Create info bar and ImageTool PyQt Widget
        self.info_bar = InfoBar(self.data, parent=self)
        self.pg_widget = QtWidgets.QWidget()  # widget to hold pyqtgraph graphicslayout
        self.pg_widget.setLayout(QtWidgets.QVBoxLayout())
        self.pg_win = PGImageTool(self.data, layout=layout)  # the pyqtgraph graphicslayout
        self.pg_widget.layout().addWidget(self.pg_win)
        # Build the layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.info_bar)
        self.layout().addWidget(self.pg_win)
        # Create status bar
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.showMessage("Initialized")
        self.layout().addWidget(self.status_bar)
        # Connect signals and slots
        self.mouse_move_proxy = pg.SignalProxy(self.pg_win.mouse_hover, rateLimit=30, slot=self.update_status_bar)
        self.build_handlers()
        # TODO: update to QT 5.14 and use textActivated signal instead
        self.info_bar.cmap_combobox.currentTextChanged.connect(self.set_all_cmaps)
        self.info_bar.transpose_request.connect(self.transpose_data)

    def update_status_bar(self, msg: tuple):
        """Slot for mouse move signal"""
        self.status_bar.showMessage(msg[0])

    def build_handlers(self):
        # Connect index spin box to model
        for i, sb in enumerate(self.info_bar.cursor_i):
            sb.valueChanged.connect(partial(self.pg_win.cursor.set_index, i))
            self.pg_win.cursor.index[i].value_changed.connect(sb.setValue)

        # Connect coordinate spin box to model
        def on_cursor_dsb_changed(spinbox, handler):
            handler(spinbox.value())

        for i, dsb in enumerate(self.info_bar.cursor_c):
            coord = self.pg_win.index_to_coord[i]
            dsb.editingFinished.connect(partial(on_cursor_dsb_changed,
                                                dsb,
                                                partial(self.pg_win.cursor.set_pos, i)))
            self.pg_win.cursor.pos[i].value_changed.connect(dsb.setValue)

        # Connect binwidth to model
        for i, sb in enumerate(self.info_bar.bin_i):
            sb.valueChanged.connect(partial(self.pg_win.cursor.set_binwidth_i, i))
            self.pg_win.cursor.bin_width[i].value_changed.connect(partial(self.binwidth_sb_handler, i, sb))

        for i, dsb in enumerate(self.info_bar.bin_c):
            dsb.editingFinished.connect(partial(on_cursor_dsb_changed,
                                                dsb,
                                                partial(self.pg_win.cursor.set_binwidth, i)))
            self.pg_win.cursor.bin_width[i].value_changed.connect(dsb.setValue)

    def binwidth_sb_handler(self, i, sb, newval):
        sb.setValue(int(round(newval/self.data.delta[i])))

    def reset(self):
        # Create info bar and ImageTool PyQt Widget
        self.info_bar.reset(self.data)
        self.pg_win.reset(self.data)

    def set_all_cmaps(self, cmap_name: str):
        self.pg_win.load_ct(cmap_name)

    def transpose_data(self, tr):
        self.data = self.data.transpose(tr)
        self.reset()

    def keyReleaseEvent(self, e):
        if e.key() == QtCore.Qt.Key_Shift:
            self.pg_win.shift_down = False
        else:
            e.ignore()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Shift:
            self.pg_win.shift_down = True
            self.pg_win.set_crosshair_to_mouse()
        else:
            e.ignore()
