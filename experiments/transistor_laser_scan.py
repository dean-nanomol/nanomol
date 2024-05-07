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
        
    def start_grid_scan(self):
        if not self.grid_scan_is_running:  # do nothing if measurement is already running
            self.grid_scan_is_running = True
            grid_scan_thread = threading.Thread(target=self.run_grid_scan)
            grid_scan_thread.start()
    
    def run_grid_scan(self):
        self.grid_X_points = np.arange(self.grid_X_start, self.grid_X_stop + self.grid_X_step, self.grid_X_step)
        self.grid_Y_points = np.arange(self.grid_Y_start, self.grid_Y_stop + self.grid_Y_step, self.grid_Y_step)
        for position_X in self.grid_X_points:
            self.stage_X.move_absolute(position_X)
            self.wait_for_motion_completed(self.stage_X)
            for position_Y in self.grid_Y_points:
                self.stage_Y.move_absolute(position_Y)
                self.wait_for_motion_completed(self.stage_Y)
        
        
    def wait_for_motion_completed(self, stage):
        while stage.is_moving():
            time.sleep(0.01)
        self.update_position(stage)