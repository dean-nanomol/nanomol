# -*- coding: utf-8 -*-
"""
Created on Tue May  7 11:48:04 2024

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
from nanomol.instruments.newport_CONEX_MFA_CC import newport_CONEX_MFA_CC, newport_CONEX_MFA_CC_XY_ui
from nanomol.instruments.optosigma_GSC_01 import optosigma_GSC_01, optosigma_GSC_01_ui
from nanomol.instruments.thorlabs_MCLS1 import thorlabs_MCLS1, thorlabs_MCLS1_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer
from nanomol.experiments.transistor_transfer import transistor_transfer

class transistor_laser_scan(interactive_ui):
    
    def __init__(self, stage_X, stage_Y, MCLS1, datafile, transistor_transfer ):
        super().__init__()
        self.stage_X = stage_X
        self.stage_Y = stage_Y
        self.MCLS1 = MCLS1
        self.datafile = datafile
        self.transfer = transistor_transfer
        ui_file_path = os.path.join(os.path.dirname(__file__), 'transistor_laser_scan.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.start_grid_scan_pushButton.clicked.connect(self.start_grid_scan)
        self.stop_grid_scan_pushButton.clicked.connect(self.stop_grid_scan)
        self.current_position_as_start_pushButton.clicked.connect(self.current_position_as_start)
        self.current_position_as_stop_pushButton.clicked.connect(self.current_position_as_stop)
        self.calculate_number_grid_points_pushButton.clicked.connect(self.calculate_number_grid_points)
        self.grid_scan_is_running = False
        
    def start_grid_scan(self):
        if not self.grid_scan_is_running:  # do nothing if measurement is already running
            self.grid_scan_is_running = True
            grid_scan_thread = threading.Thread(target=self.run_grid_scan)
            grid_scan_thread.start()
    
    def stop_grid_scan(self):
        self.grid_scan_is_running = False
    
    def run_grid_scan(self):
        self.configure_XY_grid()
        if self.grid_X_stop >= self.grid_X_start:
            grid_X_scan_stop = round(self.grid_X_start + (self.num_X_points-1)*self.grid_X_step, ndigits=3)
        else:
            grid_X_scan_stop = round(self.grid_X_start - (self.num_X_points-1)*self.grid_X_step, ndigits=3)
        if self.grid_Y_stop >= self.grid_Y_start: 
            grid_Y_scan_stop = round(self.grid_Y_start + (self.num_Y_points-1)*self.grid_Y_step, ndigits=3)
        else:
            grid_Y_scan_stop = round(self.grid_Y_start - (self.num_Y_points-1)*self.grid_Y_step, ndigits=3)
        self.grid_X_points = np.linspace(self.grid_X_start, grid_X_scan_stop, num = self.num_X_points)
        self.grid_Y_points = np.linspace(self.grid_Y_start, grid_Y_scan_stop, num = self.num_Y_points)
        self.save_scan_attrs()
        for self.position_Y in self.grid_Y_points:
            self.stage_Y.move_absolute(self.position_Y)
            self.wait_for_motion_completed(self.stage_Y)
            for self.position_X in self.grid_X_points:
                self.stage_X.move_absolute(self.position_X)
                self.wait_for_motion_completed(self.stage_X)
                self.measure_grid_point()
                if not self.grid_scan_is_running:
                    break
            if not self.grid_scan_is_running:
                break
        self.grid_scan_is_running = False
        
    def configure_XY_grid(self):
        # Configure grid with steps and start/stop points from ui.
        # -(a // -b) emulates ceiling function. If endpoint falls beteween grid points, extend grid to contain it.
        # round() used to eliminate rounding errors when subtracting start/stop coordinates.
        num_X_steps = -(abs(round(self.grid_X_stop - self.grid_X_start, ndigits=3)) // -self.grid_X_step)
        self.num_X_points = int(num_X_steps) +1
        num_Y_steps = -(abs(round(self.grid_Y_stop - self.grid_Y_start, ndigits=3)) // -self.grid_Y_step)
        self.num_Y_points = int(num_Y_steps) +1
    
    def current_position_as_start(self):
        position_X = round(self.stage_X.position(), ndigits=3)
        position_Y = round(self.stage_Y.position(), ndigits=3)
        self.grid_X_start_doubleSpinBox.setValue(position_X)
        self.grid_Y_start_doubleSpinBox.setValue(position_Y)
    
    def current_position_as_stop(self):
        position_X = round(self.stage_X.position(), ndigits=3)
        position_Y = round(self.stage_Y.position(), ndigits=3)
        self.grid_X_stop_doubleSpinBox.setValue(position_X)
        self.grid_Y_stop_doubleSpinBox.setValue(position_Y)
        
    def calculate_number_grid_points(self):
        self.configure_XY_grid()
        num_grid_points = self.num_X_points * self.num_Y_points
        self.grid_num_points_lineEdit.setText('{} x {} = {}'.format(self.num_X_points, self.num_Y_points, num_grid_points))
    
    def measure_grid_point(self):
        point_label = 'point_X{:.3f}_Y{:.3f}'.format(self.position_X, self.position_Y)
        self.active_point_group = self.active_scan_group.create_group(point_label)
        self.laserON_group = self.active_point_group.create_group('laser_ON')
        self.laserON_group.attrs.create('laser_ON', 1)
        self.save_laser_attrs(self.laserON_group)
        self.transfer.start_measurement(datafile=self.datafile, path=self.laserON_group.name)
        self.transfer.measurement_thread.join()
        self.laserOFF_group = self.active_point_group.create_group('laser_OFF')
        self.laserOFF_group.attrs.create('laser_ON', 0)
        self.stage_X.move_absolute(self.grid_X_start -0.05)
        self.wait_for_motion_completed(self.stage_X)
        self.transfer.start_measurement(datafile=self.datafile, path=self.laserOFF_group.name)
        self.transfer.measurement_thread.join()
        self.stage_X.move_absolute(self.position_X)
        self.wait_for_motion_completed(self.stage_X)
        
    def save_scan_attrs(self):
        scan_label = self.datafile.get_unique_group_name(self.datafile, basename='scan', max_N=99)
        self.active_scan_group = self.datafile.create_group(scan_label)
    
    def save_laser_attrs(self, data_group):
        laser_attrs = {}
        laser_attrs['enabled_channels'] = self.MCLS1.status
        laser_attrs['active_channel'] = self.MCLS1.channel
        laser_attrs['power'] = self.MCLS1.power
        laser_attrs['current'] = self.MCLS1.current
        laser_attrs['temperature'] = self.MCLS1.temperature
        for attr, value in laser_attrs.items():
            data_group.attrs.create(attr, value)
        
    
    def wait_for_motion_completed(self, stage):
        while stage.is_moving():
            time.sleep(0.01)
            

if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('USB0::0x05E6::0x2604::4101847::INSTR')
    stage_X = newport_CONEX_MFA_CC('COM5')
    stage_Y = newport_CONEX_MFA_CC('COM6')
    stage_Z = optosigma_GSC_01('COM1')
    MCLS1 = thorlabs_MCLS1('COM4')
    
    ui_app = QtWidgets.QApplication([])
    
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    stage_XY_ui = newport_CONEX_MFA_CC_XY_ui(stage_X, stage_Y)
    stage_Z_ui = optosigma_GSC_01_ui(stage_Z)
    MCLS1_ui = thorlabs_MCLS1_ui(MCLS1)
    transistor_transfer_ui = transistor_transfer(smu, datafile)
    scan_ui = transistor_laser_scan(stage_X, stage_Y, MCLS1, datafile, transistor_transfer_ui)
    
    datafile_viewer.show()
    smu_ui.show()
    stage_XY_ui.show()
    stage_Z_ui.show()
    MCLS1_ui.show()
    transistor_transfer_ui.show()
    scan_ui.show()
    
    ui_app.exec()