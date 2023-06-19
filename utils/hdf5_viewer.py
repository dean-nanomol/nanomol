# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 10:39:21 2023

@author: deankos
"""

import h5py
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class hdf5_viewer(QtWidgets.QWidget):
    
    def __init__(self, datafile):
        super(hdf5_viewer, self).__init__()
        self.datafile = datafile
        uic.loadUi(r'hdf5_viewer.ui', self)
        self.initialise_plot()
        self.build_datafile_tree()
        
    def initialise_plot(self):
        self.data_plot = pg.PlotWidget()
        self.plot_grid.replaceWidget(self.plot_widget, self.data_plot)
        self.data_plot.setBackground('w')
        
    def build_datafile_tree(self):
        self.datafile_tree_model = QStandardItemModel()
        self.datafile_treeview.setModel(self.datafile_tree_model)
        self.treeview_root = self.datafile_tree_model.invisibleRootItem()
        self.build_datafile_branch(self.datafile, self.treeview_root)
        
    def build_datafile_branch(self, datafile_group, tree_item):
        for row_counter, key in enumerate(datafile_group.keys()):
            tree_item.insertRow(row_counter, QStandardItem(key))
            if isinstance(datafile_group[key], h5py.Group):
                """ recursively build a branch from each group """
                self.build_datafile_branch(datafile_group[key], tree_item.child(row_counter))
        
        
if __name__ == '__main__' :
    
    from nanomol.utils.hdf5_datafile import hdf5_datafile
    
    myDatafile = hdf5_datafile(mode='r')
    
    myViewer_app = QtWidgets.QApplication([])
    myViewer = hdf5_viewer(myDatafile)
    myViewer.show()
    myViewer_app.exec()
    