from pyimagetool import imagetool
from pyimagetool.data import arpes_data_2d

# load in data, here I use example data from pyimagetool
data = arpes_data_2d()
# create and show the image tool (blocks until window is closed)
imagetool(data)
