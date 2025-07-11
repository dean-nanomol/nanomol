# -*- coding: utf-8 -*-
"""
Created on Tue May  7 11:48:04 2024

@author: deankos
"""

import numpy as np
import threading
import time
import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.instruments.arduino_shutter_controller import arduino_shutter_controller, arduino_shutter_controller_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer
from nanomol.experiments.transistor_transfer import transistor_transfer

class transistor_transfer_laser_ON_OFF(interactive_ui):
    
    def __init__(self, shutter_controller, datafile, transistor_transfer ):
        super().__init__()
        self.shutter_controller = shutter_controller
        self.shutter_pin_635nm = 2
        self.datafile = datafile
        self.transfer = transistor_transfer
        ui_file_path = os.path.join(os.path.dirname(__file__), 'transistor_transfer_laser_ON_OFF.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.start_pushButton.clicked.connect(self.start_grid_scan)
        self.stop_pushButton.clicked.connect(self.stop_grid_scan)
        self.measurement_is_running = False
        
    def start_measurement(self):
        if not self.measurement_is_running:  # do nothing if measurement is already running
            self.measurement_is_running = True
            self.measurement_thread = threading.Thread(target=self.run_measurement)
            self.measurement_thread.start()
    
    def stop_measurement(self):
        self.measurement_is_running = False
    
    def run_measurement(self):
        self.configure_XY_grid()
        self.save_scan_attrs()
        self.point_counter = 1
        self.t0 = time.time()
        for self.position_primary in self.primary_axis_points:
            self.primary_axis_stage.move_absolute(self.position_primary)
            self.wait_for_motion_completed(self.primary_axis_stage)
            for self.position_secondary in self.secondary_axis_points:
                self.secondary_axis_stage.move_absolute(self.position_secondary)
                self.wait_for_motion_completed(self.secondary_axis_stage)
                self.measure_grid_point()
                self.point_counter += 1
                if not self.grid_scan_is_running:
                    break
                if self.delay_grid != 0:
                    time.sleep(self.delay_grid)
            if not self.grid_scan_is_running:
                break
        self.grid_scan_is_running = False
        self.datafile.flush()
        if not self.parameter_sweep_is_running:
            self.MCLS1.enable = 0
            self.MCLS1.system_enable = 0
    
    def stop_parameter_sweep(self):
        self.parameter_sweep_is_running = False
    
    def configure_parameter_sweep(self):
        if self.param_sweep_laser_current_radioButton.isChecked():
            param_sweep_start = self.param_sweep_laser_current_start
            param_sweep_stop = self.param_sweep_laser_current_stop
            param_sweep_N_points = self.param_sweep_laser_current_N_points
            param_sweep_values = np.linspace(param_sweep_start, param_sweep_stop, num=param_sweep_N_points)
            self.param_sweep_values = np.round(param_sweep_values, decimals=2)
        elif self.param_sweep_delay_grid_radioButton.isChecked():
            # parse comma separated string into delay values
            parsed_values = self.param_sweep_delay_grid.split(',')
            parsed_values = [float(value.strip()) for value in parsed_values]
            self.param_sweep_values = np.round(parsed_values, decimals=1)
    
    
    def measure_grid_point(self):
        point_label = 'point_{}{:.3f}_{}{:.3f}'.format(self.primary_axis, self.position_primary,
                                                       self.secondary_axis, self.position_secondary)
        self.active_point_group = self.active_scan_group.create_group(point_label)
        self.active_point_group.attrs.create('{}_nominal'.format(self.primary_axis), self.position_primary)
        self.active_point_group.attrs.create('{}_nominal'.format(self.secondary_axis), self.position_secondary)
        self.shutter_controller.close_shutter(self.shutter_pin_635nm)
        self.laserOFF_group = self.active_point_group.create_group('laser_OFF')
        self.laserOFF_group.attrs.create('laser_ON', 0)
        self.laserOFF_group.attrs.create('shutter_state', self.shutter_controller.status())
        self.transfer.start_measurement(datafile=self.datafile, path=self.laserOFF_group.name)
        self.transfer.measurement_thread.join()
        self.shutter_controller.open_shutter(self.shutter_pin_635nm)
        self.laserON_group = self.active_point_group.create_group('laser_ON')
        self.laserON_group.attrs.create('laser_ON', 1)
        self.laserON_group.attrs.create('shutter_state', self.shutter_controller.status())
        self.transfer.start_measurement(datafile=self.datafile, path=self.laserON_group.name)
        self.transfer.measurement_thread.join()
        self.shutter_controller.close_shutter(self.shutter_pin_635nm)
        self.active_point_group.attrs.create('X_measured', self.stage_X.position())
        self.active_point_group.attrs.create('Y_measured', self.stage_Y.position())
        self.update_progress()
        
    def save_scan_attrs(self):
        scan_label = self.datafile.get_unique_group_name(self.datafile, basename=self.description, max_N=99)
        self.active_scan_group = self.datafile.create_group(scan_label)
        scan_attrs = {}
        scan_attrs['description'] = self.description
        scan_attrs['timestamp'] = self.datafile.timestamp()
        scan_attrs['grid_X_points'] = self.grid_X_points
        scan_attrs['grid_Y_points'] = self.grid_Y_points
        scan_attrs['delay_grid'] = self.delay_grid
        scan_attrs['primary_axis'] = self.primary_axis
        scan_attrs['secondary_axis'] = self.secondary_axis
        for attr, value in scan_attrs.items():
            self.active_scan_group.attrs.create(attr, value)
        self.save_laser_attrs(self.active_scan_group)
    
    def save_laser_attrs(self, data_group):
        laser_attrs = {}
        laser_attrs['enabled_channels'] = self.MCLS1.status
        laser_attrs['active_channel'] = self.MCLS1.channel
        laser_attrs['power'] = self.MCLS1.power
        laser_attrs['current'] = self.MCLS1.current
        laser_attrs['temperature'] = self.MCLS1.temperature
        for attr, value in laser_attrs.items():
            data_group.attrs.create(attr, value)
    
    def shutdown(self):
        if not self.grid_scan_is_running:
            self.datafile.close()
            

if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('USB0::0x05E6::0x2604::4101847::INSTR')
    shutter_controller = arduino_shutter_controller('COM7')
    
    ui_app = QtWidgets.QApplication([])
    
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    shutter_controller_ui = arduino_shutter_controller_ui(shutter_controller)
    transistor_transfer_ui = transistor_transfer(smu, datafile)
    transistor_transfer_laser_ON_OFF_ui = transistor_transfer_laser_ON_OFF(shutter_controller, datafile, transistor_transfer_ui)
    
    datafile_viewer.show()
    smu_ui.show()
    shutter_controller_ui.show()
    transistor_transfer_ui.show()
    transistor_transfer_laser_ON_OFF_ui.show()
    
    ui_app.exec()