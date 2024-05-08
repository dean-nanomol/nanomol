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
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class transistor_laser_scan(interactive_ui):
    
    def __init__(self, stage_X, stage_Y):
        super().__init__()
        self.stage_X = stage_X
        self.stage_Y = stage_Y
        ui_file_path = os.path.join(os.path.dirname(__file__), 'transistor_laser_scan.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.current_position_as_start_pushButton.clicked.connect(self.current_position_as_start)
        self.current_position_as_stop_pushButton.clicked.connect(self.current_position_as_stop)
        
    def start_grid_scan(self):
        if not self.grid_scan_is_running:  # do nothing if measurement is already running
            self.grid_scan_is_running = True
            grid_scan_thread = threading.Thread(target=self.run_grid_scan)
            grid_scan_thread.start()
    
    def stop_grid_scan(self):
        self.grid_scan_is_running = False
    
    def run_grid_scan(self):
        self.grid_X_points = np.arange(self.grid_X_start, self.grid_X_stop + self.grid_X_step, self.grid_X_step)
        self.grid_Y_points = np.arange(self.grid_Y_start, self.grid_Y_stop + self.grid_Y_step, self.grid_Y_step)
        for position_X in self.grid_X_points:
            self.stage_X.move_absolute(position_X)
            self.wait_for_motion_completed(self.stage_X)
            for position_Y in self.grid_Y_points:
                self.stage_Y.move_absolute(position_Y)
                self.wait_for_motion_completed(self.stage_Y)
                time.sleep(0.2)
                print('moved, X:{:.4f}, Y:{:.4f}'.format(self.stage_X.position(), stage_Y.position()))
                if not self.grid_scan_is_running:
                    break
            if not self.grid_scan_is_running:
                break
        self.grid_scan_is_running = False
    
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
        
    def wait_for_motion_completed(self, stage):
        while stage.is_moving():
            time.sleep(0.01)

if __name__ == '__main__' :
    
    smu = keithley_2600A('USB0::0x05E6::0x2604::4101847::INSTR')
    stage_X = newport_CONEX_MFA_CC('COM5')
    stage_Y = newport_CONEX_MFA_CC('COM6')
    stage_Z = optosigma_GSC_01('COM1')
    
    ui_app = QtWidgets.QApplication([])
    
    smu_ui = keithley_2600A_ui(smu)
    stage_XY_ui = newport_CONEX_MFA_CC_XY_ui(stage_X, stage_Y)
    stage_Z_ui = optosigma_GSC_01_ui(stage_Z)
    scan_ui = transistor_laser_scan(stage_X, stage_Y)
    
    smu_ui.show()
    stage_XY_ui.show()
    stage_Z_ui.show()
    scan_ui.show()
    
    ui_app.exec()