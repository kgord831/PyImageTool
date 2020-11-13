# PyImageTool

This is a Python Image Tool which is heavily inspired by the Igor Pro native Image Tool written by the Advanced Light Source (ALS). This project aims to build a highly interactive tool which can be used to rapidly visualize and analyze multidimensional data (up to four dimensions). The project leverages the pyqtgraph library for rapid visualization and is cross-platform.

![PyImageTool Demo](usage.gif)

## Install

### With anaconda

Use the Anaconda Package Manager and install packages from the conda-forge channel when possible. Also, don't be a fool---create a virtual environment.
```
conda create --name imagetool
conda activate imagetool
conda install -c conda-forge numpy xarray pyqtgraph
python setup.py install
```
where the virtual env name ``imagetool`` may be changed for a name of your choice.

You can test the install using ``pytest``. Install the ``pytest`` package and then run ``test_PyImageTool.py`` in the ``tests`` subfolder.
```
conda install -c conda-forge pytest pytest-qt
pytest test_PyImageTool.py
```

### With pip

Create a pip virtual environment.
```
python -m venv imagetool
```
Activate your virtual environment and change into the ``src`` directory where ``setup.py`` is located. Now run
```
pip install .
```

You can test the install using ``pytest``. Install the ``pytest`` package and then run ``test_PyImageTool.py`` in the ``tests`` subfolder.
```
pip install pytest pytest-qt
pytest test_PyImageTool.py
```

## Testing

You can test the installation with ``pytest`` and ``pytest-qt`` using ``test_PyImageTool.py`` in the ``tests`` subfolder. If you don't have these in your env, install them.
```
conda install -c conda-forge pytest pytest-qt
pytest test_PyImageTool.py
```

## Quick Guide

### Controls
- Hold shift to drag the cursors to mouse location.
- While hovering over the cursor index or cursor coordinate spinbox, use the middle mouse wheel to move by increments of 1. Hold control and scroll middle mouse wheel to move by increments of 10
- Left-click and drag to move image/plot
- Right-click and drag to resize (horizontal drag resizes horizontally, vertical drag resizes vertically)
- Ctrl+A will undo manipulations to view all data
- Right-click to open a menu. If you right-click on an image, you can set the aspect ratio
- Export feature currently not working

### Editing Colormaps
- Right-click image, and select "Edit Color Map"
- Color map normalizations on top, choices are "Power Law" or "Piecewise." Power law useful for quickly rescaling to make weak features stronger or vice versa with the gamma control, but piecewise gives you much more control.
- You can always see how the colormap is changing in the top right image of the colorbar.
- Bottom right is a histogram of the data. The x-axis is the value in the data and the y-axis is normalized weight at that value. For example, an image of a gaussian (z = exp(-x^2-y^2)) would have a large amount of weight at x-axis=0 falling off rapidly to almost zero at x-axis=1 (because there is only one point where z = 1 which is at x=0, y=0 in the image).
- As the cursor scans the histogram, an isosurface appears in the data showing the contours of constant value. Because the algorithm that computes the isocurve is pure python, it is slow. If the tool noticeably slows down, consider disabling the isocurve calculations by unticking the box in the top left.
- In addition to the histogram, a line is drawn representing how values in your data is mapped to the colorbar. Imagine the colorbar is the y-axis and values in the image are on the x-axis. By default, color scales are linear. As you change gamma in power-law mode, you will see this curve become nonlinear, as the colorbar will noticeably deform.
- If the color map editor is in piecewise mode, you can drag points representing the max and min of the color scale. Furthermore, by right-clicking in the histogram area, you can add more points. This is useful for forcing your colorbar to highlight a region between two isosurfaces.

You are of course welcome and encouraged to install matplotlib along with this tool for rendering your high quality figures.

## Examples

In the ``examples`` folder, you will find a few scripts and a Jupyter Notebook to help you use this tool for your work.

## Goals
- [ ] Downsample data
- [ ] Export custom colormaps to matplotlib
- [ ] Export data to Jupyter notebook
- [ ] Import common multidimensional data files (HDF5)
- [ ] Create an equivalent matplotlib figure given a plot/image
- [ ] Layout management
- [ ] Color ROI

## Colormaps

The philosophy of this tool regarding colormaps is simple: don't change your data, change the way you view it. There are several perceptually uniform colormaps built into the tool and a few non-perceptually uniform colormaps. You can add more by ``numpy.save``'ing a ``(N, 3) np.uint8`` array into the ``cmaps`` directory and then running ``make_icons.py``. You will have to restart the tool to load. Use the interactive colormap editor in piecewise mode to highlight specific parts of your data.

## The Future

A future goal is better integration with Jupyter Notebook. Existing javascript visualization libraries such as Bokeh exist (with higher level APIs such as Holoviews), but my attempts at writing a Bokeh image tool end up atrociously slow. Libraries like Holoviews are promising but their API has been difficult for me to work with. This is built on Qt, a mature platform for GUI design, and it's blazing fast. While not embedded in a Jupyter cell, you can still call it from Jupyter and work with the generated window.