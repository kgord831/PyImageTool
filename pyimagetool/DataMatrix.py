import numpy as np
import xarray as xr
from typing import Union
import warnings


class RegularDataArray(object):
    """
    An object that holds and exposes an underlying xarray DataArray which assumes regularly gridded coordinates and
    defines properties relevant to the regular grid
    """

    def __init__(self, dat=None, axes=None, delta=None, coord_min=None, dims=None):
        """Create an instance of a RegularDataArray
        :param dat: RegularDataArray, xarray.DataArray, or numpy.array
        :param axes: Iterable of numpy arrays representing coordinates
        :param delta: Iterable representing the delta for each axis
        :param coord_min: Iterable representing the offset/coord_min for each axis
        :param dims: Iterable representing names of each dimension
        """
        if dat is None:
            return
        if isinstance(dat, RegularDataArray):
            self._data = dat._data.copy()
            self.axes = dat.axes
            self.delta = dat.delta
            self.coord_min = dat.coord_min
            self.coord_max = dat.coord_max
            return
        if isinstance(dat, xr.DataArray):
            if axes is None:
                axes = [dat[dimlabel].values for dimlabel in dat.dims]
            dat = dat.values
        self.delta = np.ones(dat.ndim)
        self.coord_min = np.zeros(dat.ndim)
        if axes is not None:
            if any([len(ax) != shape for ax, shape in zip(axes, dat.shape)]):
                raise ValueError('Axis shape {0} does not match data shape {1}'.format([ax.shape for ax in axes], dat.shape))
            for i in range(len(axes)):
                self.delta[i] = np.mean(np.diff(axes[i]))
                self.coord_min[i] = axes[i][0]
            # TODO: do not assume the axes are sorted
        else:
            order = [slice(None) for i in range(dat.ndim)]
            if delta is not None:
                for i in range(len(delta)):
                    if delta[i] < 0:
                        self.delta[i] = -1 * delta[i]
                        order[i] = slice(None, None, -1)
                        if coord_min is not None:
                            self.coord_min[i] = coord_min[i] + (dat.shape[i] - 1)*delta[i]
                    else:
                        self.delta[i] = delta[i]
                        if coord_min is not None:
                            self.coord_min[i] = coord_min[i]
            elif coord_min is not None:
                for i in range(len(coord_min)):
                    self.coord_min[i] = coord_min[i]
            dat = np.copy(dat[tuple(order)])

        self.axes = [self.coord_min[i] + self.delta[i]*np.arange(dat.shape[i]) for i in range(dat.ndim)]
        self.coord_max = np.array([ax[-1] for ax in self.axes])
        coords = {}
        if dims is None:
            label = ['x', 'y', 'z', 't']
            for la, i in zip(label, range(dat.ndim)):
                coords[la] = self.axes[i]
            if dat.ndim > len(label):
                for i in range(len(label), dat.ndim):
                    coords['dim_' + str(i)] = self.axes[i]
            dims = coords.keys()
        else:
            if len(dims) != len(self.axes):
                raise ValueError('Not all dimensions are labelled')
            for i, dim in enumerate(dims):
                coords[dim] = self.axes[i]
        self._data: xr.DataArray = xr.DataArray(dat, dims=dims, coords=coords)

    def data_updated(self, regular=True):
        if regular:
            self.coord_min = np.array([self._data[dim].values[0] for dim in self._data.dims])
            self.coord_max = np.array([self._data[dim].values[-1] for dim in self._data.dims])
            self.delta = np.array([self._data[dim].values[1] - self._data[dim].values[0] for dim in self._data.dims])
            self.axes = [self.delta[i]*np.arange(self._data.shape[i]) + self.coord_min[i] for i in range(self.ndim)]
        else:
            raise NotImplementedError("Irregular coordinate update not yet implemented.")

    def get_labels(self, *index):
        return tuple([self.data.dims[i] for i in index])

    def isel(self, *args, **kwargs):
        return self.from_xarray(self.data.isel(*args, **kwargs))

    def sel(self, *args, **kwargs):
        return self.from_xarray(self.data.sel(*args, **kwargs))

    def transpose(self, tr):
        """
        tr is a dictionary mapping current axis (i) to axis (j).
        Example:
            tr = {1: 0, 0: 1} will transpose a 2D matrix
        """
        new_tr = list(range(len(tr)))
        for i, j in tr.items():
            new_tr[i] = self.data.dims[j]
        return self.from_xarray(self.data.transpose(*new_tr))

    def index_to_scale(self, axis, i):
        """Retrieve the coordinate corresponding to index i
        :return: float representing the coordinate value of index i
        """
        return self.coord_min[axis] + self.delta[axis]*i

    def scale_to_index(self, axis, coord_val):
        """Retrieve the index (may not be an integer) representing coord_val on axis
        :return: float representing index of coordinate
        """
        return (coord_val - self.coord_min[axis])/self.delta[axis]

    @property
    def T(self):
        return self.from_xarray(self.data.T)

    @property
    def data(self) -> xr.DataArray:
        """Returns DataArray"""
        return self._data

    @property
    def dims(self):
        return self._data.dims

    @property
    def values(self) -> np.array:
        """Returns np.array represented by DataArray"""
        return self._data.values

    @property
    def ndim(self) -> int:
        return self._data.ndim

    @property
    def shape(self):
        return self._data.shape

    @property
    def offset(self):
        return self.coord_min

    @staticmethod
    def from_numpy_array(dat: np.array, axes=None, delta=None, coord_min=None, dims=None):
        """
        Build data using a numpy array. Must provide one of the following:
        - An iterable of axes, where each axis is a numpy array
        - An interable of delta and coord_min
        Guarantees regularly gridded coordinates and sorts data so that coordinates are ascending
        """
        return RegularDataArray(dat, axes=axes, delta=delta, coord_min=coord_min, dims=dims)

    @staticmethod
    def from_xarray(dat: xr.DataArray):
        coord_min = np.array([dat[dim].values[0] for dim in dat.dims])
        delta = np.array([dat[dim].values[1] - dat[dim].values[0] for dim in dat.dims])
        return RegularDataArray(dat.values, delta=delta, coord_min=coord_min, dims=dat.dims)

    @staticmethod
    def from_xarray_irregular(dat: xr.DataArray):
        coord_min = np.array([dat[dim].values[0] for dim in dat.dims])
        delta = np.array([np.mean(np.diff(dat[dim].values)) for dim in dat.dims])
        return RegularDataArray(dat.values, delta=delta, coord_min=coord_min, dims=dat.dims)


class RegularSpacedData(object):
    """Object representing regularly spaced data. Irregularly spaced data must be interpolated onto a regularly spaced
    grid. Data will be sorted such that coordinates are monotonically increasing."""
    def __init__(self, dat: Union[np.array, None] = None, axes=None, delta=None, coord_min=None):
        self._data: np.array = np.array([])
        self.axes: list = []
        self.coord_min: np.array = np.array([])
        self.coord_max: np.array = np.array([])
        self.N: np.array = np.array([])
        self.delta: np.array = np.array([])

    @property
    def data(self) -> np.array:
        return self._data

    @property
    def mat(self) -> np.array:
        return self._data

    @mat.setter
    def mat(self, val: np.array) -> None:
        self._data = val
        if self.N.size != 0 and np.any(self.N != self._data.shape):
            msg = "Data has shape {0} but has been assigned new data of shape {1}. Resetting coordinates."
            warnings.warn(msg.format(self.N, self._data.shape), RuntimeWarning, stacklevel=2)
        self.coord_min = np.zeros(self.dims)
        self.delta = np.ones(self.dims)
        self._update()

    def _update(self) -> None:
        self.N = np.array(self._data.shape)
        self.axes = [cmin + cdelta*np.arange(n) for cmin, cdelta, n in zip(self.coord_min, self.delta, self.N)]
        self.coord_max = np.array([ax[-1] for ax in self.axes])

    @property
    def shape(self) -> tuple:
        return tuple(self.N)

    @property
    def dims(self) -> int:
        return self._data.ndim

    @property
    def ndim(self) -> int:
        return self._data.ndim

    def slice(self, *index):
        grab_axes = [i for i, x in enumerate(index) if isinstance(x, slice)]
        delta = np.copy(self.delta[grab_axes])
        coord_min = np.copy(self.coord_min[grab_axes])
        return RegularSpacedData.from_numpy_array(self._data[tuple(index)], delta=delta, coord_min=coord_min)

    def slice_dat(self, *index):
        return self._data[tuple(index)]

    def T(self):
        return RegularSpacedData.from_numpy_array(self._data.T, delta=np.array([self.delta[1], self.delta[0]]),
                                                  coord_min=np.array([self.coord_min[1], self.coord_min[0]]))

    @staticmethod
    def from_numpy_array(dat: np.array, axes=None, delta=None, coord_min=None):
        """Build data using a numpy array. Must provide one of the following:
        - An iterable of axes, where each axis is regularly spaced
        - An interable of delta and coord_min."""
        data = RegularSpacedData()
        data.delta = np.ones(len(dat.shape))
        data.coord_min = np.zeros(len(dat.shape))
        if axes is not None:
            if any([len(ax) != dat.shape[i] for i, ax in enumerate(axes)]):
                raise ValueError('Axis shape {0} does not match data shape {1}'.format([ax.shape for ax in axes], dat.shape))
            sort = [ax.argsort() for ax in axes]
            axes = [ax[s] for s, ax in zip(sort, axes)]
            for i in range(len(axes)):
                data.delta[i] = axes[i][1] - axes[i][0]
                data.coord_min[i] = axes[i][0]
            data._data = np.copy(dat[tuple(sort)])
        else:
            order = [slice(None) for i in range(dat.ndim)]
            if delta is not None:
                for i in range(len(delta)):
                    if delta[i] < 0:
                        data.delta[i] = -1 * delta[i]
                        order[i] = slice(None, None, -1)
                        if coord_min is not None:
                            data.coord_min[i] = coord_min[i] + (data._data.shape[i] - 1)*delta[i]
                    else:
                        data.delta[i] = delta[i]
                        if coord_min is not None:
                            data.coord_min[i] = coord_min[i]
            elif coord_min is not None:
                for i in range(len(coord_min)):
                    data.coord_min[i] = coord_min[i]
            data._data = np.copy(dat[tuple(order)])
        data.N = np.array(dat.shape)
        data.axes = [data.coord_min[i] + data.delta[i]*np.arange(data.N[i]) for i in range(data.dims)]
        data.coord_max = np.array([data.axes[i].max() for i in range(data.dims)])
        return data

    @staticmethod
    def from_xarray_dataarray(darray):
        """Build an array from an xarray DataArray. Any dimension with a length of 1 will be removed. If irregular,
        a regular grid will be approximately constructed using the min, max, and number of elements for each coord"""
        data = RegularSpacedData()
        data._data = darray.values.squeeze()
        axes = [x.values for x in darray.coords.values() if x.size > 1]  # filter out axes with only one point
        data.N = np.array([x.size for x in axes])
        data.coord_min = np.array([np.min(x) for x in axes])
        data.coord_max = np.array([np.max(x) for x in axes])
        data.delta = (data.coord_max - data.coord_min)/(data.N - 1)
        data.axes = [data.coord_min[i] + data.delta[i]*np.arange(data.N[i]) for i in range(data.dims)]
        return data
