# -*- coding: utf-8 -*-
"""
Demonstrate a simple data-slicing task: given 3D data (displayed at top), select 
a 2D plane and interpolate data along that plane to generate a slice image 
(displayed at bottom). 
"""

import numpy as np
import fnmatch
import os
import xarray as xr
import h5py
import sip
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent

from .widgets import AspectRatioForm, InfoBar
from .PGImageTool import InfiniteLineBinning
from .DataMatrix import RegularSpacedData


class ImageToolWidget(QtWidgets.QWidget):
    def __init__(self, data: RegularSpacedData, cmap='viridis', pos=None, parent=None):
        super().__init__(parent)
        # self.setWindowTitle('Image Tool (2D)')
        self.data = data
        self.setLayout(QtWidgets.QVBoxLayout())
        self.info_bar = InfoBar(data)
        self.layout().addWidget(self.info_bar)
        if pos is None:
            self._pos = np.copy(self.data.coord_min)
            self._idx = np.zeros(self.data.dims, dtype=np.int)
        else:
            self._pos = pos
            self._idx = np.round((pos - self.data.coord_min)/self.data.delta).astype(np.int)
        self.pos_subscribers = [[], [], []]
        self.ct = np.array([])
        self.ct_name = ''
        self.load_ct(cmap)
        self.build()

    def set_data(self, data: RegularSpacedData):
        self.data = data
        self.layout().removeWidget(self.info_bar)
        sip.delete(self.info_bar)  # https://stackoverflow.com/questions/5899826/pyqt-how-to-remove-a-widget
        self.info_bar = InfoBar(data)
        self.layout().addWidget(self.info_bar)

    def load_ct(self, cmap_name: str = 'viridis'):
        """
        Supported color maps:
        - viridis
        - inferno
        - magma
        - plasma
        - CET color maps (https://peterkovesi.com/projects/colourmaps/)
        """
        path = 'cmaps' + os.sep + cmap_name + '.npy'
        if os.path.isfile(path):
            self.ct = np.load('cmaps' + os.sep + cmap_name + '.npy')
            self.ct_name = cmap_name
        else:
            print('Color map: {} not found!'.format(cmap_name))
            self.ct = np.load('cmaps' + os.sep + 'viridis.npy')
            self.ct_name = 'viridis'

    def set_image(self):
        if self.data.dims == 2:
            self.img.setImage(self.data.mat[:, :], lut=self.ct)
        elif self.data.dims == 3:
            if self.bin_z_sb.value() > 1:
                try:
                    self.img.setImage(np.nanmean(self.data.mat[:, :, self.zline_cs.binslice], axis=2))
                except RuntimeWarning:
                    pass
            else:
                self.img.setImage(self.data.mat[:, :, self.idx[2]], lut=self.ct)
            self.update_v_cs()
            self.update_h_cs()

    def build(self):
        # Main layout
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Menu bar
        # transposeAction = QtGui.QAction("&Transpose Data!!!", self)
        # transposeAction.setShortcut("Ctrl+Q")
        # transposeAction.setStatusTip('Transpose axes')
        # transposeAction.triggered.connect(self.close_application)

        # Create the info bar
        self.info_bar_layout = QtWidgets.QHBoxLayout()
        # Cursor Info
        self.cursor1_info = QtWidgets.QGroupBox("Cursor Info")
        self.x1_text = QtWidgets.QLabel('X')
        self.y1_text = QtWidgets.QLabel('Y')
        self.i_label = QtWidgets.QLabel('Index')
        self.c_label = QtWidgets.QLabel('Coord')
        self.x1_i_sb = QtWidgets.QSpinBox()
        self.y1_i_sb = QtWidgets.QSpinBox()
        self.x1_c_sb = QtWidgets.QDoubleSpinBox()
        self.y1_c_sb = QtWidgets.QDoubleSpinBox()
        self.x1_i_sb.setRange(0, self.data.N[0] - 1)
        self.y1_i_sb.setRange(0, self.data.N[1] - 1)
        self.x1_c_sb.setRange(self.data.coord_min[0], self.data.coord_max[0])
        self.y1_c_sb.setRange(self.data.coord_min[1], self.data.coord_max[1])
        self.x1_i_sb.valueChanged.connect(self.updateVLineIdxBox)
        self.y1_i_sb.valueChanged.connect(self.updateHLineIdxBox)
        self.pos_subscribers[0].append(self.x1_c_sb)
        self.pos_subscribers[1].append(self.y1_c_sb)
        self.cursor1_info_layout = QtWidgets.QGridLayout()
        self.cursor1_info_layout.addWidget(self.i_label, 0, 1)
        self.cursor1_info_layout.addWidget(self.c_label, 0, 2)
        self.cursor1_info_layout.addWidget(self.x1_text, 1, 0)
        self.cursor1_info_layout.addWidget(self.x1_i_sb, 1, 1)
        self.cursor1_info_layout.addWidget(self.x1_c_sb, 1, 2)
        self.cursor1_info_layout.addWidget(self.y1_text, 2, 0)
        self.cursor1_info_layout.addWidget(self.y1_i_sb, 2, 1)
        self.cursor1_info_layout.addWidget(self.y1_c_sb, 2, 2)
        if self.data.dims == 3:
            self.z1_text = QtWidgets.QLabel('Z')
            self.z1_i_sb = QtWidgets.QSpinBox()
            self.z1_i_sb.setRange(0, self.data.N[2] - 1)
            self.z1_c_sb = QtWidgets.QDoubleSpinBox()
            self.z1_c_sb.setRange(self.data.coord_min[2], self.data.coord_max[2])
            self.z1_c_sb.setValue(self.data.coord_min[2])
            self.z1_i_sb.valueChanged.connect(self.updateZLineIdxBox)
            self.pos_subscribers[2].append(self.z1_c_sb)
            self.cursor1_info_layout.addWidget(self.z1_text, 3, 0)
            self.cursor1_info_layout.addWidget(self.z1_i_sb, 3, 1)
            self.cursor1_info_layout.addWidget(self.z1_c_sb, 3, 2)
        self.cursor1_info.setLayout(self.cursor1_info_layout)
        self.info_bar_layout.addWidget(self.cursor1_info)
        # Binning
        self.bin_info = QtWidgets.QGroupBox("Binning")
        self.bin_v_text = QtWidgets.QLabel('X')
        self.bin_h_text = QtWidgets.QLabel('Y')
        self.bin_h_sb = QtWidgets.QSpinBox()
        self.bin_v_sb = QtWidgets.QSpinBox()
        self.bin_h_sb.setRange(1, self.data.N[1])
        self.bin_v_sb.setRange(1, self.data.N[0])
        self.bin_h_sb.editingFinished.connect(self.updateBinH)
        self.bin_v_sb.editingFinished.connect(self.updateBinV)
        self.bin_info_layout = QtWidgets.QGridLayout()
        self.bin_info_layout.addWidget(self.bin_v_text, 0, 0)
        self.bin_info_layout.addWidget(self.bin_h_text, 1, 0)
        self.bin_info_layout.addWidget(self.bin_v_sb, 0, 1)
        self.bin_info_layout.addWidget(self.bin_h_sb, 1, 1)
        if self.data.dims == 3:
            self.bin_z_text = QtWidgets.QLabel('Z')
            self.bin_z_sb = QtWidgets.QSpinBox()
            self.bin_z_sb.setRange(1, self.data.N[2])
            self.bin_z_sb.editingFinished.connect(self.updateBinZ)
            self.bin_info_layout.addWidget(self.bin_z_text, 2, 0)
            self.bin_info_layout.addWidget(self.bin_z_sb, 2, 1)
        self.bin_info.setLayout(self.bin_info_layout)
        self.info_bar_layout.addWidget(self.bin_info)
        # Colors
        self.colors_info = QtWidgets.QGroupBox("Colors")
        self.cmap_text = QtWidgets.QLabel()
        self.cmap_text.setText('Color Map')
        self.cmap_cb = QtWidgets.QComboBox()
        for filename in os.listdir('cmaps'):
            if fnmatch.fnmatch(filename, '*.npy'):
                cmap_name = os.path.splitext(filename)[0]
                self.cmap_cb.addItem(QtGui.QIcon('cmaps' + os.sep + cmap_name + '.jpg'), cmap_name)
        self.cmap_cb.setCurrentText(self.ct_name)
        def update_cmap(cmap_name):
            cmap = np.load('cmaps' + os.sep + cmap_name + '.npy')
            self.ct = cmap
            self.img.setLookupTable(cmap)
        self.cmap_cb.currentTextChanged.connect(update_cmap)
        self.colors_info_layout = QtWidgets.QGridLayout()
        self.colors_info_layout.addWidget(self.cmap_text, 0, 0)
        self.colors_info_layout.addWidget(self.cmap_cb, 0, 1)
        self.colors_info.setLayout(self.colors_info_layout)
        self.info_bar_layout.addWidget(self.colors_info)
        # Append to main
        self.mainLayout.addLayout(self.info_bar_layout)

        # PyQtGraph
        self.gwin = pg.GraphicsLayoutWidget()
        self.mainLayout.addWidget(self.gwin)

        # A plot area for displaying the image
        self.v_cs = self.gwin.addPlot()
        self.v_cs_proxy = pg.SignalProxy(self.v_cs.scene().sigMouseMoved, rateLimit=60, slot=self.v_cs_hover_handler)
        # self.v_cs.hoverEvent = self.v_cs_hover_handler
        self.p1 = self.gwin.addPlot()
        self.p1.setMenuEnabled(enableMenu=False, enableViewBoxMenu=None)

        if self.data.dims == 3:
            self.z_cs = self.gwin.addPlot(rowspan=2)
            self.z_cs_proxy = pg.SignalProxy(self.z_cs.scene().sigMouseMoved, rateLimit=60, slot=self.z_cs_hover_handler)
        self.gwin.nextRow()
        self.gwin.nextCol()
        self.h_cs = self.gwin.addPlot()
        self.h_cs_proxy = pg.SignalProxy(self.h_cs.scene().sigMouseMoved, rateLimit=60, slot=self.h_cs_hover_handler)
        self.v_cs.setYLink(self.p1.getViewBox())
        self.h_cs.setXLink(self.p1.getViewBox())
        self.gwin.ci.layout.setColumnStretchFactor(0, 1)
        self.gwin.ci.layout.setColumnStretchFactor(1, 2)
        self.gwin.ci.layout.setRowStretchFactor(0, 2)
        self.gwin.ci.layout.setRowStretchFactor(1, 1)
        
        self.mouse_pnt = QtCore.QPointF(self.data.coord_min[0], self.data.coord_min[1])
        self.mousePanel = None
        self.shift_down = False

        # Item for displaying image data
        self.img = pg.ImageItem()
        self.img.hoverEvent = self.img_hover_handler
        self.p1.addItem(self.img)

        w = QtGui.QWidget()
        self.aspectUi = AspectRatioForm()
        self.aspectUi.setupUi(w)
        self.aspectUi.aspectRatio.setValidator(QtGui.QDoubleValidator(0, float("inf"), 20))

        self.aspectMenu = QtGui.QMenu('Aspect Ratio')
        self.aspectMenu.setTitle('Aspect Ratio')
        a = QtGui.QWidgetAction(self.p1.vb.menu)
        a.setDefaultWidget(w)
        self.aspectMenu.addAction(a)
        self.p1.vb.menu.addMenu(self.aspectMenu)

        self.aspectUi.lockAspect.stateChanged.connect(self.aspectLockToggle)
        self.aspectUi.aspectRatio.editingFinished.connect(self.aspectLockEdit)

        # Add infinite lines
        bin_pen = pg.mkPen(style=pg.Qt.QtCore.Qt.DashLine)
        self.vline = InfiniteLineBinning(pos=self.data.coord_min[0], angle=90, bin_pen=bin_pen, movable=True, axis_min=self.data.coord_min[0], axis_delta=self.data.delta[0], bounds=[self.data.coord_min[0], self.data.coord_max[0]])
        self.vline.line.sigDragged.connect(self.dragVLine)
        self.pos_subscribers[0].append(self.vline)
        self.vline.addToItem(self.p1)
        self.hline = InfiniteLineBinning(pos=self.data.coord_min[1], angle=0, bin_pen=bin_pen, movable=True, axis_min=self.data.coord_min[1], axis_delta=self.data.delta[1], bounds=[self.data.coord_min[1], self.data.coord_max[1]])
        self.hline.line.sigDragged.connect(self.dragHLine)
        self.pos_subscribers[1].append(self.hline)
        self.hline.addToItem(self.p1)
        self.vline_cs = InfiniteLineBinning(pos=self.vline.value(), angle=90, bin_pen=bin_pen, movable=True, axis_min=self.data.coord_min[0], axis_delta=self.data.delta[0], bounds=[self.data.coord_min[0], self.data.coord_max[0]])
        self.vline_cs.line.sigDragged.connect(self.dragVCSLine)
        self.pos_subscribers[0].append(self.vline_cs)
        self.vline_cs.addToItem(self.h_cs)
        self.hline_cs = InfiniteLineBinning(pos=self.hline.value(), angle=0, bin_pen=bin_pen, movable=True, axis_min=self.data.coord_min[1], axis_delta=self.data.delta[1], bounds=[self.data.coord_min[1], self.data.coord_max[1]])
        self.hline_cs.line.sigDragged.connect(self.dragHCSLine)
        self.pos_subscribers[1].append(self.hline_cs)
        self.hline_cs.addToItem(self.v_cs)
        if self.data.dims == 3:
            self.zline_cs = InfiniteLineBinning(pos=self.data.coord_min[2], angle=0, bin_pen=bin_pen, movable=True, axis_min=self.data.coord_min[2], axis_delta=self.data.delta[2], bounds=[self.data.coord_min[2], self.data.coord_max[2]])
            self.zline_cs.line.sigDragged.connect(self.dragZCSLine)
            self.zline_cs.addToItem(self.z_cs)
            self.pos_subscribers[2].append(self.zline_cs)

        # Initialize the cross-sections
        self.v_cs_line = self.v_cs.plot(np.zeros(self.data.shape[1]), self.data.axes[1])
        self.h_cs_line = self.h_cs.plot(self.data.axes[0], np.zeros(self.data.shape[0]))
        if (self.data.dims == 3):
            self.z_cs_line = self.z_cs.plot(np.zeros(self.data.shape[2]), self.data.axes[2])

        # First update
        self.updateVLine()
        self.updateHLine()
        self.update_v_cs()
        self.update_h_cs()
        if self.data.dims == 3:
            self.update_z_cs()

        # Another plot window displaying the slice
        # self.gwin.resize(800, 800)

        # Set the data
        self.set_image()
        # Set coordinates
        self.index_to_coords = QtGui.QTransform()
        self.index_to_coords.scale(self.data.delta[0], self.data.delta[1])
        self.index_to_coords.translate(self.data.coord_min[0]/self.data.delta[0] - 0.5, self.data.coord_min[1]/self.data.delta[1] - 0.5)
        self.img.setTransform(self.index_to_coords, True)
        self.coords_to_index, _ = self.index_to_coords.inverted()
        self.p1.autoRange()
            
        # Create status bar
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.showMessage("Initialized")
        self.mainLayout.addWidget(self.status_bar)

    @property
    def idx(self):
        return self._idx

    @idx.setter
    def idx(self, idx):
        self.pos = self.data.coord_min + self.data.delta*idx

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, newpos):
        self.setX(newpos[0])
        self.setY(newpos[1])
        if (self.data.dims > 2):
            self.setZ(self.pos[2])

    def setXY(self, newx, newy):
        self.setX(newx)
        self.setY(newy)

    def setX(self, newx):
        self._pos[0] = min(max(newx, self.data.coord_min[0]), self.data.coord_max[0])
        self._idx[0] = int(round((self._pos[0] - self.data.coord_min[0])/self.data.delta[0]))
        for sub in self.pos_subscribers[0]:
            sub.blockSignals(True)
            sub.setValue(self.pos[0])
            sub.blockSignals(False)
        self.updateVLine()
        self.setVLineIdxBox(self.idx[0])
        if self.data.dims == 3:
            self.update_z_cs()
    
    def setY(self, newy):
        self._pos[1] = min(max(newy, self.data.coord_min[1]), self.data.coord_max[1])
        self._idx[1] = int(round((self._pos[1] - self.data.coord_min[1])/self.data.delta[1]))
        for sub in self.pos_subscribers[1]:
            sub.blockSignals(True)
            sub.setValue(self.pos[1])
            sub.blockSignals(False)
        self.updateHLine()
        self.setHLineIdxBox(self.idx[1])
        if self.data.dims == 3:
            self.update_z_cs()
    
    def setZ(self, newz):
        self._pos[2] = min(max(newz, self.data.coord_min[2]), self.data.coord_max[2])
        self._idx[2] = int(round((self._pos[2] - self.data.coord_min[2])/self.data.delta[2]))
        for sub in self.pos_subscribers[2]:
            sub.blockSignals(True)
            sub.setValue(self.pos[2])
            sub.blockSignals(False)
        self.updateZLine()
        self.setZLineIdxBox(self.idx[2])

    def dragVLine(self):
        """Called when dragging the vertical cross section line"""
        self.setX(self.vline.value())

    def dragHLine(self):
        """Called when dragging the horizontal cross section line"""
        self.setY(self.hline.value())
    
    def dragVCSLine(self):
        self.vline.setValue(self.vline_cs.value())
        self.dragVLine()

    def dragHCSLine(self):
        self.hline.setValue(self.hline_cs.value())
        self.dragHLine()

    def dragZCSLine(self):
        self.setZ(self.zline_cs.value())

    def updateVLine(self):
        """Called when pos has changed"""
        self.update_v_cs()
    
    def updateHLine(self):
        """Called when pos has changed"""
        self.update_h_cs()
    
    def updateZLine(self):
        self.set_image()

    @staticmethod
    def setBlockEvents(qobject, newval):
        qobject.blockSignals(True)
        qobject.setValue(newval)
        qobject.blockSignals(False)

    def setVLineIdxBox(self, newval):
        """Called when pos has changed"""
        ImageToolWidget.setBlockEvents(self.x1_i_sb, newval)
    
    def setHLineIdxBox(self, newval):
        """Called when pos has changed"""
        ImageToolWidget.setBlockEvents(self.y1_i_sb, newval)

    def setZLineIdxBox(self, newval):
        """Called when pos has changed"""
        ImageToolWidget.setBlockEvents(self.z1_i_sb, newval)
    
    def setVLinePosBox(self, newval):
        """Called when pos has changed"""
        ImageToolWidget.setBlockEvents(self.x1_c_sb, newval)
    
    def setHLinePosBox(self, newval):
        """Called when pos has changed"""
        ImageToolWidget.setBlockEvents(self.y1_c_sb, newval)

    def setZLinePosBox(self, newval):
        """Called when pos has changed"""
        ImageToolWidget.setBlockEvents(self.z1_c_sb, newval)

    def updateBinHLine(self):
        """Called to update the position of the horizontal binning lines"""
        self.bin_h1.setValue(self.hline.value() - self.bin_h_sb.value()*self.data.delta[1]/2)
        self.bin_h2.setValue(self.hline.value() + self.bin_h_sb.value()*self.data.delta[1]/2)
        self.bin_hcs1.setValue(self.bin_h1.value())
        self.bin_hcs2.setValue(self.bin_h2.value())
    
    def updateBinVLine(self):
        """Called to update the position of the vertical binning lines"""
        self.bin_v1.setValue(self.vline.value() - self.bin_v_sb.value()*self.data.delta[0]/2)
        self.bin_v2.setValue(self.vline.value() + self.bin_v_sb.value()*self.data.delta[0]/2)
        self.bin_vcs1.setValue(self.bin_v1.value())
        self.bin_vcs2.setValue(self.bin_v2.value())
    
    def updateBinZLine(self):
        self.bin_zcs1.setValue(self.zline_cs.value() - self.bin_z_sb.value()*self.data.delta[2]/2)
        self.bin_zcs2.setValue(self.zline_cs.value() + self.bin_z_sb.value()*self.data.delta[2]/2)

    def updateBinH(self):
        """Called to update the width of the horizontal binning lines"""
        self.hline.binwidth = self.bin_h_sb.value()
        self.hline_cs.binwidth = self.bin_h_sb.value()
        self.update_h_cs()
        if self.data.dims == 3:
            self.update_z_cs()
    
    def updateBinV(self):
        """Called to update the width of the vertical binning lines"""
        self.vline.binwidth = self.bin_v_sb.value()
        self.vline_cs.binwidth = self.bin_v_sb.value()
        self.update_v_cs()
        if self.data.dims == 3:
            self.update_z_cs()

    def updateBinZ(self):
        """Called to update the width of the vertical binning lines"""
        self.zline_cs.binwidth = self.bin_z_sb.value()
        self.set_image()

    def update_v_cs(self):
        if self.data.dims == 2:
            dat = np.nanmean(self.data.mat[self.vline.binslice, :], axis=0)
            if np.all(np.isnan(dat)):
                self.v_cs_line.setData(np.zeros(self.data.axes[1].size), self.data.axes[1])
            else:
                self.v_cs_line.setData(dat, self.data.axes[1])
        elif self.data.dims == 3:
            dat = np.nanmean(self.data.mat[self.vline.binslice, :, self.zline_cs.binslice], axis=(0, 2))
            if np.all(np.isnan(dat)):
                self.v_cs_line.setData(np.zeros(self.data.axes[1].size), self.data.axes[1])
            else:
                self.v_cs_line.setData(dat, self.data.axes[1])

    def update_h_cs(self):
        if self.data.dims == 2:
            dat = np.nanmean(self.data.mat[:, self.hline.binslice], axis=1)
            if np.all(np.isnan(dat)):
                self.h_cs_line.setData(self.data.axes[0], np.zeros(self.data.axes[0].size))
            else:
                self.h_cs_line.setData(self.data.axes[0], dat)
        elif self.data.dims == 3:
            dat = np.nanmean(self.data.mat[:, self.hline.binslice, self.zline_cs.binslice], axis=(1, 2))
            if np.all(np.isnan(dat)):
                self.h_cs_line.setData(self.data.axes[0], np.zeros(self.data.axes[0].size))
            else:
                self.h_cs_line.setData(self.data.axes[0], dat)
    
    def update_z_cs(self):
        dat = np.nanmean(self.data.mat[self.vline.binslice, self.hline.binslice, :], axis=(0, 1))
        if np.all(np.isnan(dat)):
            self.z_cs_line.setData(np.zeros(self.data.axes[2].size), self.data.axes[2])
        else:
            self.z_cs_line.setData(np.nanmean(self.data.mat[self.vline.binslice, self.hline.binslice, :], axis=(0, 1)), self.data.axes[2])

    def updateVLineIdxBox(self):
        self.x1_i_sb.setValue(min(max(self.x1_i_sb.value(), 0), self.data.N[0] - 1))
        newx = self.data.coord_min[0] + self.x1_i_sb.value()*self.data.delta[0]
        self.setX(newx)

    def updateVLinePosBox(self):
        self.setX(self.x1_c_sb.value())

    def updateHLineIdxBox(self):
        self.y1_i_sb.setValue(min(max(self.y1_i_sb.value(), 0), self.data.N[1] - 1))
        newy = self.data.coord_min[1] + self.y1_i_sb.value()*self.data.delta[1]
        self.setY(newy)

    def updateHLinePosBox(self):
        self.setY(self.y1_c_sb.value())

    def updateZLineIdxBox(self):
        self.z1_i_sb.setValue(min(max(self.z1_i_sb.value(), 0), self.data.N[2] - 1))
        newz = self.data.coord_min[2] + self.z1_i_sb.value()*self.data.delta[2]
        self.setZ(newz)

    def updateZLinePosBox(self):
        self.setZ(self.z1_c_sb.value())

    def setCrosshairToMouse(self):
        """Called to move the horizontal and vertical cross section lines to the mouse position"""
        self.setXY(self.mouse_pnt.x(), self.mouse_pnt.y())

    # Hover handler for the horizontal line cross section
    def v_cs_hover_handler(self, evt: tuple):
        if self.v_cs.sceneBoundingRect().contains(evt[0]):
            self.mousePanel = 'y'
            mousepnt = self.v_cs.vb.mapSceneToView(evt[0])
            self.mouse_pnt = mousepnt
            if self.shift_down:
                self.setY(mousepnt.y())

    # Hover handler for the vertical line cross section
    def h_cs_hover_handler(self, evt: tuple):
        if self.h_cs.sceneBoundingRect().contains(evt[0]):
            self.mousePanel = 'x'
            mousepnt = self.h_cs.vb.mapSceneToView(evt[0])
            self.mouse_pnt = mousepnt
            if self.shift_down:
                self.setX(mousepnt.x())

    # Hover handler for the z line cross section
    def z_cs_hover_handler(self, evt: tuple):
        if self.z_cs.sceneBoundingRect().contains(evt[0]):
            self.mousePanel = 'z'
            mousepnt = self.z_cs.vb.mapSceneToView(evt[0])
            self.mouse_pnt = mousepnt
            if self.shift_down:
                self.setZ(mousepnt.y())

    def img_hover_handler(self, evt: HoverEvent):
        if not evt.isExit():
            self.mousePanel = 'img'
            mousepnt = self.img.transform().map(evt.pos())
            self.mouse_pnt = mousepnt
            pnt = self.pos
            pnt[0] = mousepnt.x()
            pnt[1] = mousepnt.y()
            idx = np.round((pnt - self.data.coord_min)/self.data.delta).astype(np.int)
            if self.data.dims == 2:
                self.status_bar.showMessage("{0:#.3g} : x = {1:#.3g}, y = {2:#.3g} [{3:d},{4:d}]".format(self.data.mat[tuple(idx)], *tuple(pnt), *tuple(idx)))
            elif self.data.dims == 3:
                self.status_bar.showMessage("{0:#.3g} : x = {1:#.3g}, y = {2:#.3g}, z = {3:#.3g} [{4:d},{5:d},{6:d}]".format(self.data.mat[tuple(idx)], *tuple(pnt), *tuple(idx)))
            if self.shift_down:
                self.setCrosshairToMouse()

    def keyReleaseEvent(self, e):
        if e.key() == QtCore.Qt.Key_Shift:
            self.shift_down = False

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Shift:
            if self.mousePanel == 'img':
                self.setCrosshairToMouse()
            elif self.mousePanel == 'x':
                self.setX(self.mouse_pnt.x())
            elif self.mousePanel == 'y':
                self.setY(self.mouse_pnt.y())
            elif self.mousePanel == 'z':
                self.setZ(self.mouse_pnt.y())
            self.shift_down = True
    
    def aspectLockToggle(self, b):
        if b == QtCore.Qt.Checked:
            a = float(self.aspectUi.aspectRatio.text())
            if a > 0:
                self.p1.setAspectLocked(True, a)
        else:
            self.p1.setAspectLocked(False)
    
    def aspectLockEdit(self):
        if self.aspectUi.lockAspect.isChecked():
            a = float(self.aspectUi.aspectRatio.text())
            if a > 0:
                self.p1.setAspectLocked(True, a)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication([])
    # Generate data
    # dims = 3
    # x = np.linspace(-8, 8, 256)
    # y = np.linspace(-4, 4, 128)
    # if dims == 2:
    #     r = np.sqrt(x[:, np.newaxis]**2 + y[np.newaxis, :]**2)
    # if dims == 3:
    #     z = np.linspace(-6, 6, 64)
    #     r = np.sqrt(x[:, np.newaxis, np.newaxis]**2 + y[np.newaxis, :, np.newaxis]**2 + z[np.newaxis, np.newaxis, :]**2)
    # data_mat = np.sin(np.pi*r)/(np.pi*r)
    # x = np.array([3, 4])
    # y = np.array([2, 4, 6, 8])
    # data_mat = np.array([[1, 2], [20, 4], [4, 1], [1, 2]]).T
    # if dims == 2:
    #     mydata = xr.DataArray(data_mat, coords=[('x', x), ('y', y)])
    # if dims == 3:
    #     mydata = xr.DataArray(data_mat, coords=[('x', x), ('y', y), ('z', z)])

    f = h5py.File('Mn1610_02_00034.h5', 'r')
    counts = np.array(f['data']['counts'])
    exposure = np.array(f['data']['exposure'])
    dat_mat = counts/exposure
    axes = {}
    for index, axis in enumerate(['axis0', 'axis1', 'axis2']):
        if axis == 'axis0':
            axes['perp'] = f['data'][axis].attrs['offset'] + np.arange(dat_mat.shape[index]) * f['data'][axis].attrs['delta']
        elif axis == 'axis1':
            axes['slit'] = f['data'][axis].attrs['offset'] + np.arange(dat_mat.shape[index]) * f['data'][axis].attrs['delta']
        elif axis == 'axis2':
            axes['energy'] = f['data'][axis].attrs['offset'] + np.arange(dat_mat.shape[index]) * f['data'][axis].attrs['delta']
    f.close()

    mydata = xr.DataArray(dat_mat, coords=axes, dims=axes.keys())
    mydata.values[np.isnan(mydata.values)] = 0
    mydata = RegularSpacedData.from_xarray_dataarray(mydata)

    imagetool = ImageToolWidget(mydata)
    imagetool.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
