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
from nanomol.experiments.transistor_output_transfer import transistor_output_transfer
from nanomol.experiments.current_vs_time import current_vs_time

class bias_stress(interactive_ui):
    
    def __init__(self, datafile, transistor_output_transfer, current_vs_time):
        super().__init__()
        self.transistor_output_transfer = transistor_output_transfer
        self.current_vs_time = current_vs_time
        ui_file_path = os.path.join(os.path.dirname(__file__), 'bias_stress.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.start_bias_stress_pushButton.clicked.connect(self.start_bias_stress)
        self.stop_bias_stress_pushButton.clicked.connect(self.stop_bias_stress)
        
    def start_bias_stress(self):
        if not self.bias_stress_is_running:  # do nothing if measurement is already running
            self.bias_stress_is_running = True
            self.bias_stress_thread = threading.Thread(target=self.run_bias_stress)
            self.bias_stress_thread.start()
    
    def stop_bias_stress(self):
        self.bias_stress_is_running = False
    
    def run_bias_stress(self):
        pass

if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('GPIB0::27::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)

    output_transfer_ui = transistor_output_transfer(datafile, smu)
    current_vs_time_ui = current_vs_time(datafile, smu)
    bias_stress_ui = bias_stress(datafile, output_transfer_ui, current_vs_time_ui)
    
    datafile_viewer.show()
    smu_ui.show()
    output_transfer_ui.show()
    current_vs_time_ui.show()
    bias_stress_ui.show()
    
    ui_app.exec()


#TODO implement stop button in bias stress ui so it also stops the transfer measurement thread
#TODO implement ETA
#TODO implement option to not show real time data in current_vs_time