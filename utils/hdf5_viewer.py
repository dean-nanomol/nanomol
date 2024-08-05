# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 10:39:21 2023

@author: deankos
"""

import numpy as np
import os
import h5py
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from nanomol.utils.interactive_ui import interactive_ui

class hdf5_viewer(interactive_ui):
    
    def __init__(self, datafile):
        super().__init__()
        self.datafile = datafile
        ui_file_path = os.path.join(os.path.dirname(__file__), 'hdf5_viewer.ui')
        uic.loadUi(ui_file_path, self)
        self.initialise_plot()
        self.connect_widgets_by_name()
        self.reload_datafile_pushbutton.clicked.connect(self.reload_datafile)
        self.modifier_X_comboBox.currentTextChanged.connect(self.update_data_toPlot_X)
        self.modifier_Y_comboBox.currentTextChanged.connect(self.update_data_toPlot_Y)
        self.reload_datafile()
        self.data_Y_toPlot = []
        self.data_X_toPlot = []
        self.data_plot_labels = []
        
    def initialise_plot(self):
        self.data_plot = pg.PlotWidget()
        self.plot_grid.replaceWidget(self.plot_widget, self.data_plot)
        self.data_plot.setBackground('w')
        self.plot_format = {'symbol':'o',
                            'symbolSize':3}
        self.data_plot.addLegend()
        
    def load_datafile_tree(self):
        """ make QTreeView from hdf5 dataset. The name of each dataset or group is a QStandardItem """
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
    
    def load_attributes(self, datafile_item):
        """ display hdf5 attributes of datafile_item in QTableView widget """
        self.attrs_table_model = QStandardItemModel()
        self.attrs_tableview.setModel(self.attrs_table_model)
        self.attrs_tableview_root = self.attrs_table_model.invisibleRootItem()
        for attr_name, attr_value in datafile_item.attrs.items():
            # convert attribute value into str, otherwise display type only
            try:
                attr_value = str(attr_value)
            except:
                attr_value = str(type(attr_value))
            self.attrs_tableview_root.appendRow([QStandardItem(attr_name), QStandardItem(attr_value)] )
    
    def update_data_toPlot_Y(self):
        """ update data for plotting from treeView selection """
        self.data_Y_toPlot = []
        self.data_plot_labels = []
        # get selected treeview items for Y axis of plot
        selected_indices = self.datafile_treeview_Y.selectionModel().selectedIndexes()
        for i, item_index in enumerate(selected_indices):
            # convert QModelIndex objects into hdf5 datafile paths
            tree_item = self.datafile_treeview_Y.model().itemFromIndex(item_index)
            item_label = tree_item.text()
            data_label = item_label
            datafile_directory = [item_label]
            parent_item = tree_item.parent()
            while parent_item is not None:
                # itereate through parent items to get full path from root
                datafile_directory.insert(0, parent_item.text() )
                parent_item = parent_item.parent()
            
            datafile_item = self.datafile[datafile_directory.pop(0)]
            # get actual datafile item (group or dataset) corresponding to selected item
            for datafile_key in datafile_directory:
                datafile_item = datafile_item[datafile_key]
            if isinstance(datafile_item, h5py.Dataset):
                # only append to data for plotting if datafile item is a dataset
                data_to_plot = self.apply_data_modifier(np.array(datafile_item), self.modifier_Y)
                self.data_Y_toPlot.append(data_to_plot)
                self.data_plot_labels.append(data_label)
            if i==(len(selected_indices)-1):
                # show dataset/group attributes for last selected item
                self.item_for_attrs_view = datafile_item
                self.load_attributes(self.item_for_attrs_view)
        self.update_plot()
        
    def update_data_toPlot_X(self):
        self.data_X_toPlot = []
        # get selected treeview item for X axis
        # selection limited to 1 item from treeview selectionMode property in .ui file
        selected_index = self.datafile_treeview_X.selectionModel().selectedIndexes()
        if len(selected_index)>0:   # check if an item is selected
            selected_index = selected_index[0]
            tree_item = self.datafile_treeview_X.model().itemFromIndex(selected_index)
            item_label = tree_item.text()
            datafile_directory = [item_label]
            parent_item = tree_item.parent()
            while parent_item is not None:
                datafile_directory.insert(0, parent_item.text() )
                parent_item = parent_item.parent()
            datafile_item = self.datafile[datafile_directory.pop(0)]
            for datafile_key in datafile_directory:
                datafile_item = datafile_item[datafile_key]
            if isinstance(datafile_item, h5py.Dataset):
                # only append to data for plotting if datafile item is a dataset
                data_to_plot = self.apply_data_modifier(np.array(datafile_item), self.modifier_X)
                self.data_X_toPlot.append(data_to_plot)
            self.item_for_attrs_view = datafile_item
            self.load_attributes(self.item_for_attrs_view)
            self.update_plot()
                    
    def update_plot(self):
        """ plot currently selected data """
        self.data_plot.clear()
        N_lines = len(self.data_Y_toPlot)
        for (data_Y, label, color_index) in zip(self.data_Y_toPlot, self.data_plot_labels, range(N_lines)):
            # set line and marker colours
            color = pg.intColor(color_index, hues=N_lines)
            pen = pg.mkPen(color=color, width=1)
            self.plot_format.update({'symbolPen': pen,
                                     'symbolBrush': pg.mkBrush(color=color) })
            if self.data_X_Y_are_plot_compatible():
                try:    
                    self.data_plot.plot(self.data_X_toPlot[0], data_Y, name=label, pen=pen, **self.plot_format)
                    self.data_plot.setLabel('bottom', '')
                except Exception as exception:
                    print('Exception: {}'.format(exception) )
            else:
                try:
                    self.data_plot.plot(range(len(data_Y)), data_Y, name=label, pen=pen, **self.plot_format)
                    self.data_plot.setLabel('bottom', 'index')
                except Exception as exception:
                    print('Exception: {}'.format(exception) )
                         
    def data_X_Y_are_plot_compatible(self):
        """ check if current X and Y data exist and are size compatible for plotting """
        if len(self.data_Y_toPlot)>0 and len(self.data_X_toPlot)>0:
            for data_Y in self.data_Y_toPlot:
                if len(data_Y) != len(self.data_X_toPlot[0]):
                    return False
            return True
        else:
            return False
        
    def apply_data_modifier(self, dataset, modifier):
        if modifier == 'none':
            return dataset
        elif modifier == 'abs(x)':
            return abs(dataset)
        elif modifier == 'sqrt(x)':
            return dataset**0.5
        elif modifier == 'sqrt(abs(x))':
            return abs(dataset)**0.5
        elif modifier == 'log10(x)':
            return np.log10(dataset)
        elif modifier == 'log10(abs(x))':
            return np.log10(abs(dataset))
        
    def reload_datafile(self):
        self.load_datafile_tree()
        self.datafile_treeview_Y.selectionModel().selectionChanged.connect(self.update_data_toPlot_Y)
        self.datafile_treeview_X.selectionModel().selectionChanged.connect(self.update_data_toPlot_X)
        
if __name__ == '__main__' :
    
    from nanomol.utils.hdf5_datafile import hdf5_datafile
    
    myDatafile = hdf5_datafile(mode='r')
    
    myViewer_app = QtWidgets.QApplication([])
    myViewer = hdf5_viewer(myDatafile)
    myViewer.show()
    myViewer_app.exec()
    