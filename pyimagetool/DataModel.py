from pyqtgraph import QtCore


class IntModel(QtCore.QObject):
    """A cursor position is either a float or int (determined at instantiation) and preserves the type in assignment.
    Furthermore, the object emits either an int or float pyqtSignal when the value is changed through the setter."""
    value_changed = QtCore.Signal(int)

    def __init__(self, val: int):
        super().__init__()
        self._val = val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, newval):
        if isinstance(newval, int):
            self._val = newval
        else:
            try:
                self._val = int(newval)
            except TypeError as e:
                raise e
        self.value_changed.emit(self._val)

    @QtCore.pyqtSlot(int)
    def on_value_changed(self, newval):
        self.val = newval


class FloatModel(QtCore.QObject):
    """A cursor position is either a float or int (determined at instantiation) and preserves the type in assignment.
    Furthermore, the object emits either an int or float pyqtSignal when the value is changed through the setter."""
    value_changed = QtCore.Signal(float)

    def __init__(self, val: float):
        super().__init__()
        self._val = val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, newval):
        if isinstance(newval, float):
            self._val = newval
        else:
            try:
                self._val = float(newval)
            except TypeError as e:
                raise e
        self.value_changed.emit(self._val)

    @QtCore.pyqtSlot(float)
    def on_value_changed(self, newval):
        self.val = newval


class DataModel:
    """A cursor position is either a float or int (determined at instantiation) and preserves the type in assignment.
    Furthermore, the object emits either an int or float pyqtSignal when the value is changed through the setter."""
    value_changed = QtCore.Signal(object)

    def __init__(self, ndim: int):
        self.ndim = ndim
        self.pos = [FloatModel(0)]*ndim
        self.index = [IntModel(0)]*ndim
        self.bincoordwidth = [0]*ndim
        self.binindexwidth = [1]*ndim
