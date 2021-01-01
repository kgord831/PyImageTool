from pyqtgraph.Qt import QtCore
import math


class SingleValueModel(QtCore.QObject):
    """A cursor position is either a float or int (determined at instantiation) and preserves the type in assignment.
    Furthermore, the object emits either an int or float pyqtSignal when the value is changed through the setter."""
    value_set = QtCore.Signal(object)

    def __init__(self, val: object):
        super().__init__()
        self._value = val

    def __repr__(self):
        return f"Model[{self._value}]"

    def __str__(self):
        return self.__repr__()

    def set_value(self, newval, block=False):
        self._value = newval
        if not block:
            self.value_set.emit(self._value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self.set_value(newval, block=False)


class ValueLimitedModel(SingleValueModel):
    def __init__(self, val, lower=None, upper=None):
        super().__init__(val)
        self._lower_lim = lower
        self._upper_lim = upper

    def __repr__(self):
        return f"Model[{self._value}, {(self._lower_lim, self._upper_lim)}]"

    def __str__(self):
        return self.__repr__()

    @property
    def lower_lim(self):
        return self._lower_lim

    @lower_lim.setter
    def lower_lim(self, newval):
        self._lower_lim = newval
        self.value = self._value

    @property
    def upper_lim(self):
        return self._upper_lim

    @upper_lim.setter
    def upper_lim(self, newval):
        self._upper_lim = newval
        self.value = self._value

    def set_value(self, newval, block=False):
        if self._lower_lim is not None and newval < self._lower_lim:
            newval = self._lower_lim
        if self._upper_lim is not None and newval > self._upper_lim:
            newval = self._upper_lim
        self._value = newval
        if not block:
            self.value_set.emit(self._value)
        return self._value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self.set_value(newval, block=False)
