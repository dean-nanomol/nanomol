# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:39:43 2023

@author: deankos
"""

import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A
from nanomol.utils.interactive_ui import interactive_ui

class keithley_2600_LED_driver_ui(interactive_ui):
    """ Keithley SMU used to drive an LED """
    
    def __init__(self, smu):
        super().__init__()
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'keithley_2600_LED_driver.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.I_limit_doubleSpinBox.valueChanged.connect(self.set_I_limit)
        self.V_limit_doubleSpinBox.valueChanged.connect(self.set_V_limit)
        self.I_constant_current_doubleSpinBox.valueChanged.connect(self.set_I_constant_current)
        self.V_constant_voltage_doubleSpinBox.valueChanged.connect(self.set_V_constant_voltage)
        self.constant_current_radioButton.toggled.connect(self.set_smu_mode)
        self.constant_voltage_radioButton.toggled.connect(self.set_smu_mode)
        self.set_smu_mode()
        
    def set_I_limit(self, I_limit):
        self.smu.set_source_limit(self, 'a', 'i', self.I_limit)
        
    def set_V_limit(self, V_limit):
        self.smu.set_source_limit(self, 'a', 'v', self.V_limit)
        
    def set_I_constant_current(self, I_constant_current):
        self.smu.set_source_level('a', 'i', I_constant_current)
        
    def set_V_constant_voltage(self, V_constant_voltage):
        self.smu.set_source_level('a', 'v', V_constant_voltage)
        
    def set_smu_mode(self):
        if self.constant_current_radioButton.isChecked():
            self.mode = 'constant_current'
        elif self.constant_voltage_radioButton.isChecked():
            self.mode = 'constant_voltage'
    

if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::26::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600_LED_driver_ui(myKeithley)
    ui.show()
    ui_app.exec()