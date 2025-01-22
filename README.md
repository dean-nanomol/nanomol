Code repository of the eMolMat team in the Nanomol group at the Institute of Materials Science of Barcelona (ICMAB-CSIC).

# Getting started
To run any of the code in this repository you will need to install Python on your computer. The recommended way is to install the Anaconda Python distribution, which includes many packages for data analysis and interaction with lab equipment. Download the Anaconda distribution from the following link and install with default settings:\
https://www.anaconda.com/download/success

This will have installed the Spyder development environment and the Jupyter Notebook application, which should now appear among your installed programs. Jupyter Notebook is useful for interactive data analysis, while Spyder is best used for developing and running code for lab equipment.

To install additional packages use either the graphical interface of Anaconda called Anaconda Navigator (already installed with Anaconda), or the `conda` command through the Anaconda Prompt (also already installed). For example, to install the pyqtgraph package check the availability of the package in the Anaconda repository (https://anaconda.org/anaconda/pyqtgraph), open the Anaconda Prompt and type `conda install anaconda::pyqtgraph` and follow the on-screen prompts to complete the installation. Avoid using `pip` unless the package is not available in the Anaconda repository.

## Using the repository
Install [GitHub Desktop](https://desktop.github.com/download/) and create a GitHub account. Once installed, look for this repository (`dean-nanomol/nanomol`) in the search bar and clone the repository to your computer. Then open Spyder, top menu bar -> Tools -> PYTHONPATH manager, and add the GitHub folder to the list of paths (on Window it is usually C:\Users\...\Documents\GitHub). This way Spyder will know where to look for modules if you use code from this repository.

## Data analysis
If you are new to Python take some time to familiarise yourself with its syntax, data structures, and most common packages. Here are some resources to get you started:\
https://pynative.com/python-exercises-with-solutions/ (includes a link to an [Online Code Editor](https://pynative.com/online-python-code-editor-to-execute-python-code/) to execute code in the browser)\
https://inventwithpython.com/pythongently/

A conventient way to analyse and plot data is to use Jupyter Notebooks with the Matplotlib package. Here is a tutorial to get started (skip the installation section, since you already installed everything through Anaconda):\
https://www.geeksforgeeks.org/using-matplotlib-with-jupyter-notebook/

If analysing data from the lab you will need to use the HDF5 data format. You can read and write these files with the h5py package that comes with Anaconda, but you will need to write some code. Here are some resources to get you started:\
https://docs.h5py.org/en/latest/quick.html
https://pythonforthelab.com/blog/how-to-use-hdf5-files-in-python/

The repository has an [HDF5 Viewer](/utils/hdf5_viewer.py) that you can execute in Spyder to open and browse an HDF5 file in read-only mode.

## Programming laboratory instruments
Follow these video tutorials to get started:\
[Programming scientific instruments in Python - Part 1](https://www.youtube.com/watch?v=XhUGKqORBGM) \
[Programming scientific instruments in Python - Part 2](https://www.youtube.com/watch?v=XR8fJh21wLs)
