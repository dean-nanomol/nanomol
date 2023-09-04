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
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class current_vs_time(interactive_ui):
    
    def __init__(self, datafile, smu):
        super().__init__()
        self.datafile = datafile
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'current_vs_time.ui')
        uic.loadUi(ui_file_path, self)
        self.channel_GS_comboBox.currentTextChanged.connect(self.set_smu_channels)
        self.channel_DS_comboBox.currentTextChanged.connect(self.set_smu_channels)
        self.start_pushbutton.clicked.connect(self.start_measurement)
        self.stop_pushbutton.clicked.connect(self.stop_measurement)
        self.reset_plot_widgets_pushbutton.clicked.connect(self.setup_plot_widgets)
        self.shutdown_pushbutton.clicked.connect(self.shutdown)
        self.set_smu_channels()
        self.setup_plot_widgets()
        
    def start_measurement(self):
        if not self.measurement_is_running:  # do nothing if measurement is already running
            self.measurement_is_running = True
            measurement_thread = threading.Thread(target=self.run_measurement)
            measurement_thread.start()
            
    def stop_measurement(self):
        if self.measurement_is_running:
            self.measurement_is_running = False
            
    def run_measurement(self):
        self.configure_measurement()
        t0 = time.time()
        t = t0
        
        while self.measurement_is_running and t <= self.t_limit:
            
            t = time.time() - t0
        self.smu.set_output(self.ch_GS, 0)
        
    def configure_measurement(self):
        self.smu.set_source_function('a', 1)
        self.smu.set_source_function('b', 1)
    
    def set_smu_channels(self):
        self.ch_GS = self.channel_GS_comboBox.currentText()
        self.ch_DS = self.channel_DS_comboBox.currentText()
    
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
        self.I_DS_vs_time.setLabel('bottom', 'time [s]')
        self.I_GS_vs_time.setLabel('left', 'I_GS [A]')
        self.I_DS_vs_time.setLabel('left', 'I_DS [A]')
    
    def shutdown(self):
        self.datafile.close()
        self.smu.close()
        
if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('GPIB0::27::INSTR')
    
    experiment_app = QtWidgets.QApplication([])
    
    experiment = current_vs_time(datafile, smu)
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    experiment.show()
    smu_ui.show()
    datafile_viewer.show()
    
    experiment_app.exec()