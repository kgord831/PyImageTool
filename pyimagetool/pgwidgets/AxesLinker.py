class AxesLinker:
    def __init__(self):
        self.axes = []

    def link(self, axis):
        if axis in self.axes:
            return
        self.axes.append(axis)

    def unlink(self, axis):
        if axis in self.axes:
            self.axes.remove(axis)

    def update(self, axis, newval):
        for ax in self.axes:
            if ax != axis:
                ax.set_value(newval)
