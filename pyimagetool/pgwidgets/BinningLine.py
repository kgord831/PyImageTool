import pyqtgraph as pg
from pyqtgraph.Qt import QtCore


class BinningLine(pg.GraphicsObject):
    sigPositionChanged = QtCore.Signal(object)
    _orientation_axis = {
        'v': 0,
        'h': 1
    }

    def __init__(self, **kwargs):
        pg.GraphicsObject.__init__(self)

        kwargs = kwargs.copy()
        self._min_binwidth = kwargs.pop('binwidth', 0)
        self._binwidth = self._min_binwidth
        bin_pen = kwargs.pop('bin_pen', None)
        if 'movable' not in kwargs:
            kwargs['movable'] = True
        self.line = pg.InfiniteLine(**kwargs)

        if bin_pen is not None:
            kwargs['pen'] = bin_pen
        else:
            kwargs['pen'] = pg.mkPen(style=pg.Qt.QtCore.Qt.DashLine)
        kwargs['movable'] = False
        self.bin1 = pg.InfiniteLine(**kwargs)
        self.bin2 = pg.InfiniteLine(**kwargs)

        angle = kwargs.pop('angle', 90)
        if angle == 90:
            self.orientation = 'v'
        else:
            self.orientation = 'h'

        self.bounds = QtCore.QRectF()
        self._bounds = None

        self.line.setParentItem(self)
        self.line.sigPositionChanged.connect(self.line_moved)
        self.bin1.setParentItem(self)
        self.bin2.setParentItem(self)
        self.bin1.setVisible(False)
        self.bin2.setVisible(False)

    def boundingRect(self):
        br = self.viewRect()

        if self.orientation == 'v':
            br.setLeft(self.bin1.value())
            br.setRight(self.bin2.value())
            length = br.height()
            br.setBottom(br.top() + length)
            br.setTop(br.top())
        else:
            br.setTop(self.bin1.value())
            br.setBottom(self.bin2.value())
            length = br.width()
            br.setRight(br.left() + length)
            br.setLeft(br.left())

        br = br.normalized()

        if self._bounds != br:
            self._bounds = br
            self.prepareGeometryChange()

        return br

    def paint(self, p, *args):
        pass
        # p.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 255, 50)))
        # p.setPen(pg.mkPen(None))
        # p.drawRect(self.boundingRect())

    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        if axis == self._orientation_axis[self.orientation]:
            return self.bin1.value(), self.bin2.value()
        else:
            return None

    def set_binwidth(self, newval):
        """This is a view function, no events fired"""
        self._binwidth = max(0, newval)
        if self._binwidth > self._min_binwidth:
            self.set_bin_visibility(True)
        else:
            self.set_bin_visibility(False)
        self.bin1.setValue(self.line.value() - self._binwidth/2)
        self.bin2.setValue(self.line.value() + self._binwidth/2)
        self.prepareGeometryChange()

    def set_min_binwidth(self, newval):
        self._min_binwidth = max(0, newval)
        self.set_binwidth(self._binwidth)

    def set_bin_visibility(self, newval):
        self.bin1.setVisible(newval)
        self.bin2.setVisible(newval)

    def update_pos(self, newval):
        """This is a view function, it does not fire events"""
        self.line.blockSignals(True)
        self.line.setValue(newval)
        self.line.blockSignals(False)
        self.bin1.setValue(self.line.value() - self._binwidth/2)
        self.bin2.setValue(self.line.value() + self._binwidth/2)
        self.prepareGeometryChange()

    def set_pos(self, newval):
        """This is programmatic control"""
        self.line.setValue(newval)  # fires line_moved event handler

    def line_moved(self):
        """This handler executes under user control"""
        self.bin1.setValue(self.line.value() - self._binwidth/2)
        self.bin2.setValue(self.line.value() + self._binwidth/2)
        self.prepareGeometryChange()
        self.sigPositionChanged.emit(self.line.value())

    def update_bounds(self, newbounds):
        self.line.setBounds(newbounds)
        self.bin1.setBounds(newbounds)
        self.bin2.setBounds(newbounds)

if __name__ == '__main__':
    import pyqtgraph as pg
    import numpy as np
    from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
    import sys

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtGui.QApplication([])

    win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
    p1 = win.addPlot(title="Basic array plotting", y=np.random.normal(size=100))

    x = BinningLine(binwidth=3, angle=0, bounds=(0, 99))
    x.set_bin_visibility(True)
    x.sigPositionChanged.connect(lambda t: print(t))
    x.set_pos(80)

    p1.addItem(x)

    win.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
