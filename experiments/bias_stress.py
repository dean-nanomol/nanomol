# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 18:00:20 2026

@author: deankos
"""

import numpy as np
import threading
import time
import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer
from nanomol.experiments.transistor_transfer import transistor_transfer
from nanomol.experiments.current_vs_time import current_vs_time

class bias_stress(interactive_ui):
    
    def __init__(self, datafile, transistor_transfer, current_vs_time):
        super().__init__()
        self.datafile = datafile
        self.transistor_transfer = transistor_transfer
        self.current_vs_time = current_vs_time
        ui_file_path = os.path.join(os.path.dirname(__file__), 'bias_stress.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.start_bias_stress_pushButton.clicked.connect(self.start_bias_stress)
        self.stop_bias_stress_pushButton.clicked.connect(self.stop_bias_stress)
        self.N_measurements_spinBox.valueChanged.connect(self.estimate_duration)
        self.measurements_interval_doubleSpinBox.valueChanged.connect(self.estimate_duration)
        self.estimate_duration()
        self.bias_stress_is_running = False
        
    def start_bias_stress(self, *args, datafile=None, path=None):
        if not self.bias_stress_is_running:  # do nothing if measurement is already running
            self.bias_stress_is_running = True
            self.bias_stress_thread = threading.Thread(target=self.run_bias_stress)
            self.bias_stress_thread.start()
    
    def stop_bias_stress(self):
        self.bias_stress_is_running = False
    
    def run_bias_stress(self):
        self.save_bias_stress_attrs()
        self.current_vs_time.t_limit_doubleSpinBox.setValue(self.measurements_interval)
        self.t0 = time.time()
        for self.measurement_counter in range(self.N_measurements):
            self.transistor_transfer.start_measurement(datafile=self.datafile, path=self.active_bias_stress_group.name)
            self.transistor_transfer.measurement_thread.join()
            self.save_transfer_attrs()
            self.current_vs_time.start_measurement(datafile=self.datafile, path=self.active_bias_stress_group.name)
            self.current_vs_time.measurement_thread.join()
            self.current_vs_time.active_group.attrs.create('bias_stress_measurement_counter', self.measurement_counter)
            self.update_progress()
            if not self.bias_stress_is_running:
                break
        if self.bias_stress_is_running:
            # measure one final transfer
            self.transistor_transfer.start_measurement(datafile=self.datafile, path=self.active_bias_stress_group.name)
            self.transistor_transfer.measurement_thread.join()
            self.save_transfer_attrs()
        self.datafile.flush()
        self.bias_stress_is_running = False
        self.progress_lineEdit.setText('finished')
    
    def save_bias_stress_attrs(self):
        bias_stress_label = self.datafile.get_unique_group_name(self.datafile, basename=self.description, max_N=9999)
        self.active_bias_stress_group = self.datafile.create_group(bias_stress_label)
        bias_stress_attrs = {}
        bias_stress_attrs['description'] = self.description
        bias_stress_attrs['timestamp'] = self.datafile.timestamp()
        bias_stress_attrs['N_measurements'] = self.N_measurements
        bias_stress_attrs['measurements_interval'] = self.measurements_interval
        for attr, value in bias_stress_attrs.items():
            self.active_bias_stress_group.attrs.create(attr, value)
    
    def save_transfer_attrs(self):
        self.transistor_transfer.active_sweep_group.attrs.create('bias_stress_measurement_counter', self.measurement_counter+1)
        self.transistor_transfer.active_sweep_group.attrs.create('actual_time_from_start', round(time.time()-self.t0, 3) )
        self.transistor_transfer.active_sweep_group.attrs.create('nominal_time_from_start',
                                                                 self.measurement_counter * self.measurements_interval)
    
    def estimate_duration(self):
        estimated_minutes = round( self.measurements_interval * self.N_measurements /60)
        estimated_time_h, estimated_time_min = divmod(estimated_minutes, 60)
        self.estimated_time_lineEdit.setText('{}h {}m'.format(estimated_time_h, estimated_time_min) )
    
    def update_progress(self):
        elapsed_s = round( time.time() - self.t0 )
        elapsed_min = elapsed_s // 60
        elapsed_h, elapsed_min = divmod(elapsed_min, 60)
        time_per_bias_stress_step = elapsed_s / (self.measurement_counter +1)
        remaining_s = round( (self.N_measurements - (self.measurement_counter+1) ) * time_per_bias_stress_step )
        remaining_min = remaining_s // 60
        remaining_h, remaining_min = divmod(remaining_min, 60)
        self.progress_lineEdit.setText('measurement {}/{}, elapsed: {}h {}m, remaining: {}h {}m'.format(
                                                            self.measurement_counter+1, self.N_measurements,
                                                            elapsed_h, elapsed_min,
                                                            remaining_h, remaining_min) )

if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('GPIB0::27::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)

    transistor_transfer_ui = transistor_transfer(smu, datafile)
    current_vs_time_ui = current_vs_time(smu, datafile)
    bias_stress_ui = bias_stress(datafile, transistor_transfer_ui, current_vs_time_ui)
    
    datafile_viewer.show()
    smu_ui.show()
    transistor_transfer_ui.show()
    current_vs_time_ui.show()
    bias_stress_ui.show()
    
    ui_app.exec()


#TODO implement option to not show real time data in current_vs_time