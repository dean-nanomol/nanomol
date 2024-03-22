# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 17:12:59 2024

@author: deankos
"""

import numpy as np
import os
import time
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

class thorlabs_MCLS1(serial_instrument):
    
    def __init__(self, port):
        settings = {'baudrate': 115200,
                    'timeout': 1 }
        termination = '\r'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
    
    def query(self, command):
        """ override serial_instrument.query method """
        # MCLS1 repeats command text and adds '>', so buffer may not be empty
        self.reset_input_buffer()
        super().query(command) # ignore first returned string, contains command repetition
        return self.read()
    
    @property
    def channel(self):
        return int(self.query('channel?'))
    @channel.setter
    def channel(self, channel):
        """ active channel """
        self.write('channel={}'.format(int(channel)))
        
    @property
    def target_temperature(self):
        return float(self.query('target?'))
    @target_temperature.setter
    def target_temperature(self, target_temperature):
        """
        target_temperature : float
            active channel target temperature in °C, 20 <= target_temperature <= 30
        """
        self.write('target={}'.format(target_temperature))
    
    @property
    def current(self):
        return float(self.query('current?'))
    @current.setter
    def current(self, current):
        """
        current : float
            active channel current in mA
        """
        self.write('current={}'.format(current))
    
    @property
    def temperature(self):
        """ active channel temperature in °C """
        return float(self.query('temp?'))
    
    @property
    def power(self):
        """ active channel laser power in mW """
        return float(self.query('power?'))
    
    @property
    def enable(self):
        return int(self.query('enable?'))
    @enable.setter
    def enable(self, enable):
        """
        enable : int
            0 or 1, disable or enable active laser channel
        """
        self.write('enable={}'.format(enable))
        
    @property
    def system_enable(self):
        return int(self.query('system?'))
    @system_enable.setter
    def system_enable(self, system_enable):
        """
        system_enable : int
            0 or 1, disable or enable laser system
        """
        self.write('system={}'.format(system_enable))
        
    @property
    def specs(self):
        """ active laser channel specifications """
        return self.query('specs?')
    
    @property
    def status(self):
        """ status of all 'enable' buttons """
        return self.query('statword?')


class thorlabs_MCLS1_ui(interactive_ui):
    """
    User interface for Thorlabs MCLS1 4-channel fibre-coupled laser source.
    """
    
    def __init__(self, MCLS1):
        super().__init__()
        self.MCLS1 = MCLS1
        ui_file_path = os.path.join(os.path.dirname(__file__), 'throlabs_MCSL1.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.system_enable_checkBox.toggled.connect(self.system_enable)
        
        
    def system_enable(self):
        if self.system_enable_checkBox.isChecked():
            self.MCLS1.system_enable = 1
        else:
            self.MCLS1.system_enable = 0

        
        
if __name__ == '__main__' :
    
    myMCLS1 = thorlabs_MCLS1('COM4')
    
    ui_app = QtWidgets.QApplication([])
    ui = thorlabs_MCLS1_ui(myMCLS1)
    ui.show()
    ui_app.exec()