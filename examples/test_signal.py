from PyQt5 import QtCore
from typing import overload


class Foo(QtCore.QObject):
    model_changed = QtCore.pyqtSignal(float)

    def __init__(self, name=''):
        super().__init__()
        self._name = name
        self._model: float = 1.0

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, newval):
        self._model = newval
        self.model_changed.emit(newval)

    @QtCore.pyqtSlot(float)
    def on_model_changed(self, val):
        self._model = val
        print('[{0}] New model value is {1}'.format(self._name, val))


class CursorPosition(QtCore.QObject):
    """A cursor position is a simple index that """
    value_changed = QtCore.pyqtSignal([int], [float])

    @overload
    def __init__(self, val: int = 0):
        pass

    @overload
    def __init__(self, val: float = 0):
        pass

    def __init__(self, val=0):
        super().__init__()
        self._val = val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, newval):
        if type(self._val) is float:
            self._val = float(newval)
        elif type(self._val) is int:
            self._val = int(newval)
        self.value_changed[type(self._val)].emit(self._val)

    @QtCore.pyqtSlot(float)
    def on_value_changed(self, newval):
        self.val = newval


foo = Foo('1')
foo2 = Foo('2')
model = CursorPosition(2)
model.value_changed[float].connect(foo2.on_model_changed)
model.value_changed[float].connect(foo.on_model_changed)
foo2.model_changed.connect(model.on_value_changed)
foo.model_changed.connect(model.on_value_changed)
foo.model = 1
