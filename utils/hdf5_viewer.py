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
        self.load_datafile_tree()
        self.datafile_treeview_Y.selectionModel().selectionChanged.connect(self.update_plot)
        
    def initialise_plot(self):
        self.data_plot = pg.PlotWidget()
        self.plot_grid.replaceWidget(self.plot_widget, self.data_plot)
        self.data_plot.setBackground('w')
        
    def load_datafile_tree(self):
        """ build QTreeView from hdf5 dataset. The name of each dataset or group is a QStandardItem """
        self.datafile_tree_model = QStandardItemModel()
        self.datafile_treeview_X.setModel(self.datafile_tree_model)
        self.treeview_root = self.datafile_tree_model.invisibleRootItem()  # get root item
        self.load_datafile_branch(self.datafile, self.treeview_root)
        self.datafile_treeview_Y.setModel(self.datafile_treeview_X.model()) # copy tree for Y axis
        
    def load_datafile_branch(self, datafile_group, tree_item):
        """ populate branch with datasets and recursively build sub-branches """
        for row_counter, key in enumerate(datafile_group.keys()):
            tree_item.insertRow(row_counter, QStandardItem(key))
            if isinstance(datafile_group[key], h5py.Group):
                """ recursively build a tree branch for each datafile group """
                self.load_datafile_branch(datafile_group[key], tree_item.child(row_counter))
        
    #def load_attributes(self)
                
    def get_attributes(self, datafile_item):
        """
        Returns python dictionary of attributes
        
        datafile_item: h5py group or dataset        
        """
        if isinstance(datafile_item, (h5py.Group, h5py.Dataset) ):
            attributes = {}
            for attr_name, attr_value in datafile_item.attrs.items():
                attributes[attr_name] = attr_value
            return attributes
    
    def update_plot(self):
        """ check selected datasets and update plot """
        # get selected treeview items, selectedIndexes() returns QModelIndex objects
        selected_indices = self.datafile_treeview_Y.selectionModel().selectedIndexes()
        for index in selected_indices:
            # convert QModelIndex objects into hdf5 datafile paths
            tree_item = self.datafile_treeview_Y.model().itemFromIndex(index)
            item_label = tree_item.text()
            datafile_item = [item_label]
            parent_item = tree_item.parent()
            while parent_item is not None:
                datafile_item.insert(0, parent_item.text() )
                parent_item = parent_item.parent()
            print(datafile_item)
        
        
if __name__ == '__main__' :
    
    from nanomol.utils.hdf5_datafile import hdf5_datafile
    
    myDatafile = hdf5_datafile(mode='r')
    
    myViewer_app = QtWidgets.QApplication([])
    myViewer = hdf5_viewer(myDatafile)
    myViewer.show()
    myViewer_app.exec()
    