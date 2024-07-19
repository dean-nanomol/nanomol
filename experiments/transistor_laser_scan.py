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
from nanomol.instruments.newport_CONEX_MFA_CC import newport_CONEX_MFA_CC, newport_CONEX_MFA_CC_XY_ui
from nanomol.instruments.optosigma_GSC_01 import optosigma_GSC_01, optosigma_GSC_01_ui
from nanomol.instruments.thorlabs_MCLS1 import thorlabs_MCLS1, thorlabs_MCLS1_ui
from nanomol.instruments.arduino_shutter_controller import arduino_shutter_controller, arduino_shutter_controller_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer
from nanomol.experiments.transistor_transfer import transistor_transfer

class transistor_laser_scan(interactive_ui):
    
    def __init__(self, stage_X, stage_Y, MCLS1, shutter_controller, datafile, transistor_transfer ):
        super().__init__()
        self.stage_X = stage_X
        self.stage_Y = stage_Y
        self.MCLS1 = MCLS1
        self.shutter_controller = shutter_controller
        self.shutter_pin_635nm = 2
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
        self.save_scan_attrs()
        self.MCLS1.system_enable = 1
        self.MCLS1.channel = 2
        self.MCLS1.enable = 1
        time.sleep(5)
        self.point_counter = 1
        self.t0 = time.time()
        for self.position_Y in self.grid_Y_points:
            self.stage_Y.move_absolute(self.position_Y)
            self.wait_for_motion_completed(self.stage_Y)
            for self.position_X in self.grid_X_points:
                self.stage_X.move_absolute(self.position_X)
                self.wait_for_motion_completed(self.stage_X)
                self.measure_grid_point()
                self.point_counter += 1
                if not self.grid_scan_is_running:
                    break
            if not self.grid_scan_is_running:
                break
        self.grid_scan_is_running = False
        self.datafile.flush()
        self.MCLS1.enable = 0
        self.MCLS1.system_enable = 0
        
    def configure_XY_grid(self):
        # Configure grid with steps and start/stop points from ui.
        # -(a // -b) emulates ceiling function. If endpoint falls beteween grid points, extend grid to contain it.
        # round() used to eliminate rounding errors when subtracting start/stop coordinates.
        num_X_steps = -(abs(round(self.grid_X_stop - self.grid_X_start, ndigits=3)) // -self.grid_X_step)
        self.num_X_points = int(num_X_steps) +1
        num_Y_steps = -(abs(round(self.grid_Y_stop - self.grid_Y_start, ndigits=3)) // -self.grid_Y_step)
        self.num_Y_points = int(num_Y_steps) +1
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
        self.num_grid_points = self.num_X_points * self.num_Y_points
        self.grid_num_points_lineEdit.setText('{} x {} = {}'.format(self.num_X_points, self.num_Y_points, self.num_grid_points))
    
    def measure_grid_point(self):
        point_label = 'point_X{:.3f}_Y{:.3f}'.format(self.position_X, self.position_Y)
        self.active_point_group = self.active_scan_group.create_group(point_label)
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
        self.active_point_group.attrs.create('X', self.stage_X.position())
        self.active_point_group.attrs.create('Y', self.stage_Y.position())
        self.update_progress()
        time.sleep(self.shutter_cooling_delay)
        
    def save_scan_attrs(self):
        scan_label = self.datafile.get_unique_group_name(self.datafile, basename=self.description, max_N=99)
        self.active_scan_group = self.datafile.create_group(scan_label)
        scan_attrs = {}
        scan_attrs['description'] = self.description
        scan_attrs['timestamp'] = self.datafile.timestamp()
        scan_attrs['grid_X_points'] = self.grid_X_points
        scan_attrs['grid_Y_points'] = self.grid_Y_points
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
        
    def update_progress(self):
        elapsed_s = int( time.time() - self.t0 )
        elapsed_min = elapsed_s // 60
        elapsed_h, elapsed_min = divmod(elapsed_min, 60)
        time_per_point = elapsed_s / self.point_counter
        remaining_s = int( (self.num_grid_points - self.point_counter) * time_per_point )
        remaining_min = remaining_s // 60
        remaining_h, remaining_min = divmod(remaining_min, 60)
        self.progress_lineEdit.setText('point {}/{}, elapsed: {}h {}m, remaining: {}h {}m'.format(
                                                            self.point_counter, self.num_grid_points,
                                                            elapsed_h, elapsed_min,
                                                            remaining_h, remaining_min) )
    
    def wait_for_motion_completed(self, stage):
        while stage.is_moving():
            time.sleep(0.01)
    
    def shutdown(self):
        if not self.grid_scan_is_running:
            self.datafile.close()
            

if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('USB0::0x05E6::0x2604::4101847::INSTR')
    stage_X = newport_CONEX_MFA_CC('COM5')
    stage_Y = newport_CONEX_MFA_CC('COM6')
    stage_Z = optosigma_GSC_01('COM1')
    MCLS1 = thorlabs_MCLS1('COM4')
    shutter_controller = arduino_shutter_controller('COM7')
    
    ui_app = QtWidgets.QApplication([])
    
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    stage_XY_ui = newport_CONEX_MFA_CC_XY_ui(stage_X, stage_Y)
    stage_Z_ui = optosigma_GSC_01_ui(stage_Z)
    MCLS1_ui = thorlabs_MCLS1_ui(MCLS1)
    shutter_controller_ui = arduino_shutter_controller_ui(shutter_controller)
    transistor_transfer_ui = transistor_transfer(smu, datafile)
    scan_ui = transistor_laser_scan(stage_X, stage_Y, MCLS1, shutter_controller, datafile, transistor_transfer_ui)
    
    datafile_viewer.show()
    smu_ui.show()
    stage_XY_ui.show()
    stage_Z_ui.show()
    MCLS1_ui.show()
    shutter_controller_ui.show()
    transistor_transfer_ui.show()
    scan_ui.show()
    
    ui_app.exec()