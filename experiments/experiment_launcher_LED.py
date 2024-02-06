# -*- coding: utf-8 -*-
"""
Created on Tue Sep  5 16:48:53 2023

@author: deankos
"""

from PyQt5 import QtWidgets
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer
from nanomol.instruments.keithley_2600_LED_driver import keithley_2600_LED_driver_ui
from nanomol.experiments.transistor_output_transfer_LED import transistor_output_transfer_LED
from nanomol.experiments.current_vs_time import current_vs_time

datafile = hdf5_datafile(mode='x')
smu = keithley_2600A('GPIB0::27::INSTR')
LED_smu = keithley_2600A('GPIB0::26::INSTR')

experiment_app = QtWidgets.QApplication([])

smu_ui = keithley_2600A_ui(smu)

datafile_viewer_ui = hdf5_viewer(datafile)
current_vs_time_ui = current_vs_time(datafile, smu)
LED_ui = keithley_2600_LED_driver_ui(LED_smu)
output_transfer_LED_ui = transistor_output_transfer_LED(datafile, smu, LED_ui)

smu_ui.show()
datafile_viewer_ui.show()
LED_ui.show()
output_transfer_LED_ui.show()
current_vs_time_ui.show()


experiment_app.exec()