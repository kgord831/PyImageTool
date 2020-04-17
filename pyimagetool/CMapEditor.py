import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import os
from typing import List, Union
import fnmatch
import numpy as np
import pickle


class CMapDialog(QtWidgets.QDialog):

    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.widget = CMapEditor(image, parent=self)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.widget)
        self.widget.ok_button.clicked.connect(self.accept)
        self.widget.cancel_button.clicked.connect(self.reject)

class CMapEditor(QtWidgets.QWidget):

    def __init__(self, image, parent=None):
        super().__init__(parent)

        # Layout management
        self.main_layout = QtWidgets.QVBoxLayout()
        self.header_layout = QtWidgets.QHBoxLayout()
        self.cmap_norm_layout = QtWidgets.QHBoxLayout()
        self.gamma_layout = QtWidgets.QVBoxLayout()
        self.gamma_value_layout = QtWidgets.QHBoxLayout()
        self.piecewise_layout = QtWidgets.QVBoxLayout()
        self.cmap_layout = QtWidgets.QVBoxLayout()
        self.bottom_layout = QtWidgets.QHBoxLayout()

        # Create widgets
        self.power_law_radio = QtWidgets.QRadioButton('Power Law')
        self.power_law_radio.setChecked(True)
        self.piecewise_radio = QtWidgets.QRadioButton('Piecewise')
        self.piecewise_reset = QtWidgets.QPushButton('Reset')
        self.piecewise_reset.setDisabled(True)
        self.norm_button_group = QtWidgets.QButtonGroup()
        self.norm_button_group.addButton(self.power_law_radio)
        self.norm_button_group.addButton(self.piecewise_radio)
        self.gamma_label = QtWidgets.QLabel('Gamma')
        self.gamma_spinbox = QtWidgets.QDoubleSpinBox()
        self.gamma_spinbox.setMinimumSize(50, 0)
        self.gamma_spinbox.setRange(10**-2, 10**2)
        self.gamma_spinbox.setValue(1)
        self.gamma_spinbox.setSingleStep(0.1)
        self.gamma_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gamma_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        gamma_min = -20
        gamma_max = 20
        gamma_step = 1
        self.gamma_slider.setMinimum(gamma_min)
        self.gamma_slider.setMaximum(gamma_max)
        self.gamma_slider.setValue(0)
        self.enable_isocurve_layout = QtWidgets.QHBoxLayout()
        self.enable_isocurve_checkbox = QtWidgets.QCheckBox()
        self.enable_isocurve_checkbox.setChecked(True)
        self.enable_isocurve = True
        self.enable_isocurve_label = QtWidgets.QLabel('Enable Isocurve?')
        self.cmap_label = QtWidgets.QLabel('Colormap')
        self.cmap_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.cmap_combobox = QtWidgets.QComboBox()
        self.cmap_combobox.setMinimumSize(150, 0)
        self.header = QtWidgets.QWidget()
        self.splitter = QtWidgets.QSplitter()
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.pg_win = PGCMapEditor(image)
        self.pg_widget = QtWidgets.QWidget()
        self.pg_widget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum))
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.pg_win)
        self.pg_widget.setLayout(layout)
        self.save_map_button = QtWidgets.QPushButton('Save Color Map')
        self.load_map_button = QtWidgets.QPushButton('Load Color Map')
        self.ok_button = QtWidgets.QPushButton('OK')
        self.cancel_button = QtWidgets.QPushButton('Cancel')

        # Populate the combo box
        self.cmap_combobox.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
        for cmap in list_cmaps():
            self.cmap_combobox.addItem(load_ct_icon(cmap), cmap)
        # for filename in os.listdir('cmaps'):
        #     if fnmatch.fnmatch(filename, '*.npy'):
        #         cmap_name = os.path.splitext(filename)[0]
        #         self.cmap_combobox.addItem(QtGui.QIcon('cmaps' + os.sep + cmap_name + '.jpg'), cmap_name)
        self.cmap_combobox.setIconSize(QtCore.QSize(64, 12))
        self.cmap_combobox.setCurrentText('viridis')
        def update_cmap(cmap_name):
            self.pg_win.load_ct(cmap_name)
            self.pg_win.update()
        self.cmap_combobox.currentTextChanged.connect(update_cmap)

        # Connect signals to slots
        self.gamma_slider.valueChanged.connect(self.gamma_spinbox_slot)
        self.gamma_spinbox.valueChanged.connect(self.gamma_slider_slot)
        self.piecewise_radio.clicked.connect(self.piecewise_clicked)
        self.power_law_radio.clicked.connect(self.power_law_clicked)
        self.enable_isocurve_checkbox.clicked.connect(self.enable_isocurve_clicked)
        self.piecewise_reset.clicked.connect(self.reset_clicked)
        self.save_map_button.clicked.connect(self.save_cmap_clicked)
        self.load_map_button.clicked.connect(self.load_cmap_clicked)

        # Initialize
        update_cmap('viridis')

        # Add widgets
        self.main_layout.addLayout(self.header_layout)
        self.header_layout.addLayout(self.cmap_norm_layout)
        self.cmap_norm_layout.addLayout(self.gamma_layout)
        self.gamma_layout.addWidget(self.power_law_radio)
        self.gamma_layout.addLayout(self.gamma_value_layout)
        self.gamma_value_layout.addWidget(self.gamma_label)
        self.gamma_value_layout.addWidget(self.gamma_spinbox)
        self.gamma_value_layout.addWidget(self.gamma_slider)
        self.enable_isocurve_layout.addWidget(self.enable_isocurve_checkbox)
        self.enable_isocurve_layout.addWidget(self.enable_isocurve_label)
        self.enable_isocurve_layout.addStretch(0)
        self.gamma_layout.addLayout(self.enable_isocurve_layout)
        self.cmap_norm_layout.addLayout(self.piecewise_layout)
        self.piecewise_layout.addWidget(self.piecewise_radio)
        self.piecewise_layout.addWidget(self.piecewise_reset)
        self.header_layout.addLayout(self.cmap_layout)
        self.cmap_layout.addWidget(self.cmap_label)
        self.cmap_layout.addWidget(self.cmap_combobox)
        self.header.setLayout(self.header_layout)
        self.splitter.addWidget(self.header)
        self.splitter.addWidget(self.pg_widget)
        self.splitter.setStretchFactor(0, 1)  # resizes the pg.GraphicsLayoutWidget against the header
        # -- makes a visible line and adds the splitter handle to a QFrame widget which draws a relief line
        splitter_handle = self.splitter.handle(1)
        layout = QtWidgets.QVBoxLayout(splitter_handle)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        line = QtWidgets.QFrame(splitter_handle)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)
        # -- end
        self.main_layout.addWidget(self.splitter)
        self.main_layout.addLayout(self.bottom_layout)
        self.bottom_layout.addWidget(self.save_map_button)
        self.bottom_layout.addWidget(self.load_map_button)
        self.bottom_layout.addStretch(0)
        self.bottom_layout.addWidget(self.ok_button)
        self.bottom_layout.addWidget(self.cancel_button)
        self.setLayout(self.main_layout)

    def save_cmap(self, filename):
        """Construct a dict with relevant data and save to filename using pickle dumps"""
        dat = {'ct': self.pg_win.ct,
               'ct_name': self.pg_win.ct_name,
               'lut': self.pg_win.lut}
        if self.pg_win.hist_graph.enabled:
            dat['cmap_stops'] = self.pg_win.hist_graph.data['pos']
        else:
            dat['gamma'] = self.pg_win.gamma
        with open(filename, 'wb') as f:
            pickle.dump(dat, f)

    def load_cmap(self, filename):
        """Load a dict with relevant data from filename"""
        with open(filename, 'rb') as f:
            dat = pickle.load(f)
        self.pg_win.ct = dat['ct']
        self.pg_win.ct_name = dat['ct_name']
        self.pg_win.lut = dat['lut']
        ret = self.cmap_combobox.findText(self.pg_win.ct_name)
        if ret < 0:
            print('This colormap does not exist in your database.')
        else:
            self.cmap_combobox.setCurrentIndex(ret)
        if 'gamma' in dat.keys():
            self.pg_win.gamma = dat['gamma']
            self.gamma_spinbox.setValue(dat['gamma'])
            self.power_law_radio.setChecked(True)
            self.power_law_clicked(False)
        elif 'cmap_stops' in dat.keys():
            self.pg_win.hist_graph.setData(pos=dat['cmap_stops'])
            # self.pg_win.hist_graph.data['pos'] = dat['cmap_stops']
            self.piecewise_radio.setChecked(True)
            self.piecewise_clicked(False)
        else:
            print('{0} is corrupted.'.format(filename))

    def enable_gamma(self):
        self.gamma_spinbox.setEnabled(True)
        self.gamma_slider.setEnabled(True)
        self.piecewise_reset.setDisabled(True)
        self.pg_win.hist_cnorm_data.setVisible(True)
        self.pg_win.hist_graph.setVisible(False)
        self.pg_win.hist_graph.enabled = False

    def enable_piecewise(self):
        self.gamma_spinbox.setDisabled(True)
        self.gamma_slider.setDisabled(True)
        self.piecewise_reset.setEnabled(True)
        self.pg_win.hist_cnorm_data.setVisible(False)
        self.pg_win.hist_graph.setVisible(True)
        self.pg_win.hist_graph.enabled = True

    def get_lut(self):
        return self.pg_win.lut

    @QtCore.pyqtSlot(bool)
    def reset_clicked(self, checked):
        self.pg_win.hist_graph.reset()
        self.pg_win.update()

    @QtCore.pyqtSlot(bool)
    def piecewise_clicked(self, checked):
        self.enable_piecewise()
        self.pg_win.update()

    @QtCore.pyqtSlot(bool)
    def power_law_clicked(self, checked):
        self.enable_gamma()
        self.pg_win.update()

    @QtCore.pyqtSlot(bool)
    def enable_isocurve_clicked(self, checked):
        self.enable_isocurve = checked
        self.pg_win.set_iso_enabled(checked)
        if checked:
            self.pg_win.iso.show()
        else:
            self.pg_win.iso.hide()

    @QtCore.pyqtSlot(int)
    def gamma_spinbox_slot(self, slider_value):
        self.gamma_spinbox.blockSignals(True)
        self.gamma_spinbox.setValue(10**(slider_value/20))
        self.gamma_spinbox.blockSignals(False)
        self.pg_win.gamma = self.gamma_spinbox.value()
        self.pg_win.update()

    @QtCore.pyqtSlot(float)
    def gamma_slider_slot(self):
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(round(20*np.log10(self.gamma_spinbox.value())))
        self.gamma_slider.blockSignals(False)
        self.pg_win.gamma = self.gamma_spinbox.value()
        self.pg_win.update()

    @QtCore.pyqtSlot(bool)
    def save_cmap_clicked(self):
        filename, ext = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Color Map', '',
                                                              'PyIT CMap (*.cmap);;All Files (*)')
        self.save_cmap(filename)

    @QtCore.pyqtSlot(bool)
    def load_cmap_clicked(self):
        filename, ext = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Color Map', '',
                                                              'PyIT CMap (*.cmap);;All Files (*)')
        self.load_cmap(filename)

class PGCMapEditor(pg.GraphicsLayoutWidget):
    def __init__(self, image, parent=None):
        super().__init__(parent)

        self.lut = np.empty((256, 3), dtype=np.uint8)
        self.ct = np.array([])
        self.ct_name = 'inferno'
        self.load_ct(self.ct_name)
        self.gamma = 1
        self.cmap_piecewise = False

        # make image view
        self.view = pg.PlotItem()
        self.imageItem = pg.ImageItem()
        self.view.addItem(self.imageItem)

        # preprocess image
        self.img_min = image.min()
        self.img_max = image.max()
        image = (image - self.img_min)/(self.img_max - self.img_min)

        # make isocurve
        self.iso = pg.IsocurveItem(pen=pg.mkPen(color='g'))
        self.iso_enabled = True

        # calculate histogram
        self.hist, self.bin_edges = np.histogram(image, 256)
        self.hist = self.hist/self.hist.sum()
        self.bin_midpoints = self.bin_edges[:-1] + np.diff(self.bin_edges)/2

        # color bar
        self.color_bar_coords = pg.PlotItem()
        self.color_bar_coords.hideAxis('left')
        height = 0.2*(self.bin_midpoints.max() - self.bin_midpoints.min())
        width = self.bin_midpoints.max() - self.bin_midpoints.min()
        x = self.bin_midpoints.min()
        y = 0
        self.color_bar = QtGui.QGraphicsRectItem(QtCore.QRectF(x - 0.5, y - 0.5, width + 1, height + 1))
        self.gradient = QtGui.QLinearGradient(QtCore.QPointF(x, 0), QtCore.QPointF(width, 0))
        self.gradient.setFinalStop(width, 0)
        self.gradient.setStops([(i/255, QtGui.QColor(*tuple(self.ct[i]))) for i in range(256)])
        self.color_bar.setBrush(QtGui.QBrush(self.gradient))

        self.color_bar_line = pg.InfiniteLine(bounds=(self.bin_edges[0], self.bin_edges[-1]))

        # histogram
        self.histogram = pg.PlotItem()
        self.hist_data = self.histogram.plot(self.bin_midpoints, self.hist)

        # histogram line and position label
        self.hist_line = pg.InfiniteLine(bounds=(self.bin_edges[0], self.bin_edges[-1]))
        self.hist_line_label = pg.TextItem(anchor=(0.5, 0.5))
        self.hist_line_label.setPos(self.bin_midpoints[128], self.hist.max())

        # add menus to the histogram line
        self.histogram.vb.menu.addSeparator()
        self.add_point_action: QtWidgets.QAction = self.histogram.vb.menu.addAction('Add point')
        self.rm_point_action: QtWidgets.QAction = self.histogram.vb.menu.addAction('Remove point')
        self.rm_point_action.setEnabled(False)
        self.add_point_action.triggered.connect(self.add_piecewise_point)

        # histogram piecewise line
        self.hist_graph = Graph(pos=np.array([[self.bin_midpoints[0], self.hist.min()], [self.bin_midpoints[-1], self.hist.max()]]), adj=np.array([[0, 1]]))
        self.hist_graph.setVisible(False)

        # histogram power law line
        self.hist_cnorm = (np.arange(len(self.hist))/(len(self.hist) - 1))**self.gamma
        self.hist_cnorm_data = self.histogram.plot(self.bin_midpoints, self.hist_cnorm*self.hist.max())

        # set data
        self.imageItem.setImage(image, lut=self.lut)
        self.iso.setData(image)

        # add items
        self.ci.addItem(self.view, row=0, col=0, rowspan=2)
        self.ci.addItem(self.color_bar_coords, row=0, col=1)
        self.ci.addItem(self.histogram, row=1, col=1)
        self.view.addItem(self.iso)
        # self.color_bar_coords.addItem(self.color_bar_element)
        self.color_bar_coords.addItem(self.color_bar)
        self.color_bar_coords.addItem(self.color_bar_line)
        self.histogram.addItem(self.hist_line)
        self.histogram.addItem(self.hist_graph)
        self.histogram.addItem(self.hist_line_label)

        # Mouse interaction
        self.mousepnt: Union[None, QtCore.QPointF] = QtCore.QPointF(0, 0)

        # Set events
        self.hist_hover_proxy = pg.SignalProxy(self.histogram.scene().sigMouseMoved, rateLimit=20,
                                               slot=self.hist_hover_handler)
        self.histogram.setXLink(self.color_bar_coords)
        self.hist_graph.color_map_changed.connect(self.update)
        self.sceneObj.sigMouseClicked.connect(self.mouseClickEvent)

        self.resize(800, 400)
        self.color_bar_coords.autoRange()
        self.update()

    def set_iso_enabled(self, enabled):
        self.iso_enabled = enabled

    def hist_hover_handler(self, evt: tuple):
        if self.histogram.sceneBoundingRect().contains(evt[0]):
            mousepnt = self.histogram.vb.mapSceneToView(evt[0])
            if self.iso_enabled:
                self.iso.setLevel(mousepnt.x())
            self.color_bar_line.setValue(mousepnt.x())
            self.hist_line.setValue(mousepnt.x())
            self.hist_line_label.setText("{0:.3g}".format(self.color_bar_line.value()*(self.img_max - self.img_min) + self.img_min))

    def update_cmap_norm(self):
        if not self.hist_graph.enabled:
            self.hist_cnorm = (np.arange(len(self.hist))/(len(self.hist) - 1))**self.gamma
            self.hist_cnorm_data.setData(self.bin_midpoints, self.hist_cnorm*self.hist.max())

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

    def update_ct(self):
        if not self.hist_graph.enabled:
            i = np.round((np.arange(len(self.ct))/(len(self.ct) - 1))**self.gamma*(len(self.ct) - 1)).astype('int')
            i[i > 255] = 255
        else:
            i = self.hist_graph.ind
        self.lut = self.ct[i]

    def update(self):
        self.update_ct()
        self.gradient.setStops([(i/255, QtGui.QColor(*tuple(self.lut[i]))) for i in range(256)])
        self.color_bar.setBrush(QtGui.QBrush(self.gradient))
        self.imageItem.setLookupTable(self.lut)
        self.update_cmap_norm()

    def add_piecewise_point(self, b: bool):
        if self.mousepnt is not None and self.hist_graph.enabled:
            pnts = [pnt for pnt in self.hist_graph.data['pos']]
            pnts.append(np.array([self.mousepnt.x(), self.mousepnt.y()]))
            pnts = np.array(pnts)
            sort = np.argsort(pnts[:, 0])
            pnts = pnts[sort, :]
            adj = np.array([[i, i + 1] for i in range(len(pnts) - 1)])
            self.hist_graph.setData(pos=pnts, adj=adj)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.histogram.sceneBoundingRect().contains(ev.scenePos()):
            self.add_point_action.setEnabled(self.hist_graph.enabled)
            self.mousepnt = self.histogram.vb.mapSceneToView(ev.scenePos())
        else:
            self.mousepnt = None

class Graph(pg.GraphItem):
    color_map_changed = QtCore.Signal()

    def __init__(self, **kwargs):
        self.dragPoint = None
        self.dragOffset = None
        self.textItems = []
        self.init_pos = kwargs['pos'].copy()
        self.init_adj = kwargs['adj'].copy()
        self.data = None
        self.ind = np.arange(256).astype('uint8')
        self.enabled = False  # False if power law, True if piecewise
        super().__init__(**kwargs)

    def reset(self):
        self.setData(pos=self.init_pos.copy(), adj=self.init_adj.copy())
        self.mapPosToIndex()

    def mapPosToIndex(self):
        x = np.empty(self.data['pos'].shape, dtype='int')
        x[:, 0] = np.round(255/(self.init_pos[1, 0] - self.init_pos[0, 0])*(self.data['pos'][:, 0] - self.init_pos[0, 0]))
        x[:, 1] = np.round(255/(self.init_pos[1, 1] - self.init_pos[0, 1])*(self.data['pos'][:, 1] - self.init_pos[0, 1]))
        sort = np.argsort(x[:, 0])
        self.ind = np.round(np.interp(np.arange(256), x[sort, 0], x[sort, 1])).astype('uint8')
        self.data['pos'] = self.data['pos'][sort, :]
        self.data['adj'] = np.array([[i, i + 1] for i in range(len(sort) - 1)])
        self.color_map_changed.emit()

    def setData(self, **kwds):
        if 'pos' in kwds:
            sort = np.argsort(kwds['pos'][:, 0])
            kwds['pos'] = kwds['pos'][sort, :]
            kwds['adj'] = np.array([[i, i + 1] for i in range(len(sort) - 1)])
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)
        self.updateGraph()

    def updateGraph(self):
        pg.GraphItem.setData(self, **self.data)
        self.mapPosToIndex()

    def mouseClickEvent(self, ev):
        ev.ignore()
        for rect in self.scatter.data['targetRect']:
            if rect is not None:
                if rect.contains(ev.scenePos()):
                    pass  # TODO: delete the point here

    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.LeftButton or not self.enabled:
            ev.ignore()
            return

        if ev.isStart():
            # We are already one step into the drag.
            # Find the point(s) at the mouse cursor when the button was first
            # pressed:
            pos = ev.buttonDownPos()
            pts = self.scatter.pointsAt(pos)
            if len(pts) == 0:
                ev.ignore()
                return
            self.dragPoint = pts[0]
            ind = pts[0].data()[0]
            self.dragOffset = self.data['pos'][ind] - pos
        elif ev.isFinish():
            self.dragPoint = None
            return
        else:
            if self.dragPoint is None:
                ev.ignore()
                return

        ind = self.dragPoint.data()[0]
        self.data['pos'][ind] = ev.pos() + self.dragOffset
        self.data['pos'][ind][0] = min(max(self.init_pos[0][0], self.data['pos'][ind][0]), self.init_pos[1][0])
        self.data['pos'][ind][1] = min(max(self.init_pos[0][1], self.data['pos'][ind][1]), self.init_pos[1][1])
        self.updateGraph()
        ev.accept()


class ColorBar(pg.GraphicsObject):
    max_colors = 256

    def __init__(self, lut=None, centers=None):
        pg.GraphicsObject.__init__(self)
        if lut is None:
            self.lut: np.array = np.empty((self.max_colors, 3), dtype=np.uint8)
        else:
            if lut.shape[0] != 256:
                raise ValueError("lut must be {0} colors".format(self.max_colors))
            self.lut = lut
        if centers is None:
            self.centers: np.array = np.arange(self.max_colors)
        else:
            if centers.size != 256:
                raise ValueError("centers must have {0} positions".format(self.max_colors))
            self.centers = centers

        self.elements: List[ColorbarElement] = []
        w = self.centers[1] - self.centers[0]
        self.w: float = w*self.max_colors
        for i in range(self.max_colors):
            pen = pg.mkPen(width=0)
            brush = pg.mkBrush(*tuple(self.lut[i]))
            cb_elem = ColorbarElement(pen=pen, brush=brush, x=self.centers[i]*2, y=0, w=w, h=1)
            self.elements.append(cb_elem)

    def set_lut(self, lut):
        if lut.shape[0] != 256:
            raise ValueError("lut must be {0} colors".format(self.max_colors))
        self.lut = lut
        for i, cb_elem in enumerate(self.elements):
            cb_elem.set_color(self.lut[i])

    def boundingRect(self):
        return QtCore.QRectF(self.centers[0] - (self.centers[1] - self.centers[0])/2, -0.5, self.w, 1)

    def paint(self, p, *args):
        for cb_elem in self.elements:
            cb_elem.paint(p, *args)


class ColorbarElement(pg.GraphicsObject):
    """
    A simple rectangle with width w, height h, and center position at x, y
    """
    def __init__(self, pen=None, brush=None, **opts):
        """
        Must implement boundingRect and paint
        """
        pg.GraphicsObject.__init__(self)
        self.setX(opts.pop('x', 0)/2)  # for some reason, there is a factor of 2 here...
        self.setY(opts.pop('y', 0))
        self.w = opts.pop('w', 1)
        self.h = opts.pop('h', 4)
        if pen is None:
            self.pen = pg.mkPen((255, 255, 255), width=0)
        else:
            self.pen = pg.mkPen(pen)

        if brush is None:
            self.brush = pg.mkBrush((255, 255, 255))
        else:
            self.brush = pg.mkBrush(brush)

        self.path = QtGui.QPainterPath()
        self.path.addRect(self.x() - self.w/2, self.y() - self.h/2, self.w, self.h)

    def set_color(self, qcolor: tuple):
        self.brush = pg.mkBrush(*qcolor)

    def boundingRect(self):
        return QtCore.QRectF(self.x() - self.w/2, self.y() - self.h/2, self.w, self.h)

    def paint(self, p, *args):
        p.setRenderHints(p.renderHints() | p.Antialiasing)
        p.setPen(self.pen)
        p.fillPath(self.path, self.brush)
        p.drawPath(self.path)


def get_cmap_dir():
    dirname = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dirname, 'cmaps')


def list_cmaps():
    cmaps = []
    for filename in os.listdir(get_cmap_dir()):
        if fnmatch.fnmatch(filename, '*.npy'):
            cmaps.append(os.path.splitext(filename)[0])
    return cmaps


def load_ct(cmap_name: str = 'viridis'):
    path = get_cmap_dir() + os.sep + cmap_name + '.npy'
    if os.path.isfile(path):
        ct = np.load(path)
        if ct.shape[0] != 256:
            ct = PGCMapEditor.interp_cmap_256(ct)
        return ct
    else:
        print(get_cmap_dir(), path)
        print('Color map [{}] not found!'.format(cmap_name))
        return None


def load_ct_icon(cmap_name: str = 'viridis'):
    path = get_cmap_dir() + os.sep + cmap_name + '.jpg'
    if os.path.isfile(path):
        icon = QtGui.QIcon(path)
        return icon
    else:
        print(get_cmap_dir(), path)
        print('Color map icon [{}] not found!'.format(cmap_name))
        return None


def interp_cmap_256(ct: np.array):
    """
    Given an array of size (M, 3), where M is not equal to 256, this will linearly interpolate each channel to create
    an array of size (256, 3)
    """
    r = np.interp(np.arange(256), np.arange(ct.shape[0]) / (ct.shape[0] - 1) * 255, ct[:, 0])
    g = np.interp(np.arange(256), np.arange(ct.shape[0]) / (ct.shape[0] - 1) * 255, ct[:, 1])
    b = np.interp(np.arange(256), np.arange(ct.shape[0]) / (ct.shape[0] - 1) * 255, ct[:, 2])
    return np.array([r, g, b]).T

# Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication([])

    # generate data
    import numpy as np
    x = np.linspace(-3, 3, 101)
    y = np.linspace(-5, 5, 101)
    X, Y = np.meshgrid(x, y, indexing='ij')
    gamma1 = 2
    gamma2 = 0.9
    gamma3 = 0.8
    img = gamma1**2/((Y - X**2)**2 + gamma1**2) + gamma2**2/((Y + (1 + X**2))**2 + gamma2**2) + gamma3**2/((Y - np.cos(X))**2 + gamma3**2)
    img += np.random.rand(*img.shape)*(img.max()/20)

    # import matplotlib.pyplot as plt
    # plt.imshow(img.T, cmap='inferno', origin='lower')
    # plt.colorbar()
    # plt.show()

    cmap_editor = CMapEditor(img)

    cmap_editor.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
