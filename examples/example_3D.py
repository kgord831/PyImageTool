from pyimagetool import imagetool
from pyimagetool.data import arpes_data_3d

data = arpes_data_3d()
tool = imagetool(data)
# after closing the ImageTool window, you can access data from the imagetool
# this will only run if matplotlib exists in lib
try:
    import matplotlib
    tool.get('xy').plot(cmap='viridis')
except ImportError:
    print(tool.get('xy'))
