# PyImageTool

This is a Python Image Tool which is heavily inspired by the Igor Pro native Image Tool written by the Advanced Light Source (ALS). This project aims to build a highly interactive tool which can be used to rapidly visualize and analyze multidimensional data (up to four dimensions). The project leverages the pyqtgraph library for rapid visualization and is cross-platform.

![PyImageTool Demo](usage.gif)

## Install

Use the Anaconda Package Manager and install packages from the conda-forge channel when possible. Also, don't be a fool---create a virtual environment.
```
conda create --name arpes
conda activate arpes
conda install python=3.7
conda install -c conda-forge numpy xarray pyqtgraph
python setup.py install
```
where the virtual env name ``arpes`` may be changed for a name of your choice.

You can test the installation. Suppose you cloned the repo (with folders pyimagetool, examples, and tests) into a folder named src.
```
python -m src.examples.test_pyimagetool
```
and you should see an Image Tool be displayed within a few seconds.

You are of course welcome and encouraged to install matplotlib along with this tool for rendering your high quality figures.

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