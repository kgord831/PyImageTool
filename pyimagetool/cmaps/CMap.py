from pathlib import Path
from xml.dom import minidom
import numpy as np
from PIL import Image
try:
    import matplotlib.cm as cm
    from matplotlib.colors import ListedColormap
except ImportError:
    cm = None
try:
    import pyqtgraph.Qt as qt
except ImportError:
    qt = None

CET_NAMES = {
    'CET-L1': 'CET-L-Gry',
    'CET-L4': 'CET-L-Red-Yel',
    'CET-L5': 'CET-L-Blk-Grn-Yel',
    'CET-L6': 'CET-L-Blk-Blu-Cyn',
    'CET-L13': 'CET-L-Red',
    'CET-L14': 'CET-L-Grn',
    'CET-L15': 'CET-L-Blu',
    'CET-D1A': 'CET-D-Blu-Wht-Red',
    'CET-D4': 'CET-D-Blu-Blk-Red',
    'CET-D13': 'CET-D-Blu-Wht-Grn',
    'CET-R2': 'CET-R-Blu-Grn-Yel-Red',
    'CET-C2': 'CET-C-Mrn-Yel-Grn-Blu',
    'CET-C4': 'CET-C-Red-Wht-Blu',
    'CET-C5': 'CET-C-Gry'
         }

SCIVIS_NAMES = {
    'mellow-rainbow': 'mellow_rainbow',
    'gr-insert_40-50': 'highlight',
    'gr-insert_40-60': 'highlight_2',
    'blue-orange-div': 'blue_orange'
         }

MPL_NAMES = {
    'viridis': 'viridis',
    'plasma': 'plasma',
    'inferno': 'inferno',
    'magma': 'magma',
    'bone': 'bone',
    'afmhot': 'afmhot',
    'seismic': 'seismic',
    'hsv': 'hsv',
    'gist_heat': 'gist_heat',
    'gist_rainbow': 'gist_rainbow',
    'jet': 'jet',
    'nipy_spectral': 'nipy_spectral'
}

modulepath = Path(__file__).parent


class CMap:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CMap, cls).__new__(cls)
            cls._instance.cmaps = []
            cls._instance.colortables = {}
            cls._instance.pixmaps = {}
            cls._instance.icons = {}
            cls._instance.reload()
        return cls._instance

    def reload(self):
        self.make_cet_maps()
        self.make_scivis_maps()
        if cm:
            self.make_mpl_maps()
        self.make_icons()
        self.cmaps = self.update_cmap_list()

    def clear_cache(self):
        self.colortables = {}
        self.pixmaps = {}
        self.icons = {}

    def load_ct(self, name='viridis'):
        if name in self.colortables:
            return self.colortables[name]
        elif name in self.cmaps:
            filepath = Path(modulepath, 'data', name + '.npy')
            dat = np.load(str(filepath)).astype(np.uint8)
            self.colortables[name] = dat
            return dat
        else:
            raise FileNotFoundError(f'Colormap "{name}" is not loaded, try reloading.')

    def load_icon(self, name='viridis'):
        if qt:
            if name in self.icons:
                return self.icons[name]
            elif name in self.cmaps:
                filepath = Path(modulepath, 'data', name + '.jpg')
                icon = qt.QtGui.QIcon(str(filepath))
                self.icons[name] = icon
                return icon
            else:
                raise FileNotFoundError(f'Colormap "{name}" is not loaded, try reloading.')
        else:
            raise ImportError("Failed to import pyqtgraph, method load_icon() not available.")

    def load_pixmap(self, name='viridis'):
        if qt:
            if name in self.pixmaps:
                return self.pixmaps[name]
            elif name in self.cmaps:
                filepath = Path(modulepath, 'data', name + '.jpg')
                pixmap = qt.QtGui.QPixmap.fromImage(qt.QtGui.QImage(str(filepath)))
                self.pixmaps[name] = pixmap
                return pixmap
            else:
                raise FileNotFoundError(f'Colormap "{name}" is not loaded, try reloading.')
        else:
            raise ImportError("Failed to import pyqtgraph, method load_pixmap() not available.")

    @staticmethod
    def update_cmap_list():
        filelist = Path(modulepath, 'data').glob('*.npy')
        return [fp.stem for fp in filelist]

    @staticmethod
    def make_cet_maps():
        filelist = Path(modulepath, 'data', 'CETperceptual_csv_0_255').glob('*.csv')
        for filepath in filelist:
            cmap_name = filepath.stem
            if cmap_name in CET_NAMES:
                dat = np.loadtxt(str(filepath), dtype=np.uint8, delimiter=',')
                newpath = Path(modulepath, 'data', CET_NAMES[cmap_name])
                np.save(newpath, dat)

    @staticmethod
    def make_scivis_maps():
        filelist = Path(modulepath, 'data', 'scivis_cmaps').glob('*.xml')
        for filepath in filelist:
            cmap_name = filepath.stem
            if cmap_name in SCIVIS_NAMES:
                xmldoc = minidom.parse(str(filepath))
                pts = xmldoc.getElementsByTagName('Point')
                x_pnts = np.empty(len(pts))
                read_pnts = np.empty((len(pts), 3))
                for i, pt in enumerate(pts):
                    x_pnts[i] = float(pt.attributes['x'].value)
                    r = float(pt.attributes['r'].value)
                    g = float(pt.attributes['g'].value)
                    b = float(pt.attributes['b'].value)
                    read_pnts[i, 0] = r
                    read_pnts[i, 1] = g
                    read_pnts[i, 2] = b
                dat = np.empty((256, 3), dtype=np.uint8)
                dat[:, 0] = np.round(255 * np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 0])).astype(np.uint8)
                dat[:, 1] = np.round(255 * np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 1])).astype(np.uint8)
                dat[:, 2] = np.round(255 * np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 2])).astype(np.uint8)
                newpath = Path(modulepath, 'data', SCIVIS_NAMES[cmap_name])
                np.save(newpath, dat)

    @staticmethod
    def make_mpl_maps():
        cmaps = list(MPL_NAMES.keys())
        for i, cmap_name in enumerate(cmaps):
            dat = np.round(255*cm.get_cmap(cmap_name)(np.arange(256))).astype(np.uint8)
            dat = dat[:, 0:3]
            newpath = Path(modulepath, 'data', MPL_NAMES[cmap_name])
            np.save(newpath, dat)

    @staticmethod
    def make_icons(height=12, width=64):
        filelist = Path(modulepath, 'data').glob('*.npy')
        for filepath in filelist:
            cmap_name = filepath.stem
            mat = np.load(str(filepath))
            mat = mat[:, 0:3]
            rows, cols = mat.shape
            if cols < 3 or rows != 256 or mat.dtype != np.uint8:
                print(str(filepath) + ' unsupported format. Requires 256 rows and 3 columns.'
                      + f' Has rows={rows} and cols={cols}. Skipping...')
                continue
            if mat.dtype != np.uint8:
                print(str(filepath) + f' must have dtype=np.uint8. Has type {mat.dtype}. Skipping...')
                continue
            colorbar = np.ones((height, width, 3), dtype=np.uint8)
            colorbar *= mat[np.newaxis, ::256//width, :]
            colorbar_ico = Image.fromarray(colorbar)
            colorbar_ico.save(Path(modulepath, 'data', cmap_name + '.jpg'), 'jpeg')
