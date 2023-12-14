# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:39:43 2023

@author: deankos
"""

import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A

class keithley_2600_LED_driver_ui():
    """ Keithley SMU used to drive an LED """
    
    def __init__(self, smu):
        super().__init__()
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'keithley_2600_LED_driver.ui')
        uic.loadUi(ui_file_path, self)

if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::26::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600_LED_driver_ui(myKeithley)
    ui.show()
    ui_app.exec()