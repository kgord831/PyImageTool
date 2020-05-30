import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent
from .DataMatrix import RegularDataArray
from .ImageSlice import ImageSlice
from .CMapEditor import load_ct
from typing import Dict, List, Tuple
from functools import partial


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
        self.cursor_lines: Dict[str, List[InfiniteLineBinning]] = {}  # dict of cursor lines for 'x', 'y', 'z', etc.
        # self.bin_widths: List[SingleValueModel] = \
        #     [SingleValueModel(1.0) for i in range(data.ndim)]  # each dimension has a bin width
        self.imgs: Dict[str, ImageSlice] = {}  # a dictionary of ImageItems
        self.img_tr: Dict[str, QtGui.QTransform] = {}  # a dictionary of transforms going from index to coordinates
        self.img_tr_inv: Dict[str, QtGui.QTransform] = {}  # a dictionary of transforms going from coordinates to index
        self._signal_proxies: List[pg.SignalProxy] = []  # a list of created signal proxies to be held in memory
        # Properties for color map
        self.ct: np.array = np.array([])
        self.ct_name: str = 'viridis'
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
        self.cursor.reset()
        # for i in range(self.data.ndim):
        #     self.cursor.set_index(i, 0)
        # Set the new data
        self.data = data
        # Update the line cuts
        for key, (plot_item, orientation) in self.lineplots_data.items():
            # Set the initial data
            i = self.coord_to_index[key]
            linedata = self.data_slice1d(i)
            if orientation == 'h':
                plot_item.setData(self.data.axes[i], linedata)
            else:
                plot_item.setData(linedata, self.data.axes[i])
        # Update the image plots
        for key, img_ax in self.imgs.items():
            i, j = self.coord_to_index[key]
            sl = [slice(None) if x == i or x == j else 0 for x in range(self.data.ndim)]
            selector = {self.data.dims[i]: sl[i] for i in range(self.data.ndim)}
            if j > i:
                img_ax.set_data(self.data.isel(selector))
            else:
                img_ax.set_data(self.data.isel(selector).T)
            if img_ax.aspect_ui.lockAspect.isChecked():
                img_ax.aspect_ui.lockAspect.click()
            img_ax.vb.setXRange(self.data.coord_min[i], self.data.coord_max[i])
            img_ax.vb.setYRange(self.data.coord_min[j], self.data.coord_max[j])
        # Update the cursor lines
        for coord in list(self.imgs.keys()) + list(self.lineplots.keys()):
            if len(coord) == 1:
                i = self.coord_to_index[coord]
                if coord in self.cursor_lines:
                    for line in self.cursor_lines[coord]:
                        line.reset(axis_min=self.data.coord_min[i], axis_delta=self.data.delta[i],
                                   bounds=(self.data.coord_min[i], self.data.coord_max[i]))
            elif len(coord) == 2:
                i, j = self.coord_to_index[coord]
                if coord in self.cursor_lines:
                    for line in self.cursor_lines[coord]:
                        if line.line.angle == 0:
                            line.reset(axis_min=self.data.coord_min[i], axis_delta=self.data.delta[i],
                                       bounds=(self.data.coord_min[i], self.data.coord_max[i]))
                        else:
                            line.reset(axis_min=self.data.coord_min[j], axis_delta=self.data.delta[j],
                                       bounds=(self.data.coord_min[j], self.data.coord_max[j]))
            else:
                raise RuntimeError("A key in the imgs and lineplots dictionary has length {0}".format(len(coord)))
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
                self.lineplots['x'][0].setXLink(self.imgs['xy'])
                self.imgs['xy'].setXLink(self.imgs['xz'])
                self.lineplots['y'][0].setYLink(self.imgs['xy'])
                self.imgs['xy'].setYLink(self.imgs['zy'])
                # TODO: override the autoscale so that the sigRangeChangedManually is emitted
                # TODO: find a cleaner way to do this
                def onSigZRangeChanged(_):
                    self.imgs['xz'].setYRange(*self.lineplots['z'][0].getViewBox().viewRange()[0])
                    self.imgs['zy'].setXRange(*self.lineplots['z'][0].getViewBox().viewRange()[0])
                def onSigXZRangeChanged(_):
                    self.lineplots['z'][0].setXRange(*self.imgs['xz'].getViewBox().viewRange()[1])
                def onSigZYRangeChanged(_):
                    self.lineplots['z'][0].setXRange(*self.imgs['zy'].getViewBox().viewRange()[0])
                self.lineplots['z'][0].getViewBox().sigRangeChangedManually.connect(onSigZRangeChanged)
                self.imgs['xz'].getViewBox().sigRangeChangedManually.connect(onSigXZRangeChanged)
                self.imgs['zy'].getViewBox().sigRangeChangedManually.connect(onSigZYRangeChanged)
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
                    'axis_min': self.data.coord_min[i], 'axis_delta': self.data.delta[i],
                    'bounds': (self.data.coord_min[i], self.data.coord_max[i])}
            cursor_line = InfiniteLineBinning(**args)
            cursor_line.addToItem(plotitem)
            cursor_line.sigDragged.connect(partial(self.cursor.set_pos, i))
            self.cursor.pos[i].value_changed.connect(cursor_line.update_value)
            self.cursor.bin_width[i].value_changed.connect(cursor_line.update_binwidth)
            self.cursor_lines[key] = [cursor_line]  # guaranteed to be the only item

        # Create an image item corresponding to each axis
        for key, img_ax in self.imgs.items():
            i, j = self.coord_to_index[key]
            sl = [slice(None) if x == i or x == j else 0 for x in range(self.data.ndim)]
            selector = {self.data.dims[i]: sl[i] for i in range(self.data.ndim)}
            if j > i:
                img_ax.set_data(self.data.isel(selector), lut=self.ct)
            else:
                img_ax.set_data(self.data.isel(selector).T, lut=self.ct)
            self.img_tr[key] = img_ax.img.transform()
            self.img_tr_inv[key], _ = img_ax.img.transform().inverted()

            # Add hover event
            img_ax.img.hoverEvent = partial(self.img_hover_handler, i, j, img_ax.img)

            # Add a binning line
            # in my convention, i is always the horizontal axis (vert_cursor) in an image plot
            args1 = {'pos': self.data.coord_min[i], 'angle': 90, 'bin_pen': self.bin_pen, 'movable': True,
                     'axis_min': self.data.coord_min[i], 'axis_delta': self.data.delta[i],
                     'bounds': (self.data.coord_min[i], self.data.coord_max[i])}
            args2 = {'pos': self.data.coord_min[j], 'angle': 0, 'bin_pen': self.bin_pen, 'movable': True,
                     'axis_min': self.data.coord_min[j], 'axis_delta': self.data.delta[j],
                     'bounds': (self.data.coord_min[j], self.data.coord_max[j])}
            vert_cursor = InfiniteLineBinning(**args1)
            horz_cursor = InfiniteLineBinning(**args2)
            vert_cursor.sigDragged.connect(partial(self.cursor.set_pos, i))
            self.cursor.pos[i].value_changed.connect(vert_cursor.update_value)
            horz_cursor.sigDragged.connect(partial(self.cursor.set_pos, j))
            self.cursor.pos[j].value_changed.connect(horz_cursor.update_value)
            self.cursor.bin_width[i].value_changed.connect(vert_cursor.update_binwidth)
            self.cursor.bin_width[j].value_changed.connect(horz_cursor.update_binwidth)
            axis0, axis1 = tuple(key)
            if axis0 in self.cursor_lines:
                self.cursor_lines[axis0].append(vert_cursor)
            else:
                self.cursor_lines[axis0] = [vert_cursor]
            if axis1 in self.cursor_lines:
                self.cursor_lines[axis1].append(horz_cursor)
            else:
                self.cursor_lines[axis1] = [horz_cursor]
            vert_cursor.addToItem(img_ax)
            horz_cursor.addToItem(img_ax)
            img_ax.autoRange()

    def init_data(self):
        for key, (plot_item, orientation) in self.lineplots_data.items():
            # Set the initial data
            i = self.coord_to_index[key]
            linedata = self.data_slice1d(i)
            if orientation == 'h':
                plot_item.setData(self.data.axes[i], linedata)
            else:
                plot_item.setData(linedata, self.data.axes[i])
            # Listen to all cursor indices (except this one) and connect to update function
            for j in range(self.data.ndim):
                if j != i:
                    self.cursor.index[j].value_changed.connect(partial(self.update_line, i, plot_item, orientation))
                    self.cursor.bin_width[j].value_changed.connect(partial(self.update_line, i, plot_item, orientation))
        for key, img_ax in self.imgs.items():
            # Wire up events
            i, j = self.coord_to_index[key]
            for k in range(self.data.ndim):
                if k != i and k != j:
                    self.cursor.index[k].value_changed.connect(partial(self.update_img, i, j, img_ax.img))
                    self.cursor.bin_width[k].value_changed.connect(partial(self.update_img, i, j, img_ax.img))

    def update_img(self, i: int, j: int, img: pg.ImageItem):
        """Template function for creating image update callback functions.
        i is the row axis, j is the col axis corresponding to the image. xy is 0, 1 and zy is 2, 1"""
        data_slice = [self.cursor.index[i].val for i in range(self.data.ndim)]
        data_slice[i] = slice(None)
        data_slice[j] = slice(None)
        if j > i:
            img.setImage(self.data_slice2d(i, j))
        else:
            img.setImage(self.data_slice2d(i, j).T)

    def update_line(self, index: int, lineplot: pg.PlotDataItem, orientation: str):
        """Template function for creating callbacks which update every PlotDataItem according to current cursor
        position."""
        linedata = self.data_slice1d(index)
        if orientation == 'h':
            lineplot.setData(self.data.axes[index], linedata)
        else:
            lineplot.setData(linedata, self.data.axes[index])

    def data_slice1d(self, index: int) -> np.array:
        """Given a dimension index, return a 1d array that slices through cursor position at index"""
        # Start at cursor indices
        data_slice = [self.cursor.get_index_slice(i) for i in range(self.data.ndim)]
        # Grab all values for index
        data_slice[index] = slice(None)
        # Average over all dimensions except for index
        avg_over = tuple([i for i in range(self.data.ndim) if i != index])
        avg = np.mean(self.data.values[tuple(data_slice)], axis=avg_over)
        return avg

    def data_slice2d(self, i: int, j: int) -> np.array:
        """Given two dimensions, return a 2d array that slices through cursor position at i, j"""
        data_slice = [self.cursor.get_index_slice(i) for i in range(self.data.ndim)]
        data_slice[i] = slice(None)
        data_slice[j] = slice(None)
        avg_over = tuple([x for x in range(self.data.ndim) if x != i and x != j])
        avg = np.mean(self.data.values[tuple(data_slice)], axis=avg_over)
        return avg

    def load_ct(self, cmap_name: str = 'viridis'):
        """
        Supported color maps:
        - viridis
        - inferno
        - magma
        - plasma
        - CET color maps (https://peterkovesi.com/projects/colourmaps/)
        """
        lut = load_ct(cmap_name)
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
            pos = np.array([x.val for x in self.cursor.pos])
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
        self._index: List[SingleValueModel] = [SingleValueModel(0) for i in range(data.ndim)]
        self._pos: List[SingleValueModel] = [SingleValueModel(float(self.data.coord_min[i])) for i in range(data.ndim)]
        self._binwidth: List[SingleValueModel] = [SingleValueModel(data.delta[i]) for i in range(data.ndim)]
        self._binpos: List[List[float]] = [[data.coord_min[i], data.coord_min[i] + data.delta[i]/2]
                                           for i in range(data.ndim)]

    @property
    def pos(self):
        return self._pos

    @property
    def index(self):
        return self._index

    @property
    def bin_width(self):
        return self._binwidth

    def get_pos(self, axis):
        if isinstance(axis, str):
            i = PGImageTool.coord_to_index[axis]
        else:
            i = int(axis)
        return self._pos[i].val

    def get_index(self, axis):
        if isinstance(axis, str):
            i = PGImageTool.coord_to_index[axis]
        else:
            i = int(axis)
        return self._index[i].val

    def get_index_slice(self, i):
        """Using the known binwidth and bin positions, calculate a slice in index space
        Note: if the binwidth <= delta (or the bin index is 1), there will never be any binning
        """
        if self._binwidth[i].val <= self.data.delta[i]:
            return slice(self._index[i].val, self._index[i].val + 1)
        else:
            mn = int(np.ceil(self.data.scale_to_index(i, self._binpos[i][0])))
            mx = int(np.floor(self.data.scale_to_index(i, self._binpos[i][1])))
            return slice(mn, mx + 1)

    def get_binwidth(self, i):
        return self._binwidth[i].val

    def set_pos(self, i, newval, force=False):
        newval = min(max(self.data.coord_min[i], newval), self.data.coord_max[i])
        newindex = int(np.round((newval - self.data.coord_min[i])/self.data.delta[i]))
        if force or newval != self._pos[i].val:
            self._binpos[i][0] = min(max(self.data.coord_min[i], newval - self._binwidth[i].val / 2),
                                     self.data.coord_max[i])
            self._binpos[i][1] = min(max(self.data.coord_min[i], newval + self._binwidth[i].val / 2),
                                     self.data.coord_max[i])
            self._pos[i].val = newval
        if force or newindex != self._index[i].val:
            self._index[i].val = newindex

    def set_index(self, i, newindex, force=False):
        newindex = min(max(0, round(newindex)), self.data.shape[i] - 1)
        if force or newindex != self._index[i].val:
            newpos = self.data.coord_min[i] + newindex*self.data.delta[i]
            self._binpos[i][0] = min(max(self.data.coord_min[i], newpos - self._binwidth[i].val / 2),
                                     self.data.coord_max[i])
            self._binpos[i][1] = min(max(self.data.coord_min[i], newpos + self._binwidth[i].val / 2),
                                     self.data.coord_max[i])
            self._index[i].val = newindex
            self._pos[i].val = newpos

    def set_binwidth(self, i, newval, force=False):
        newval = min(max(self.data.delta[i], newval),
                     self.data.coord_max[i] - self.data.coord_min[i] + self.data.delta[i])
        if force or newval != self._binwidth[i].val:
            self._binpos[i][0] = min(max(self.data.coord_min[i], self._pos[i].val - newval / 2),
                                     self.data.coord_max[i])
            self._binpos[i][1] = min(max(self.data.coord_min[i], self._pos[i].val + newval / 2),
                                     self.data.coord_max[i])
            self._binwidth[i].val = newval

    def set_binwidth_i(self, i, newindex, force=False):
        newindex = min(max(1, round(newindex)), self.data.shape[i])
        if force or newindex != int(round(self._binwidth[i].val / self.data.delta[i])):
            new_width = newindex*self.data.delta[i]
            self._binpos[i][0] = min(max(self.data.coord_min[i], self._pos[i].val - new_width / 2),
                                     self.data.coord_max[i])
            self._binpos[i][1] = min(max(self.data.coord_min[i], self._pos[i].val + new_width / 2),
                                     self.data.coord_max[i])
            self._binwidth[i].val = new_width

    def reset(self, data=None):
        if data is not None:
            self.data = data
            for i in range(self.data.ndim):
                self._binwidth[i].set_val(self.data.delta[i], block=True)
                self._binpos[i][0] = min(max(self.data.coord_min[i], self._pos[i].val - self.data.delta[i] / 2),
                                         self.data.coord_max[i])
                self._binpos[i][1] = min(max(self.data.coord_min[i], self._pos[i].val + self.data.delta[i] / 2),
                                         self.data.coord_max[i])
        for i in range(self.data.ndim):
            self.set_index(i, 0, True)
            self.set_binwidth_i(i, 1, True)

class SingleValueModel(QtCore.QObject):
    """A cursor position is either a float or int (determined at instantiation) and preserves the type in assignment.
    Furthermore, the object emits either an int or float pyqtSignal when the value is changed through the setter."""
    value_changed = QtCore.Signal(object)

    def __init__(self, val: object):
        super().__init__()
        self._val = val

    def set_val(self, newval, block=False):
        if type(self._val) is type(newval):
            self._val = newval
        else:
            self._val = type(self._val)(newval)
        if not block:
            self.value_changed.emit(self._val)

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, newval):
        if type(self._val) is type(newval):
            self._val = newval
        else:
            self._val = type(self._val)(newval)
        self.value_changed.emit(self._val)

    @QtCore.pyqtSlot(object)
    def on_value_changed(self, newval):
        self.val = newval


class InfiniteLineBinning(pg.GraphicsObject):
    """
    A convenience class that subclasses pyqtgraph's Infinite Line, but includes internal functions for controlling parallel lines that represent the binning window.
    Requires some information about the axis the line is tied to, for convenience in slicing a data array.
    It's hacky. This object just holds three InfiniteLines and has an addTo function for adding to pg widgets.
    It also defined a sigDragged signals which emits the new position the line has been dragged to.
    """
    sigDragged = QtCore.Signal(object)

    def __init__(self, pos=None, angle=90, pen=None, bin_pen=None, movable=False, axis_min=0, axis_delta=1, bounds=None,
                 hoverPen=None, label=None, labelOpts=None, name=None):
        pg.GraphicsObject.__init__(self)
        self._binwidth: int = 1  # pixel bin width
        self.delta: np.array = axis_delta
        self.min = axis_min
        self.line = pg.InfiniteLine(pos=pos, angle=angle, pen=None, movable=True, bounds=bounds, hoverPen=hoverPen,
                                    label=label, labelOpts=labelOpts, name='center')
        self.bin1 = pg.InfiniteLine(pos=pos, angle=angle, pen=bin_pen, movable=False, bounds=bounds, hoverPen=hoverPen,
                                    label=label, labelOpts=labelOpts, name='left')
        self.bin2 = pg.InfiniteLine(pos=pos, angle=angle, pen=bin_pen, movable=False, bounds=bounds, hoverPen=hoverPen,
                                    label=label, labelOpts=labelOpts, name='right')
        self.bin1.setVisible(False)
        self.bin2.setVisible(False)
        self.line.sigDragged.connect(self.on_dragged)

    def reset(self, axis_min=0, axis_delta=1, bounds=None):
        self.delta = axis_delta
        self.min = axis_min
        for x in [self.line, self.bin1, self.bin2]:
            x.setBounds(bounds)

    @property
    def binwidth(self):
        return self._binwidth

    # @binwidth.setter
    # def binwidth(self, idx):
    #     self._binwidth = int(round(idx))
    #     self.updateBinLines()

    def set_binwidth(self, val):
        self._binwidth = int(round(val / self.delta))
        self.updateBinLines()

    @property
    def pos(self):
        return self.value()

    @property
    def idx(self):
        return int(round((self.value() - self.min) / self.delta))

    @property
    def binpos(self):
        return self.bin1.value(), self.bin2.value()

    @property
    def binindex(self):
        return int(np.ceil((self.bin1.value() - self.min) / self.delta)), int(
            np.floor((self.bin2.value() - self.min) / self.delta))

    @property
    def binslice(self):
        if self._binwidth > 1:
            return slice(*self.binindex)
        else:
            return slice(self.idx, self.idx + 1)

    def setValue(self, newval):
        self.line.setValue(newval)
        self.updateBinLines()

    def updateBinLines(self):
        if self._binwidth > 1:
            self.bin1.setVisible(True)
            self.bin2.setVisible(True)
        else:
            self.bin1.setVisible(False)
            self.bin2.setVisible(False)
        self.bin1.setValue(self.value() - self._binwidth / 2 * self.delta)
        self.bin2.setValue(self.value() + self._binwidth / 2 * self.delta)

    def addToItem(self, addto):
        """
        This function is a hack. I should be writing a paint and boundingRect function
        with these items as children, but I don't know how to write it.
        """
        addto.addItem(self.line)
        addto.addItem(self.bin1)
        addto.addItem(self.bin2)

    def pixelToPos(self, px):
        return self.min + px * self.delta

    def value(self):
        return self.line.value()

    @QtCore.pyqtSlot()
    def on_dragged(self):
        self.sigDragged.emit(self.line.value())

    @QtCore.pyqtSlot(object)
    def update_value(self, newval):
        if type(newval) == tuple:  # when using SignalProxy, it is possible that this becomes a tuple with single value
            newval = float(newval[0])
        self.setValue(newval)

    @QtCore.pyqtSlot(object)
    def update_binwidth(self, newwidth):
        self.set_binwidth(newwidth)
        self.updateBinLines()
