import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
from .DataMatrix import RegularDataArray
from .widgets import AspectRatioForm
from typing import Union
from .CMapEditor import CMapDialog
import warnings
import numpy as np


class ImageSlice(pg.PlotItem):

    def __init__(self, dat: Union[RegularDataArray, None] = None, parent=None, name=None, labels=None, title=None, viewBox=None, axisItems=None, enableMenu=True, **kwargs):
        super().__init__(parent, name, labels, title, viewBox, axisItems, enableMenu, **kwargs)
        self.img = pg.ImageItem(parent=self)
        self.addItem(self.img)
        if dat is not None:
            if dat.ndim != 2:
                warnings.warn('Data should have exactly 2 dimensions.')
                if dat.ndim < 2:
                    raise NotImplementedError('This tool cannot yet insert one dimension.')
                else:
                    raise NotImplementedError('This tool cannot yet sample exactly two dimensions.')
            else:
                self.set_data(dat)

        # Create the menu
        self.menu = QtWidgets.QMenu('Image')
        self.aspect_menu = QtWidgets.QMenu('Aspect Ratio')
        self.aspect_ui = AspectRatioForm()
        self.build_aspect_form()
        self.edit_cmap_action = QtWidgets.QAction('Edit Color Map')
        self.edit_cmap_action.triggered.connect(self.edit_cmap)
        self.cmap_editor = QtWidgets.QWidget()
        self.menu.addAction(self.edit_cmap_action)
        self.ctrl_down = False

    def set_data(self, dat: RegularDataArray, **kwargs):
        self.img.setImage(dat.values, **kwargs)
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
            warnings.warn('New image size is not the same shape as current data. Use ImageSlice.set_data instead.')
        else:
            self.img.setImage(img, **kwargs)

    def set_lut(self, lut: np.array):
        self.img.setImage(self.img.image, lut=lut)

    def edit_cmap(self):
        dialog = CMapDialog(self.img.image)
        r = dialog.exec()
        if r == 1:
            lut = dialog.widget.get_lut()
            self.img.setLookupTable(lut)

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

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    from test_imagetool import from_file
    app = QtGui.QApplication([])

    my_data = from_file()
    my_data = RegularDataArray(my_data.data[:, :, 885], delta=my_data.delta[0:2], coord_min=my_data.coord_min[0:2])

    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()
    window.setLayout(layout)
    pg_view = pg.GraphicsLayoutWidget(window)
    image_slice = ImageSlice(my_data)
    pg_view.addItem(image_slice)

    layout.addWidget(pg_view)

    window.resize(400, 400)
    window.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()