import warnings
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
import numpy as np

from pyimagetool.cmaps import CMap
from pyimagetool.DataMatrix import RegularDataArray


class ImageBase(pg.PlotItem):

    def __init__(self, dat: RegularDataArray = None, **kwargs):
        """2D image view with extra features.

        :param lut: Name of colormap to initialize with
        :type lut: str
        """
        super().__init__(**kwargs)

        self.baselut = CMap().load_ct(kwargs.pop('lut', 'blue_orange'))
        self.lut = np.copy(self.baselut)

        self.img = pg.ImageItem(parent=self, lut=self.lut)
        self.addItem(self.img)

        # Create the menu
        self.menu = QtWidgets.QMenu('Image')
        # Aspect ratio
        self.aspect_menu = QtWidgets.QMenu('Aspect Ratio')
        self.aspect_ui = AspectRatioForm()
        self.build_aspect_form()

        self.ctrl_down = False

        self.data = dat
        if dat is not None:
            self.set_data(dat)

    def set_data(self, dat: RegularDataArray, calc_tr=True, **kwargs):
        self.data = dat
        self.img.setImage(dat.values, **kwargs)
        if calc_tr:
            tr = QtGui.QTransform()
            tr.scale(dat.delta[0], dat.delta[1])
            tr.translate(dat.coord_min[0] / dat.delta[0] - 0.5,
                         dat.coord_min[1] / dat.delta[1] - 0.5)
            self.img.resetTransform()
            self.img.setTransform(tr, True)

    def set_image(self, img: np.array, **kwargs):
        """Replace the current image data with new data of the same shape. If the shape changes, the axes are no
        longer guaranteed."""
        if img.shape != self.img.image.shape:
            warnings.warn('New image size is not the same shape as current data. Use ImageSlice.set_data instead. '
                          + 'ignoring set_image request...')
        else:
            self.img.setImage(img, **kwargs)

    def set_lut(self, lut: np.array):
        self.lut = lut
        self.baselut = lut
        self.img.setLookupTable(lut)
        # self.img.setImage(self.img.image, lut=lut)

    def build_aspect_form(self):
        w = QtWidgets.QWidget()
        self.aspect_ui.setupUi(w)
        self.aspect_ui.aspectRatio.setValidator(QtGui.QDoubleValidator(0, float("inf"), 20))
        action = QtWidgets.QWidgetAction(self.menu)
        action.setDefaultWidget(w)
        self.aspect_menu.addAction(action)
        self.menu.addMenu(self.aspect_menu)
        self.aspect_ui.lockAspect.stateChanged.connect(self.aspect_lock_toggle)
        self.aspect_ui.aspectRatio.editingFinished.connect(self.aspect_lock_edit)

    def aspect_lock_toggle(self, b):
        if b == QtCore.Qt.Checked:
            a = float(self.aspect_ui.aspectRatio.text())
            if a > 0:
                self.setAspectLocked(True, a)
        else:
            range_now = self.vb.viewRange()
            self.setAspectLocked(False)
            self.vb.setRange(xRange=range_now[0], yRange=range_now[1])

    def aspect_lock_edit(self):
        if self.aspect_ui.lockAspect.isChecked():
            a = float(self.aspect_ui.aspectRatio.text())
            if a > 0:
                self.setAspectLocked(True, a)

    def zoom_fit(self):
        self.vb.autoRange()

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.menuEnabled():
            ev.accept()
            self.raiseContextMenu(ev)

    def raiseContextMenu(self, ev):
        menu = self.getMenu(ev)
        menu.addSeparator()
        for act in self.vb.menu.actions():
            menu.addAction(act)
        menu.addSeparator()
        self.scene().addParentContextMenus(self, menu, ev)
        menu.popup(ev.screenPos().toPoint())

    def getMenu(self, ev):
        return self.menu

    def keyPressEvent(self, ev: QtGui.QKeyEvent):
        if ev.key() == QtCore.Qt.Key_Control:
            self.ctrl_down = True
        elif ev.key() == QtCore.Qt.Key_A and self.ctrl_down:
            self.zoom_fit()
            ev.accept()
        else:
            ev.ignore()

    def keyReleaseEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Control and self.ctrl_down:
            self.ctrl_down = False
        else:
            ev.ignore()


class AspectRatioForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(150, 24)
        Form.setMaximumSize(QtCore.QSize(150, 16777215))
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.aspectRatio = QtWidgets.QLineEdit(Form)
        self.aspectRatio.setObjectName("aspectRatio")
        self.gridLayout.addWidget(self.aspectRatio, 0, 1, 1, 1)
        self.lockAspect = QtWidgets.QCheckBox(Form)
        self.lockAspect.setObjectName("lockAspect")
        self.gridLayout.addWidget(self.lockAspect, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.aspectRatio.setText(_translate("Form", "1"))
        self.lockAspect.setText(_translate("Form", "Lock Aspect"))
