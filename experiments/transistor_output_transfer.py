# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 12:02:09 2023

@author: deankos
"""

import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A
from nanomol.utils.experiment_ui import experiment_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class transistor_output_transfer(experiment_ui):
    
    def __init__(self, smu_address):
        super().__init__()
        self.smu = keithley_2600A(smu_address)
        # set gate-source and drain-source channels
        self.GS = 'a'
        self.DS = 'b'
        uic.loadUi(r'transistor_output_transfer.ui', self)
        self.connect_widgets_by_name()
        
if __name__ == '__main__' :
    
    #datafile = hdf5_datafile(mode='x')
    
    experiment_app = QtWidgets.QApplication([])
    #experiment = transistor_output_transfer(datafile, 'GPIB0::27::INSTR')
    experiment = transistor_output_transfer('GPIB0::27::INSTR')
    experiment.show()
    experiment_app.exec()
    