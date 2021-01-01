from pyqtgraph.Qt import QtCore, QtWidgets
from functools import partial
from typing import Union
import pyqtgraph as pg
import numpy as np
import warnings

from .widgets import InfoBar
from .PGImageTool import PGImageTool
from .DataMatrix import RegularDataArray

try:
    import xarray as xr
    DataType = Union[RegularDataArray, np.array, xr.DataArray]
except ImportError:
    xr = None
    DataType = Union[RegularDataArray, np.array]


class ImageTool(QtWidgets.QWidget):
    LayoutSimple = PGImageTool.LayoutSimple
    LayoutComplete = PGImageTool.LayoutComplete
    LayoutRaster = PGImageTool.LayoutRaster

    def __init__(self, data: DataType,
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
        # -------------------------------
        def update_spinbox_view(spinbox: QtWidgets.QSpinBox, i: int):
            spinbox.blockSignals(True)
            spinbox.setValue(i)
            spinbox.blockSignals(False)

        for i, sb in enumerate(self.info_bar.cursor_i):
            sb.valueChanged.connect(partial(self.pg_win.cursor.set_index, i))
            self.pg_win.cursor.index[i].value_set.connect(partial(update_spinbox_view, sb))

        # Connect coordinate spin box to model
        # ------------------------------------
        def control_doublespinbox(doublespinbox: QtWidgets.QDoubleSpinBox, handler):
            handler(doublespinbox.value())

        def update_doublespinbox_view(doublespinbox: QtWidgets.QDoubleSpinBox, v: float):
            doublespinbox.blockSignals(True)
            doublespinbox.setValue(v)
            doublespinbox.blockSignals(False)

        for i, dsb in enumerate(self.info_bar.cursor_c):
            dsb.editingFinished.connect(partial(control_doublespinbox, dsb,
                                                partial(self.pg_win.cursor.set_pos, i)))
            self.pg_win.cursor.pos[i].value_set.connect(partial(update_doublespinbox_view, dsb))

        # Connect binwidth to model
        # -------------------------
        for i, sb in enumerate(self.info_bar.bin_i):
            sb.valueChanged.connect(partial(self.pg_win.cursor.set_binwidth_i, i))
            self.pg_win.cursor.binwidth[i].value_set.connect(partial(self.update_binwidth_index_view,
                                                                     sb, i))

        for i, dsb in enumerate(self.info_bar.bin_c):
            dsb.editingFinished.connect(partial(control_doublespinbox, dsb,
                                                partial(self.pg_win.cursor.set_binwidth, i)))
            self.pg_win.cursor.binwidth[i].value_set.connect(partial(update_doublespinbox_view, dsb))

    def update_binwidth_index_view(self, spinbox, i, newvalue):
        spinbox.blockSignals(True)
        spinbox.setValue(round(newvalue/self.data.delta[i]))
        spinbox.blockSignals(False)

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

    def get(self, plot: str):
        """Get a slice of the data shown in ImageTool.

        :param plot: should be one of ``x``, ``y``, ``z``, ``xy``, ``zy``, ``xt``, etc. depending on the plotted data
        :type plot: str
        :return: If returning an image, will return RegularDataArray. Otherwise, returns a tuple of x, y
        """
        # TODO: make plot items display RegularDataArray and consistently return a RegularDataArray
        plot = plot.lower()
        if plot in self.pg_win.imgs.keys():
            return self.pg_win.imgs[plot].data
        elif plot in self.pg_win.lineplots_data.keys():
            p = self.pg_win.lineplots_data[plot]
            if p[1] == 'h':
                return p[0].xData, p[0].yData
            else:
                return p[0].yData, p[0].xData
        else:
            legalvalues = list(self.pg_win.imgs.keys()) + list(self.pg_win.lineplots_data.keys())
            raise ValueError(f'plot {plot} not found in this ImageTool. Should be one of {legalvalues}')
