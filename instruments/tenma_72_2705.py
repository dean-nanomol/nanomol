# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 14:33:02 2024

@author: deankos
"""

import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

class tenma_72_2705(serial_instrument):
    
    def __init__(self, port):
        settings = {'baudrate': 9600,
                    'timeout': 1 }
        super().__init__(port=port, port_settings=settings)
        
    @property
    def current(self):
        """ returns measured output current in A """
        return float(self.query('IOUT1?'))
    @current.setter
    def current(self, current):
        """ set output current in A """
        self.write('ISET1:{:.3}'.format(float(current)) )
    
    def current_setting(self):
        """ returns set output current """
        return float(self.query('ISET1?'))
    
    @property
    def voltage(self):
        """ returns measured output voltage in V """
        return float(self.query('VOUT1?'))
    @voltage.setter
    def voltage(self, voltage):
        """ set output voltage in V """
        self.write('VSET1:{:.2}'.format(float(voltage)) )
    
    def voltage_setting(self):
        """ returns set output voltage """
        return float(self.query('VSET1?'))
    
    @property
    def output(self):
        """ returns 0: OFF ; 1:ON """
        status = self.status()
        return status[1]
    @output.setter
    def output(self, output):
        """ 0: OFF ; 1:ON """
        self.write('OUT{}'.format(int(output)) )
    
    @property
    def output_mode(self):
        """ 'cc': constant current ; 'cv': constant voltage """
        status = self.status()
        if status[7] == 0:
            return 'cc'
        elif status[7] == 1:
            return 'cv'
        
    def status(self):
        """
        Returns
        status : str
            string of 8 bits. bit 0 is last.
            bit 0: 0: constant current; 1:constant voltage
            bit 6: 0: output OFF; 1: output ON
            bits 1,2,3,4,5,7: not used
            e.g. '00010010': OFF, constant current; '01010011': ON, constant voltage
        """
        status = self.query('STATUS?').encode()
        status_int = ord(status)
        status_bin = format(status_int, 'b').zfill(8)
        status = status_bin
        return status
    
class tenma_72_2705_ui(interactive_ui):
    """
    Keithley SMU used to drive an LED. 
    """
    
    def __init__(self, power_supply):
        super().__init__()
        self.power_supply = power_supply
        ui_file_path = os.path.join(os.path.dirname(__file__), 'tenma_72_2705.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.current_doubleSpinBox.valueChanged.connect(self.set_current)
        self.voltage_doubleSpinBox.valueChanged.connect(self.set_voltage)
        self.measure_current_pushButton.clicked.connect(self.read_current)
        self.measure_voltage_pushButton.clicked.connect(self.read_voltage)
        self.on_pushButton.toggled.connect(self.ON)
        self.off_pushButton.clicked.connect(self.OFF)
        self.OFF()
    
    def set_current(self):
        self.power_supply.current = self.current
        
    def set_voltage(self):
        self.power_supply.voltage = self.voltage
    
    def read_current(self):
        current = self.power_supply.current
        self.measured_current_lineEdit.setText('{:.3f}'.format(current))
    
    def read_voltage(self):
        voltage = self.power_supply.voltage
        self.measured_voltage_lineEdit.setText('{:.2f}'.format(voltage))
        
    def ON(self, checked):
        # checked state is passed by pushButton. If toggled to unchecked state, turn OFF
        if checked:
            self.power_supply.output = 1
        else:
            self.OFF()
            
    def OFF(self):
        self.power_supply.output = 0
        if self.on_pushButton.isChecked():
            self.on_pushButton.setChecked(False)

if __name__ == '__main__' :
    
    myTenma = tenma_72_2705('COM3')
    
    ui_app = QtWidgets.QApplication([])
    ui = tenma_72_2705_ui(myTenma)
    ui.show()
    ui_app.exec()