# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:39:43 2023

@author: deankos
"""

import os
import time
import threading
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
        self.on_pushButton.pressed.connect(self.ON)
        self.on_pushButton.released.connect(self.OFF)
        self.off_pushButton.clicked.connect(self.OFF)
        self.set_smu_mode()
        self.smu.set_source_range('a', 'i', 1.5)
        self.smu.set_source_range('a', 'v', 20)
        
    def set_I_limit(self, I_limit):
        self.smu.set_source_limit(self, 'a', 'i', self.I_limit/1e+3)
        
    def set_V_limit(self, V_limit):
        self.smu.set_source_limit(self, 'a', 'v', self.V_limit)
        
    def set_I_constant_current(self, I_constant_current):
        self.smu.set_source_function(self, 'a', 0)
        self.smu.set_source_level('a', 'i', I_constant_current/1e+3)
        
    def set_V_constant_voltage(self, V_constant_voltage):
        self.smu.set_source_function(self, 'a', 1)
        self.smu.set_source_level('a', 'v', V_constant_voltage)
        
    def set_smu_mode(self):
        if self.constant_current_radioButton.isChecked():
            self.mode = 'constant_current'
        elif self.constant_voltage_radioButton.isChecked():
            self.mode = 'constant_voltage'
    
    def ON(self):
        self.smu.set_output('a', 1)
        measure_thread = threading.Thread(target=self.measure_output)
        measure_thread.start()
        
    def OFF(self):
        self.smu.set_output('a', 0)
        self.on_pushButton.setChecked(False)
        self.i = 0
        self.v = 0
    
    def measure_output(self):
        while self.smu.get_output('a'):
            self.i, self.v = self.smu.measure('a', 'iv')
            self.output_I_lineEdit.setText('{}'.format(self.i*1e+3))
            self.output_V_lineEdit.setText('{}'.format(self.v))
            time.sleep(0.1)
    

if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::26::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600_LED_driver_ui(myKeithley)
    ui.show()
    ui_app.exec()