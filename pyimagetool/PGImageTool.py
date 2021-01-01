import numpy as np
from typing import Dict, List, Tuple, Union
from functools import partial
from collections.abc import Iterable
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent

from .DataMatrix import RegularDataArray
from .cmaps import CMap
from .DataModel import ValueLimitedModel
from pyimagetool.pgwidgets.BinningLine import BinningLine
from pyimagetool.pgwidgets.ImageSlice import ImageSlice


class PGImageTool(pg.GraphicsLayoutWidget):
    LayoutSimple = 0
    LayoutComplete = 1
    LayoutRaster = 2
    coord_to_index = {'x': 0, 'y': 1, 'z': 2, 't': 3,
                      'xy': (0, 1), 'zy': (2, 1), 'xz': (0, 2), 'zt': (2, 3)}
    index_to_coord: List[str] = ['x', 'y', 'z', 't']
    frame_rate = 60
    bin_pen = pg.mkPen(style=pg.Qt.QtCore.Qt.DashLine)

    mouse_hover = QtCore.Signal(str)  # event fired when the mouse moves on an image

    def __init__(self, data: RegularDataArray, parent=None, layout=0):
        """data is the RegularSpacedData to examine
        layout is an integer. 0 is a simple layout, 1 is a complete layout, and 2 is a special layout for 4D data"""
        super().__init__(parent)

        self.data: RegularDataArray = data
        self.parent = parent
        self.tool_layout: int = layout

        self.cursor: Cursor = Cursor(data)

        self.lineplots: Dict[str, Tuple[pg.PlotItem, str]] = {}  # dict of (PlotItem, orient), orient = 'h' or 'v'
        self.lineplots_data: Dict[str, Tuple[pg.PlotDataItem, str]] = {}  # dict of PlotDataItems, orient = 'h' or 'v'
        self.cursor_lines: Dict[str, List[BinningLine]] = {}  # dict of cursor lines for 'x', 'y', 'z', etc.
        self.imgs: Dict[str, ImageSlice] = {}  # a dictionary of ImageItems
        self.img_tr: Dict[str, QtGui.QTransform] = {}  # a dictionary of transforms going from index to coordinates
        self.img_tr_inv: Dict[str, QtGui.QTransform] = {}  # a dictionary of transforms going from coordinates to index

        self._signal_proxies: List[pg.SignalProxy] = []  # a list of created signal proxies to be held in memory

        # Properties for color map
        self.ct: np.array = np.array([])
        self.ct_name: str = 'blue_orange'

        # Properties for tracking the mouse
        self.mouse_pos: QtCore.QPointF = QtCore.QPointF(0, 0)
        self.mouse_panel: str = ''

        # Keyboard
        self.shift_down = False

        self.status_bar: str = ''  # string representing current mouse location

        self.load_ct(self.ct_name)
        self.build_layout()  # add plots according to chosen layout which populates self.lineplots and self.img_axes
        self.create_items()  # now that axes are ready, make ImageItems, PlotDataItems, and Cursor lines
        self.init_data()  # set data for each ImageItem, PlotDataItem, and connect cursors to data

    def reset(self, data: RegularDataArray):
        """
        When it's time to update the data represented by this image tool, update all properties
        """
        # Set the new data
        self.data = data
        # Reset the cursor
        self.cursor.reset(data)
        # for i in range(self.data.ndim):
        #     self.cursor.set_index(i, 0)
        # Update the line cuts
        for key, (plot_item, orientation) in self.lineplots_data.items():
            # Set the initial data
            i = self.coord_to_index[key]
            linedata = self.cursor.get_cut(i).squeeze().values
            if orientation == 'h':
                plot_item.setData(self.data.axes[i], linedata)
            else:
                plot_item.setData(linedata, self.data.axes[i])
        # Update the image plots
        for key, img_ax in self.imgs.items():
            i, j = self.coord_to_index[key]
            sl = [slice(None) if x == i or x == j else 0 for x in range(self.data.ndim)]
            selector = tuple(sl)
            if j > i:
                img_ax.set_data(self.data.isel(*selector).squeeze())
            else:
                img_ax.set_data(self.data.isel(*selector).squeeze().T)
            if img_ax.aspect_ui.lockAspect.isChecked():
                img_ax.aspect_ui.lockAspect.click()
            img_ax.vb.setXRange(self.data.coord_min[i], self.data.coord_max[i])
            img_ax.vb.setYRange(self.data.coord_min[j], self.data.coord_max[j])
        # Update the cursor lines
        for axis, line_list in self.cursor_lines.items():
            i = self.coord_to_index[axis]
            for line in line_list:
                line.set_min_binwidth(self.data.delta[i])
                line.set_binwidth(self.data.delta[i])
                line.update_bounds((self.data.coord_min[i], self.data.coord_max[i]))
        # Update the cursor object
        self.cursor.reset(data)

    def build_layout(self):
        # 1 dimension has a trivial layout
        if self.data.ndim == 1:
            self.lineplots['x'] = (self.addPlot(), 'h')
        # 2 dimensions has vertical profile on left side, horizontal profile on bottom, and image in top right
        if self.data.ndim == 2:
            self.lineplots['y'] = (self.addPlot(), 'v')
            self.imgs['xy'] = ImageSlice()
            self.addItem(self.imgs['xy'])
            self.nextRow()
            self.nextCol()
            self.lineplots['x'] = (self.addPlot(), 'h')
            self.ci.layout.setColumnStretchFactor(0, 1)
            self.ci.layout.setColumnStretchFactor(1, 2)
            self.ci.layout.setRowStretchFactor(0, 2)
            self.ci.layout.setRowStretchFactor(1, 1)
            self.lineplots['x'][0].setXLink(self.imgs['xy'])
            self.lineplots['y'][0].setYLink(self.imgs['xy'])
        # 3 dimensions has multiple layouts
        if self.data.ndim == 3:
            if self.tool_layout == self.LayoutSimple:
                self.lineplots['y'] = (self.addPlot(), 'v')
                self.imgs['xy'] = ImageSlice()
                self.addItem(self.imgs['xy'])
                self.lineplots['z'] = (self.addPlot(rowspan=2), 'v')
                self.nextRow()
                self.nextCol()
                self.lineplots['x'] = (self.addPlot(), 'h')
                self.ci.layout.setColumnStretchFactor(0, 1)
                self.ci.layout.setColumnStretchFactor(1, 2)
                self.ci.layout.setRowStretchFactor(0, 2)
                self.ci.layout.setRowStretchFactor(1, 1)
                self.lineplots['x'][0].setXLink(self.imgs['xy'])
                self.lineplots['y'][0].setYLink(self.imgs['xy'])
            else:  # make a complete layout
                self.lineplots['x'] = (self.addPlot(), 'h')
                self.lineplots['z'] = (self.addPlot(rowspan=2, colspan=2), 'h')
                self.nextRow()
                self.imgs['xz'] = ImageSlice()
                self.addItem(self.imgs['xz'])
                self.nextRow()
                self.imgs['xy'] = ImageSlice()
                self.addItem(self.imgs['xy'])
                self.imgs['zy'] = ImageSlice()
                self.addItem(self.imgs['zy'])
                self.lineplots['y'] = (self.addPlot(), 'v')
                self.ci.layout.setColumnStretchFactor(0, 4)
                self.ci.layout.setColumnStretchFactor(1, 4)
                self.ci.layout.setColumnStretchFactor(2, 1)
                self.ci.layout.setRowStretchFactor(0, 1)
                self.ci.layout.setRowStretchFactor(1, 4)
                self.ci.layout.setRowStretchFactor(2, 4)
                self.lineplots['x'][0].setXLink(self.imgs['xz'])
                self.imgs['xz'].setXLink(self.imgs['xy'])
                self.imgs['xy'].setYLink(self.imgs['zy'])
                self.imgs['zy'].setYLink(self.lineplots['y'][0])
        if self.data.ndim == 4:
            self.lineplots['y'] = (self.addPlot(), 'v')
            self.imgs['xy'] = ImageSlice()
            self.addItem(self.imgs['xy'])
            self.imgs['zt'] = ImageSlice()
            self.addItem(self.imgs['zt'])
            self.lineplots['t'] = (self.addPlot(), 'v')
            self.nextRow()
            self.nextCol()
            self.lineplots['x'] = (self.addPlot(), 'h')
            self.lineplots['z'] = (self.addPlot(), 'h')
            self.lineplots['x'][0].setXLink(self.imgs['xy'])
            self.lineplots['z'][0].setXLink(self.imgs['zt'])
            self.lineplots['y'][0].setYLink(self.imgs['xy'])
            self.lineplots['t'][0].setYLink(self.imgs['zt'])
            self.ci.layout.setRowStretchFactor(0, 2)
            self.ci.layout.setRowStretchFactor(0, 2)
            self.ci.layout.setColumnStretchFactor(1, 2)
            self.ci.layout.setColumnStretchFactor(2, 2)

    def create_items(self):
        # Create a PlotDataItem for each PlotItem
        for key, (plotitem, orientation) in self.lineplots.items():
            # Create the PlotDataItem
            i = self.coord_to_index[key]
            self.lineplots_data[key] = (plotitem.plot(self.data.axes[i], np.zeros(self.data.shape[i])), orientation)
            # Add the hover event
            handler = partial(self.lin_hover_handler, i, plotitem)
            evt_proxy = pg.SignalProxy(plotitem.scene().sigMouseMoved, rateLimit=self.frame_rate, slot=handler)
            self._signal_proxies.append(evt_proxy)
            # Add a binning line
            if orientation == 'h':
                angle = 90
            else:
                angle = 0
            args = {'pos': self.data.coord_min[i], 'angle': angle, 'bin_pen': self.bin_pen, 'movable': True,
                    'bounds': (self.data.coord_min[i], self.data.coord_max[i]), 'binwidth': self.data.delta[i]}
            cursor_line = BinningLine(**args)
            plotitem.addItem(cursor_line)
            # connect binning line control event to model update
            cursor_line.sigPositionChanged.connect(partial(self.cursor.set_pos, i))
            # connect model update to binning view
            self.cursor.pos[i].value_set.connect(cursor_line.update_pos)
            self.cursor.binwidth[i].value_set.connect(cursor_line.set_binwidth)
            self.cursor_lines[key] = [cursor_line]  # guaranteed to be the only item

        # Create an image item corresponding to each axis
        for key, img_ax in self.imgs.items():
            i, j = self.coord_to_index[key]
            sl = [slice(None) if x == i or x == j else 0 for x in range(self.data.ndim)]
            selector = tuple(sl)
            if j > i:
                img_ax.set_data(self.data.isel(*selector).squeeze(), lut=self.ct)
            else:
                img_ax.set_data(self.data.isel(*selector).squeeze().T, lut=self.ct)
            self.img_tr[key] = img_ax.img.transform()
            self.img_tr_inv[key], _ = img_ax.img.transform().inverted()

            # Add hover event
            img_ax.img.hoverEvent = partial(self.img_hover_handler, i, j, img_ax.img)

            # Add a binning line
            # in my convention, i is always the horizontal axis (vert_cursor) in an image plot
            args1 = {'pos': self.data.coord_min[i], 'angle': 90, 'bin_pen': self.bin_pen, 'movable': True,
                     'bounds': (self.data.coord_min[i], self.data.coord_max[i]), 'binwidth': self.data.delta[i]}
            args2 = {'pos': self.data.coord_min[j], 'angle': 0, 'bin_pen': self.bin_pen, 'movable': True,
                     'bounds': (self.data.coord_min[j], self.data.coord_max[j]), 'binwidth': self.data.delta[j]}
            vert_cursor = BinningLine(**args1)
            horz_cursor = BinningLine(**args2)
            vert_cursor.sigPositionChanged.connect(partial(self.cursor.set_pos, i))
            self.cursor.pos[i].value_set.connect(vert_cursor.update_pos)
            horz_cursor.sigPositionChanged.connect(partial(self.cursor.set_pos, j))
            self.cursor.pos[j].value_set.connect(horz_cursor.update_pos)
            self.cursor.binwidth[i].value_set.connect(vert_cursor.set_binwidth)
            self.cursor.binwidth[j].value_set.connect(horz_cursor.set_binwidth)
            axis0, axis1 = tuple(key)
            if axis0 in self.cursor_lines:
                self.cursor_lines[axis0].append(vert_cursor)
            else:
                self.cursor_lines[axis0] = [vert_cursor]
            if axis1 in self.cursor_lines:
                self.cursor_lines[axis1].append(horz_cursor)
            else:
                self.cursor_lines[axis1] = [horz_cursor]
            img_ax.addItem(vert_cursor)
            img_ax.addItem(horz_cursor)
            img_ax.autoRange()

    def init_data(self):
        for key, (plot_item, orientation) in self.lineplots_data.items():
            # Set the initial data
            i = self.coord_to_index[key]
            linedata = self.cursor.get_cut(i).squeeze().values
            if orientation == 'h':
                plot_item.setData(self.data.axes[i], linedata)
            else:
                plot_item.setData(linedata, self.data.axes[i])
            # Listen to all cursor indices (except this one) and connect to update function
            for j in range(self.data.ndim):
                if j != i:
                    self.cursor.index[j].value_set.connect(partial(self.update_line, i, plot_item, orientation))
                    self.cursor.binwidth[j].value_set.connect(partial(self.update_line, i, plot_item, orientation))
        for key, img_ax in self.imgs.items():
            # Wire up events
            i, j = self.coord_to_index[key]
            for k in range(self.data.ndim):
                if k != i and k != j:
                    self.cursor.index[k].value_set.connect(partial(self.update_img, i, j, img_ax))
                    self.cursor.binwidth[k].value_set.connect(partial(self.update_img, i, j, img_ax))

    def update_img(self, i: int, j: int, img: ImageSlice, _=None):
        """Template function for creating image update callback functions.
        i is the row axis, j is the col axis corresponding to the image. xy is 0, 1 and zy is 2, 1"""
        x = self.cursor.get_cut((i, j)).squeeze()
        if j > i:
            img.set_data(x, calc_tr=False)
        else:
            img.set_data(x.T, calc_tr=False)

    def update_line(self, index: int, lineplot: pg.PlotDataItem, orientation: str, _=None):
        """Template function for creating callbacks which update every PlotDataItem according to current cursor
        position."""
        x = self.cursor.get_cut(index).squeeze()
        if orientation == 'h':
            lineplot.setData(self.data.axes[index], x.values)
        else:
            lineplot.setData(x.values, self.data.axes[index])

    def load_ct(self, cmap_name: str = 'viridis'):
        """
        Supported color maps:
        - viridis
        - inferno
        - magma
        - plasma
        - CET color maps (https://peterkovesi.com/projects/colourmaps/)
        """
        lut = CMap().load_ct(cmap_name)
        if lut is not None:
            self.ct = lut
            self.ct_name = cmap_name
            for img in self.imgs.values():
                img.set_lut(self.ct)

    def set_crosshair_to_mouse(self):
        if self.mouse_panel[:3] == 'lin':
            coord = self.mouse_panel[-1]
            i = self.coord_to_index[coord]
            if self.lineplots[coord][1] == 'h':
                self.cursor.set_pos(i, self.mouse_pos.x())
            else:
                self.cursor.set_pos(i, self.mouse_pos.y())
        elif self.mouse_panel[:3] == 'img':
            i, j = self.coord_to_index[self.mouse_panel[-2:]]
            self.cursor.set_pos(i, self.mouse_pos.x())
            self.cursor.set_pos(j, self.mouse_pos.y())
        else:
            raise NotImplementedError("Mouse panel {0} is unknown".format(self.mouse_panel))

    def keyReleaseEvent(self, e):
        if e.key() == QtCore.Qt.Key_Shift:
            self.shift_down = False
        else:
            e.ignore()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Shift:
            self.shift_down = True
            self.set_crosshair_to_mouse()
        else:
            e.ignore()

    def lin_hover_handler(self, i: int, lin: pg.PlotItem, evt: tuple):
        if lin.sceneBoundingRect().contains(evt[0]):
            self.mouse_panel = 'lin_' + self.index_to_coord[i]
            mousepnt = lin.vb.mapSceneToView(evt[0])
            self.mouse_pos = mousepnt
            self.status_bar = "{0:#.5g}, {1:#.5g}".format(mousepnt.x(), mousepnt.y())
            self.mouse_hover.emit(self.status_bar)
            if self.shift_down:
                self.set_crosshair_to_mouse()

    def img_hover_handler(self, i: int, j: int, img: pg.ImageItem, evt: HoverEvent):
        """Template function for image hover handler
        i should be index for the x-axis
        j should be index for the y-axis
        img is a reference to the image"""
        if not evt.isExit():
            self.mouse_panel = 'img_' + self.index_to_coord[i] + self.index_to_coord[j]
            mousepnt = img.transform().map(evt.pos())
            self.mouse_pos = mousepnt
            pos = np.array([x.value for x in self.cursor.pos])
            pos[i] = mousepnt.x()
            pos[j] = mousepnt.y()
            idx = np.round((pos - self.data.coord_min)/self.data.delta).astype(np.int)
            if self.data.ndim == 2:
                self.status_bar = "{0:#.3g} : x = {1:#.3g}, y = {2:#.3g} [{3:d},{4:d}]".format(self.data.values[tuple(idx)], *tuple(pos), *tuple(idx))
            elif self.data.ndim == 3:
                self.status_bar = "{0:#.3g} : x = {1:#.3g}, y = {2:#.3g}, z = {3:#.3g} [{4:d},{5:d},{6:d}]".format(self.data.values[tuple(idx)], *tuple(pos), *tuple(idx))
            elif self.data.ndim == 4:
                self.status_bar = "{0:#.3g} : x = {1:#.3g}, y = {2:#.3g}, z = {3:#.3g}, t = {4:#.4g} [{5:d},{6:d},{7:d},{8:d}]".format(self.data.values[tuple(idx)], *tuple(pos), *tuple(idx))
            else:
                raise RuntimeError("The data ndim for an image is not 2, 3, or 4")
            self.mouse_hover.emit(self.status_bar)
            if self.shift_down:
                self.set_crosshair_to_mouse()


class Cursor:
    """An object that holds a list of current index and position of the cursor location. Warning: this function
    will raise a list indexing error if you access y, z, or t variables on data which does not have that as a
    dimension.
    """
    def __init__(self, data: RegularDataArray):
        """
        :param data: Regular spaced data, which will be used to calculate how to transform axis to coordinate
        """
        self.data = data
        self._index: List[ValueLimitedModel] = [ValueLimitedModel(0, 0, imax) for imax in np.array(data.shape) - 1]
        self._pos: List[ValueLimitedModel] = [ValueLimitedModel(cmin, cmin, cmax)
                                              for cmin, cmax in zip(data.coord_min, data.coord_max)]
        self._binwidth: List[ValueLimitedModel] = [ValueLimitedModel(0, 0, cmax)
                                                   for cmax in (data.coord_max - data.coord_min)]
        self._binpos: List[List[float]] = [[cmin, cmin + delta/2] for cmin, delta in zip(data.coord_min, data.delta)]

    @property
    def pos(self):
        return self._pos

    @property
    def index(self):
        return self._index

    @property
    def binwidth(self):
        return self._binwidth

    def get_binwidth(self, i):
        return self._binwidth[i].value

    def get_pos(self, axis):
        if isinstance(axis, str):
            i = PGImageTool.coord_to_index[axis]
        else:
            i = int(axis)
        return self._pos[i].value

    def get_index(self, axis):
        if isinstance(axis, str):
            i = PGImageTool.coord_to_index[axis]
        else:
            i = int(axis)
        return self._index[i].value

    def get_slice(self):
        return tuple(self.get_index_slice(i) for i in range(self.data.ndim))

    def get_index_slice(self, i):
        """Using the known binwidth and bin positions, calculate a slice in index space
        Note: if the binwidth <= delta (or the bin index is 1), there will never be any binning
        """
        if self._binwidth[i].value > self.data.delta[i]:
            self._binpos[i][0] = min(max(self._pos[i].value - self._binwidth[i].value / 2, self.data.coord_min[i]),
                                     self.data.coord_max[i])
            self._binpos[i][1] = min(max(self._pos[i].value + self._binwidth[i].value / 2, self.data.coord_min[i]),
                                     self.data.coord_max[i])
            mn = int(np.ceil(self.data.scale_to_index(i, self._binpos[i][0])))
            mx = int(np.floor(self.data.scale_to_index(i, self._binpos[i][1])))
            return slice(mn, mx + 1)
        else:
            return slice(self._index[i].value, self._index[i].value + 1)

    def get_cut(self, axis: Union[int, Iterable]):
        if not isinstance(axis, Iterable):
            axis = [axis]
        else:
            axis = list(axis)
        axis_cmpl = tuple(filter(lambda x: x not in axis, range(self.data.ndim)))
        selection = tuple(slice(None) if i in axis else self.get_index_slice(i) for i in range(self.data.ndim))
        return self.data.isel(*selection).mean(axis_cmpl).squeeze()

    def set_pos(self, i, newpos):
        newpos = self._pos[i].set_value(newpos)
        newindex = round(self.data.scale_to_index(i, newpos))
        self._index[i].set_value(newindex)

    def set_index(self, i, newindex):
        newindex = self._index[i].set_value(newindex)
        newpos = self.data.index_to_scale(i, newindex)
        self._pos[i].set_value(newpos)

    def set_binwidth(self, i, newwidth):
        self._binwidth[i].set_value(newwidth)

    def set_binwidth_i(self, i, newindex):
        newindex = min(max(0, round(newindex)), self.data.shape[i] - 1)
        self._binwidth[i].set_value(newindex*self.data.delta[i])

    def reset(self, data=None):
        if data is not None:
            self.data = data
            for i in range(self.data.ndim):
                self._index[i]._lower_lim = 0
                self._index[i]._upper_lim = self.data.shape[i] - 1
                self._pos[i]._lower_lim = self.data.coord_min[i]
                self._pos[i]._upper_lim = self.data.coord_max[i]
                self._binwidth[i]._lower_lim = 0
                self._binwidth[i]._upper_lim = self.data.coord_max[i] - self.data.coord_min[i]
                self._binpos = [[cmin, cmin + delta/2] for cmin, delta in zip(self.data.coord_min, self.data.delta)]
        for i in range(self.data.ndim):
            self.set_index(i, 0)
            self.set_binwidth_i(i, 1)
