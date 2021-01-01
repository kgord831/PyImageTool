import numpy as np
from collections.abc import Iterable
from scipy.interpolate import RegularGridInterpolator

try:
    import xarray as xr
except ImportError:
    xr = None

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


class RegularDataArray(object):
    """
    An object that holds and exposes an underlying xarray DataArray which assumes regularly gridded coordinates and
    defines properties relevant to the regular grid
    """

    def __init__(self, dat, delta=None, coord_min=None, dims=None, name='Unnamed'):
        """Create an instance of a RegularDataArray from an existing array.

        ``delta``, ``coord_min``, and ``dims`` are ordered according to row-major order. For example, given 2D matrix
        ``img`` with ``dims = ['x', 'y']``, then dat[:, 0] would be all the ``x`` values at a fixed ``y``.

        :param dat: Input data. If class:`RegularDataArray`, then perform a deep copy. Input class:`np.ndarray` is
        ordinary usage. If class:`xr.DataArray`, then assume it's already regularly gridded.
        :type dat: class:`RegularDataArray`, class:`np.ndarray`, or class`xr.DataArray`
        :param delta: Iterable representing the delta for each axis
        :type delta: Iterable[class:`np.ndarray`]
        :param coord_min: The first coordinate value for each axis
        :type coord_min: Iterable[class:`np.ndarray`]
        :param dims: Labels of each dimension
        :type dims: Iterable[class:`str`]
        """
        # Deep copy RegularDataArray
        if isinstance(dat, RegularDataArray):
            self._data = dat._data.copy()
            def deepcopy(listin):
                return [x.copy() for x in listin]
            self.delta = np.array(deepcopy(dat.delta))
            self.coord_min = np.array(deepcopy(dat.coord_min))
            self.dims = dat.dims
            self.axes = deepcopy(dat.axes)
            self.coord_max = np.array(deepcopy(dat.coord_max))
            self.name = dat.name
            return
        # read in numpy array
        elif isinstance(dat, np.ndarray):
            self._data = dat.copy()
            if coord_min is None:
                self.coord_min = np.array([0 for _ in range(dat.ndim)])
            else:
                if not isinstance(coord_min, Iterable):
                    coord_min = (coord_min,)
                if len(coord_min) != dat.ndim:
                    raise ValueError(f"Shape mismatch between data {dat.shape} and delta {coord_min}")
                self.coord_min = np.array(coord_min)
            if delta is None:
                self.delta = np.array([1 for _ in range(dat.ndim)])
            else:
                if not isinstance(delta, Iterable):
                    delta = (delta,)
                if len(delta) != dat.ndim:
                    raise ValueError(f"Shape mismatch between data {dat.shape} and delta {delta}")
                self.delta = np.array(delta)
        # read in xarray
        elif xr and isinstance(dat, xr.DataArray):
            self._data = dat.values.copy()
            if coord_min is None:
                self.coord_min = np.array([dat.coords[x][0] for x in dat.dims])
            else:
                self.coord_min = np.array(list(coord_min))
            if delta is None:
                delta = [(dat.coords[x][-1] - dat.coords[x][0])/(dat.coords[x].size - 1) for x in dat.dims]
                self.delta = np.array(delta)
            else:
                self.delta = np.array(list(delta))
        else:
            raise ValueError("Input data is not recognized by RegularDataArray")
        # if any delta is negative, make it positive and update data
        idx = self.delta < 0
        if np.any(idx):
            self.coord_min[idx] += (np.array(self._data.shape)[idx] - 1) * self.delta[idx]
            self.delta[idx] *= -1
            newview = tuple(slice(None, None, -1 if x else None) for x in idx)
            self._data = self._data[newview].copy()

        # create axes and coord_max properties
        self.axes = [cmin + d*np.arange(n) for cmin, d, n in zip(self.coord_min, self.delta, self._data.shape)]
        self.coord_max = np.array([ax[-1] for ax in self.axes])

        # create dims property
        if dims is None:
            label = ['x', 'y', 'z', 't']
            self.dims = [lbl for lbl, _ in zip(label, range(self._data.ndim))]
            if dat.ndim > len(label):
                for i in range(len(label), self._data.ndim):
                    self.dims.append('dim' + str(i))
        else:
            self.dims = [lbl for lbl, _ in zip(dims, range(self._data.ndim))]
            if self._data.ndim > len(dims):
                for i in range(len(dims), self._data.ndim):
                    self.dims.append('dim' + str(i))
        self.dims = tuple(self.dims)

        # Set the name
        self.name = str(name)

        # Set up interpolator
        self.interpolator = None

    def __str__(self):
        out = f"{self.name} Array\n"
        out += f"\tshape={self.shape}\n"
        out += f"\tdims={self.dims}\n"
        out += f"\tcoord_min={list(self.coord_min)}\n"
        out += f"\tcoord_max={list(self.coord_max)}\n"
        out += f"\tdelta={list(self.delta)}\n"
        out += "Values:\n"
        out += f"{str(self.data)}"
        return out

    def __array__(self):
        return self._data

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return self.isel(*item)
        else:
            return self.isel(item)

    def isel(self, *args):
        """Returns a new RegularDataArray cropped by index.

        :param args: Tuple of integers or slice objects. Length of tuple must match ndim
        :type args: Tuple[Union[int, slice]]
        """
        if len(args) != self.ndim:
            raise ValueError(f"Input slice dimensions {len(args)} does not match data dimensions {self.ndim}.")
        selection = []
        for i, arg in enumerate(args):
            if arg is None:
                selection.append(slice(0, self.shape[i], 1))
            elif isinstance(arg, slice):
                start = arg.start
                if start is None:
                    start = 0
                elif start < 0:
                    start += self.shape[i]
                stop = arg.stop
                if stop is None:
                    stop = self.shape[i]
                elif stop < 0:
                    stop += self.shape[i]
                selection.append(slice(start, stop, arg.step))
            else:
                j = (arg if arg >= 0 else self.shape[i] + arg)
                selection.append(slice(j, j + 1))

        coord_min = self.coord_min.copy()
        delta = self.delta.copy()
        for i, slc in enumerate(selection):
            start = 0 if slc.start is None else round(slc.start)
            stop = self.data.shape[i] if slc.stop is None else round(slc.stop)
            step = 1 if slc.step is None else round(slc.step)
            if start == stop:
                if start == 0:
                    stop += 1
                elif start == self._data.shape[i] - 1:
                    start -= 1
                else:
                    stop = start + 1
            coord_min[i] = self.axes[i][start]
            delta[i] *= step
            selection[i] = slice(start, stop, step)
        try:
            data = self._data[tuple(selection)]
        except IndexError:
            raise IndexError("Slice data")
        return RegularDataArray(data, delta=delta, coord_min=coord_min, dims=self.dims)

    def sel(self, *args):
        if len(args) != self.ndim:
            raise ValueError(f"Input slice dimensions {len(args)} does not match data dimensions {self.ndim}.")
        selection = []
        for i, arg in enumerate(args):
            if arg is None:
                selection.append(slice(self.coord_min[i], self.coord_max[i]))
            elif isinstance(arg, slice):
                selection.append(arg)
            else:
                selection.append(slice(arg, arg + 1))

        coord_min = self.coord_min.copy()
        delta = self.delta.copy()
        for i, slc in enumerate(selection):
            start = 0 if slc.start is None else round(self.scale_to_index(i, slc.start))
            stop = self.data.shape[i] - 1 if slc.stop is None else round(self.scale_to_index(i, slc.stop)) + 1
            step = 1 if slc.step is None else round(slc.step/self.delta[i])
            start = min(self._data.shape[i] - 1, max(0, start))
            stop = min(self._data.shape[i], max(1, stop))
            if start == stop:
                if start == 0:
                    stop += 1
                elif start == self._data.shape[i] - 1:
                    start -= 1
                else:
                    stop = start + 1
            coord_min[i] = self.axes[i][start]
            delta[i] *= step
            selection[i] = slice(start, stop, step)
        try:
            data = self._data[tuple(selection)]
        except IndexError:
            raise IndexError("Slice data")
        return RegularDataArray(data, delta=delta, coord_min=coord_min, dims=self.dims)

    def squeeze(self):
        """Remove any one dimensional axis."""
        rm_dim = [x == 1 for x in self.shape]
        mat = self.data.squeeze()
        coord_min = []
        delta = []
        for i, rm in enumerate(rm_dim):
            if not rm:
                coord_min.append(self.coord_min[i])
                delta.append(self.delta[i])
        return RegularDataArray(mat, coord_min=coord_min, delta=delta)

    def transpose(self, tr):
        """Transpose the RegularSpacedData

        :param tr: A list containing a permutation of [1, 2, ..., N-1] where N = self.data.ndim
        :type tr: List[int]
        """
        coord_min = [self.coord_min[i] for i in tr]
        delta = [self.delta[i] for i in tr]
        dims = tuple(self.dims[i] for i in tr)
        return RegularDataArray(np.transpose(self.data, tr),
                                coord_min=coord_min, delta=delta, dims=dims, name=self.name)

    def index_to_scale(self, axis, i):
        """Retrieve the coordinate corresponding to index i
        :return: float representing the coordinate value of index i
        """
        return float(self.coord_min[axis] + self.delta[axis]*i)

    def scale_to_index(self, axis, coord_val):
        """Retrieve the index (may not be an integer) representing coord_val on axis
        :return: float representing index of coordinate
        """
        return float((coord_val - self.coord_min[axis])/self.delta[axis])

    def interp(self, pts, method='linear'):
        """Interpolate the regularly gridded data at arbitrary points.

        :param pts: (Npts, ndim) array of points to interpolate onto
        :type pts: Union[Iterable[float], np.ndarray]
        :param method: should be ``linear`` or ``nearest``
        :type method: class:`str`
        """
        if self.interpolator is None or method != self.interpolator[0]:
            fcn = RegularGridInterpolator(tuple(self.axes), self._data, method, bounds_error=False)
            self.interpolator = (method, fcn)
            return fcn(pts)
        else:
            return self.interpolator[1](pts)

    def plot(self, ax=None, **kwargs):
        if plt:
            if ax is None:
                _, ax = plt.subplots(1)
            if self.ndim == 1:
                if 'marker' not in kwargs:
                    kwargs['marker'] = 'o'
                if 'markeredgecolor' not in kwargs:
                    kwargs['markeredgecolor'] = 'k'
                if 'markerfacecolor' not in kwargs:
                    kwargs['markerfacecolor'] = 'r'
                ax.plot(self.axes[0], self.values, **kwargs)
                ax.set_xlabel(self.dims[0])
                ax.set_ylabel(self.name)
            elif self.ndim == 2:
                if 'extent' not in kwargs:
                    kwargs['extent'] = [self.coord_min[0] - self.delta[0]/2, self.coord_max[0] + self.delta[0]/2,
                                        self.coord_min[1] - self.delta[1]/2, self.coord_max[1] + self.delta[1]/2]
                if 'origin' not in kwargs:
                    kwargs['origin'] = 'lower'
                ax.imshow(self.values.T, **kwargs)
                ax.set_xlabel(self.dims[0])
                ax.set_ylabel(self.dims[1])
            else:
                raise ValueError("Using matplotlib, I cannot plot 3D or higher dimensional data.")
            plt.show()
        else:
            raise ModuleNotFoundError("matplotlib not found!")

    def mean(self, axes):
        newdims = list(self.shape)
        if not isinstance(axes, Iterable):
            axes = (axes,)
        for ax in axes:
            newdims[ax] = 1
        coord_min = [self.coord_min[ax] if ax not in axes else (self.coord_max[ax] + self.coord_min[ax])/2
                     for ax in range(self.ndim)]
        delta = self.delta.copy()
        mat = np.mean(self.data, axis=axes).reshape(newdims)
        return RegularDataArray(mat, coord_min=coord_min, delta=delta, dims=self.dims, name=self.name)

    @property
    def T(self):
        return self.transpose([1, 0])

    @property
    def data(self) -> np.ndarray:
        """Returns DataArray"""
        return self._data

    @property
    def values(self) -> np.ndarray:
        """Returns np.array represented by DataArray"""
        return self._data

    @property
    def ndim(self) -> int:
        return self._data.ndim

    @property
    def shape(self):
        return self._data.shape

    @property
    def offset(self):
        return self.coord_min


def from_numpy_array(dat: np.array, delta=None, coord_min=None, dims=None):
    """
    Build data using a numpy array. Must provide one of the following:
    - An iterable of axes, where each axis is a numpy array
    - An interable of delta and coord_min
    Guarantees regularly gridded coordinates and sorts data so that coordinates are ascending
    """
    return RegularDataArray(dat, delta=delta, coord_min=coord_min, dims=dims)


if xr:
    def from_xarray(dat: xr.DataArray):
        if xr:
            coord_min = np.array([dat[dim].values[0] for dim in dat.dims])
            delta = np.array([dat[dim].values[1] - dat[dim].values[0] for dim in dat.dims])
            return RegularDataArray(dat.values, delta=delta, coord_min=coord_min, dims=dat.dims)
        else:
            raise ModuleNotFoundError("xarray not available!")

    def from_xarray_irregular(dat: xr.DataArray):
        if xr:
            coord_min = np.array([dat[dim].values[0] for dim in dat.dims])
            delta = np.array([np.mean(np.diff(dat[dim].values)) for dim in dat.dims])
            return RegularDataArray(dat.values, delta=delta, coord_min=coord_min, dims=dat.dims)
        else:
            raise ModuleNotFoundError("xarray not available!")
else:
    def from_xarray(dat):
        raise ModuleNotFoundError("xarray not available!")

    def from_xarray_irregular(dat):
        raise ModuleNotFoundError("xarray not available!")
