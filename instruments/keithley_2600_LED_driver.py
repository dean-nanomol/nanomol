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
    """
    Keithley SMU used to drive an LED. 
    """
    
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
        self.on_pushButton.toggled.connect(self.ON)
        self.off_pushButton.clicked.connect(self.OFF)
        self.toggle_pushButton.toggled.connect(self.toggle)
        self.set_smu_mode()
        self.I_source_range_comboBox.currentTextChanged.connect(self.set_I_source_range)
        self.V_source_range_comboBox.currentTextChanged.connect(self.set_V_source_range)
        self.set_I_source_range()
        self.set_V_source_range()
        self.set_I_limit()
        self.set_V_limit()
        self.OFF()
        
    def set_I_limit(self):
        self.smu.set_source_limit('a', 'i', self.I_limit/1e+3)
        
    def set_V_limit(self):
        self.smu.set_source_limit('a', 'v', self.V_limit)
        
    def set_I_source_range(self):
        self.smu.set_source_range('a', 'i', self.I_source_range_comboBox.currentText() )
        self.smu.set_measure_range('a', 'i', self.I_source_range_comboBox.currentText() )
        
    def set_V_source_range(self):
        self.smu.set_source_range('a', 'v', self.V_source_range_comboBox.currentText() )
        self.smu.set_measure_range('a', 'v', self.V_source_range_comboBox.currentText() )
        
    def set_I_constant_current(self, I_constant_current):
        self.smu.set_source_level('a', 'i', I_constant_current/1e+3)
        
    def set_V_constant_voltage(self, V_constant_voltage):
        self.smu.set_source_level('a', 'v', V_constant_voltage)
    
    def set_smu_mode(self):
        if self.constant_current_radioButton.isChecked():
            self.smu.set_source_function('a', 0)
            self.mode = 'constant_current'
        elif self.constant_voltage_radioButton.isChecked():
            self.smu.set_source_function('a', 1)
            self.mode = 'constant_voltage'
    
    def ON(self, checked):
        # checked state is passed by pushButton. If toggled to unchecked state, turn OFF
        if checked:
            self.LED_is_running = True
            self.smu.set_output('a', 1)
            measure_thread = threading.Thread(target=self.measure_thread)
            measure_thread.start()
        else:
            self.OFF()
        
    def OFF(self):
        self.smu.set_output('a', 0)
        self.LED_is_running = False
        self.on_pushButton.setChecked(False)
        self.toggle_pushButton.setChecked(False)
        self.i = 0
        self.v = 0
    
    def measure_thread(self, measure_interval=0.1):
        """
        Measure actual I and V output. Run as thread with values updated every measure_interval seconds.
        self.i, self.v contain the latest measured values.
        """
        while self.LED_is_running:
            self.i, self.v = self.smu.measure('a', 'iv')
            self.measured_I_lineEdit.setText('{:.3f}'.format(self.i*1e+3))
            self.measured_V_lineEdit.setText('{:.4f}'.format(self.v))
            time.sleep(measure_interval)
    
    def toggle(self, checked):
        if checked:
            self.LED_is_running = True
            measure_thread = threading.Thread(target=self.measure_thread)
            toggle_thread = threading.Thread(target=self.toggle_thread)
            measure_thread.start()
            toggle_thread.start()
        else:
            self.OFF()
        
    def toggle_thread(self):
        while self.toggle_pushButton.isChecked():
            self.smu.set_output('a', 1)
            time.sleep(self.toggle_ON_time)
            self.smu.set_output('a', 0)
            time.sleep(self.toggle_OFF_time)
            

if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::26::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600_LED_driver_ui(myKeithley)
    ui.show()
    ui_app.exec()