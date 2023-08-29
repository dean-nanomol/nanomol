# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 12:02:09 2023

@author: deankos
"""

import numpy as np
import threading
import time
import os
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class transistor_output_transfer(interactive_ui):
    
    def __init__(self, datafile, smu_address):
        super().__init__()
        self.datafile = datafile
        self.smu = keithley_2600A(smu_address)
        ui_file_path = os.path.join(os.path.dirname(__file__), 'transistor_output_transfer.ui')
        uic.loadUi(ui_file_path, self)
        # set gate-source and drain-source channels
        self.smu_channels = {'GS': 'a', 'DS': 'b'}
        self.connect_widgets_by_name()
        self.output_mode_radiobutton.clicked.connect(self.set_measurement_mode)
        self.transfer_mode_radiobutton.clicked.connect(self.set_measurement_mode)
        self.start_pushbutton.clicked.connect(self.start_measurement)
        self.set_measurement_mode()
        self.measurement_is_running = False
    
    def start_measurement(self):
        if not self.measurement_is_running:  # do nothing if measurement is already running
            self.measurement_is_running = True
            measurement_thread = threading.Thread(target=self.run_measurement)
            measurement_thread.start()
            
    def run_measurement(self):
        self.configure_measurement()
        # set channels to start from first point when output is turned on
        self.V1_active = self.V1[0]
        self.smu.set_source_level(self.V1_ch, 'v', self.V1_active)
        self.smu.set_output(self.V1_ch, 1)
        for self.V1_active in self.V1:
            active_curve_name = self.datafile.get_unique_group_name(self.active_device_group, basename='curve')
            self.active_curve_group = self.active_device_group.create_group(active_curve_name)
            self.initialise_datasets()
            self.smu.set_source_level(self.V1_ch, 'v', self.V1_active)
            self.V2_active = self.V2[0]
            self.smu.set_source_level(self.V2_ch, 'v', self.V2_active)
            self.smu.set_output(self.V2_ch, 1)
            t0 = time.time()
            for self.V2_active in self.V2:
                self.smu.set_source_level(self.V2_ch, 'v', self.V2_active)
                measured_I1, measured_V1 = self.smu.measure(self.V1_ch, 'iv')
                measured_I2, measured_V2 = self.smu.measure(self.V2_ch, 'iv')
                self.data['time'].append(time.time()-t0)
                self.data['measured_V1'].append(measured_V1)
                self.data['measured_I1'].append(measured_I1)
                self.data['measured_V2'].append(measured_V2)
                self.data['measured_I2'].append(measured_I2)
            self.smu.set_output(self.V2_ch, 0)
            self.save_data()
        self.smu.set_output(self.V1_ch, 0)
        self.measurement_is_running = False
    
    
    def configure_measurement(self):
        active_device_name = self.datafile.get_unique_group_name(self.datafile, basename='device', max_N=1000)
        self.active_device_group =  self.datafile.create_group(active_device_name)
        if self.measurement_mode == 'output':
            self.V1_ch, self.V2_ch = self.smu_channels['GS'], self.smu_channels['DS']
            self.V1_label, self.V2_label = 'GS', 'DS'
            self.V1 = np.arange(self.V_GS_min_output, self.V_GS_max_output + self.V_GS_step_output, self.V_GS_step_output)
            self.V2 = np.arange(self.V_DS_min_output, self.V_DS_max_output + self.V_DS_step_output, self.V_DS_step_output)
        elif self.measurement_mode == 'transfer':
            self.V1_ch, self.V2_ch = self.smu_channels['DS'], self.smu_channels['GS']
            self.V1_label, self.V2_label = 'DS', 'GS'
            self.V1 = np.arange(self.V_DS_min_transfer, self.DS_max_transfer + self.V_DS_step_transfer, self.V_DS_step_transfer)
            self.V2 = np.arange(self.V_GS_min_transfer, self.GS_max_transfer + self.V_GS_step_transfer, self.V_GS_step_transfer)
    
    def initialise_datasets(self):
        self.data = {'time':[],
                     'measured_V1':[],
                     'measured_I1':[],
                     'measured_V2':[],
                     'measured_I2':[]  }
    
    def set_measurement_mode(self):
        if self.output_mode_radiobutton.isChecked():
            self.measurement_mode = 'output'
        elif self.transfer_mode_radiobutton.isChecked():
            self.measurement_mode = 'transfer'
    
    def save_data(self):
        for dataset_name, data in self.data.items():
            dataset_name = dataset_name.replace('1', '_{}'.format(self.V1_label) )
            dataset_name = dataset_name.replace('2', '_{}'.format(self.V2_label) )
            self.active_curve_group.create_dataset(dataset_name, data=np.array(data) )
    
        
if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    
    experiment_app = QtWidgets.QApplication([])
    
    experiment = transistor_output_transfer(datafile, 'GPIB0::27::INSTR')
    datafile_viewer = hdf5_viewer(datafile)
    # TO DO: fix absolute path for ui in hdf5_viewer
    experiment.show()
    datafile_viewer.show()
    
    experiment_app.exec()
    