# -*- coding: utf-8 -*-
"""
Created on Mon Sep  4 17:50:35 2023

@author: deankos
"""

import numpy as np
import threading
import time
import os
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class current_vs_time(interactive_ui):
    """
    Class to measure transistor output over time. Set V_GS and V_DS and start measurement.
    Measurements always record time and measured V and I values for both channels.
    Run measurement until the time limit, or set time limit to -1 to run indefinitely.
    """
    
    update_plots_signal = pyqtSignal()
    
    def __init__(self, smu, datafile=None):
        super().__init__()
        if datafile is not None:
            self.default_datafile = datafile
        self.datafile = datafile
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'current_vs_time.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.start_pushbutton.clicked.connect(self.start_measurement)
        self.stop_pushbutton.clicked.connect(self.stop_measurement)
        self.reset_plot_widgets_pushbutton.clicked.connect(self.setup_plot_widgets)
        self.shutdown_pushbutton.clicked.connect(self.shutdown)
        self.update_plots_signal.connect(self.update_plots)
        self.setup_plot_widgets()
        self.measurement_is_running = False
        
    def start_measurement(self, *args, datafile=None, path=None):          
        """
        datafile : hdf5 datafile [optional, default=None]
            hdf5 data file where data of the measurement will be saved. Useful when calling externally.
            If passed must also pass data_path. If not passed defaults to saving to default_datafile.
        
        path : str [optional, default=None]
            Path to hdf5 group within passed datafile where data is to be saved.
            Usually generated within calling environment using hdf5_group.name
            If not passed, defaults to saving in root group of default_datafile.
        """
        # *args captures unnecessary arguments passed by qt buttons
        if datafile is not None:
            self.datafile = datafile
            self.data_path = datafile[path]
        else:
            self.datafile = self.default_datafile
            self.data_path = self.datafile
        if not self.measurement_is_running:  # do nothing if measurement is already running
            self.measurement_is_running = True
            self.measurement_thread = threading.Thread(target=self.run_measurement)
            self.measurement_thread.start()
            
    def stop_measurement(self):
        if self.measurement_is_running:
            self.measurement_is_running = False
            
    def run_measurement(self):
        self.clear_plots()
        self.configure_measurement()
        self.create_new_plot_lines()
        self.smu.set_source_level(self.ch_GS, 'v', self.V_GS)
        self.smu.set_source_level(self.ch_DS, 'v', self.V_DS)
        active_V_GS = self.V_GS
        active_V_DS = self.V_DS
        t0 = time.time()
        t = 0
        self.smu.set_output(self.ch_GS, 1)
        self.smu.set_output(self.ch_DS, 1)
        while self.measurement_is_running:
            if t > self.t_limit:
                self.measurement_is_running = False
            if self.V_GS != active_V_GS:
                # set voltage only if changed
                self.smu.set_source_level(self.ch_GS, 'v', self.V_GS)
            if self.V_DS != active_V_DS:
                self.smu.set_source_level(self.ch_DS, 'v', self.V_DS)
            measured_I_GS, measured_V_GS = self.smu.measure(self.ch_GS, 'iv')
            measured_I_DS, measured_V_DS = self.smu.measure(self.ch_DS, 'iv')
            self.data['time'].append(t)
            self.data['V_GS'].append(measured_V_GS)
            self.data['I_GS'].append(measured_I_GS)
            self.data['V_DS'].append(measured_V_DS)
            self.data['I_DS'].append(measured_I_DS)
            self.update_plots_signal.emit()
            t = time.time() - t0
        self.smu.set_output(self.ch_GS, 0)
        self.smu.set_output(self.ch_DS, 0)
        self.save_data()
        
    def configure_measurement(self):
        self.smu.set_source_function('a', 1)
        self.smu.set_source_function('b', 1)
        self.initialise_datasets()
        if self.t_limit == -1:
            self.t_limit = np.inf
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()) )
        
    def initialise_datasets(self):
        self.data = {'time': [],
                     'V_GS': [],
                     'I_GS': [],
                     'V_DS': [],
                     'I_DS': []  }
        
    def save_data(self):
        """ write data to hdf5 datafile """
        active_group = self.datafile.get_unique_group_name(self.data_path, basename=self.description, max_N=9999)
        self.active_group = self.data_path.create_group(active_group)
        self.active_group.attrs.create('description', self.description)
        self.active_group.attrs.create('timestamp', self.timestamp)
        self.active_group.attrs.create('measurement_type', 'current_vs_time')
        self.active_group.attrs.create('channel_GS', self.ch_GS)
        self.active_group.attrs.create('channel_DS', self.ch_DS)
        for key, value in self.smu.get_settings().items():
            self.active_group.attrs.create('keithley_{}'.format(key), value)
        for dataset_name, data in self.data.items():
            self.active_group.create_dataset(dataset_name, data=np.array(data) )
        self.data_path.file.flush()
    
    def setup_plot_widgets(self):
        self.plot_layout.removeWidget(self.I_DS_vs_time)
        self.plot_layout.removeWidget(self.I_GS_vs_time)
        self.I_DS_vs_time.deleteLater()
        self.I_GS_vs_time.deleteLater()
        self.I_GS_vs_time = None
        self.I_DS_vs_time = None
        self.I_GS_vs_time = pg.PlotWidget()
        self.I_DS_vs_time = pg.PlotWidget()
        self.plot_layout.addWidget(self.I_GS_vs_time)
        self.plot_layout.addWidget(self.I_DS_vs_time)
        self.I_GS_vs_time.setBackground('w')
        self.I_DS_vs_time.setBackground('w')
        self.I_DS_vs_time.setLabel('bottom', 'time [s]', color='black')
        self.I_DS_vs_time.setLabel('left', 'I_DS [A]', color='black')
        self.I_GS_vs_time.setLabel('left', 'I_GS [A]', color='black')

    def clear_plots(self):
        self.I_GS_vs_time.clear()
        self.I_DS_vs_time.clear()
        
    def create_new_plot_lines(self):
        pen_I = pg.mkPen(color='r')
        self.I_GS_vs_time_line = self.I_GS_vs_time.plot(self.data['time'], self.data['I_GS'], pen=pen_I )
        self.I_DS_vs_time_line = self.I_DS_vs_time.plot(self.data['time'], self.data['I_DS'], pen=pen_I )
    
    def update_plots(self):
        self.I_GS_vs_time_line.setData(self.data['time'], self.data['I_GS'] )
        self.I_DS_vs_time_line.setData(self.data['time'], self.data['I_DS'] )
    
    def shutdown(self):
        self.datafile.close()
        self.smu.close()
        
if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('GPIB0::27::INSTR')
    
    experiment_app = QtWidgets.QApplication([])
    
    experiment = current_vs_time(smu, datafile)
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    experiment.show()
    smu_ui.show()
    datafile_viewer.show()
    
    experiment_app.exec()