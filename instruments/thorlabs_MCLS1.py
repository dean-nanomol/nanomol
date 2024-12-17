# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 17:12:59 2024

@author: deankos
"""

import os
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
        # MCLS1 repeats each command it receives
        # MCLS1 sends '>' when commands execute without errors, so buffer may not be empty
        self.reset_input_buffer()
        if '?' in command:
            # querying a value so ignore first returned string, contains command repetition
            super().query(command)
        return super().query(command)
    
    @property
    def channel(self):
        return int(self.query('channel?'))
    @channel.setter
    def channel(self, channel):
        """ active channel """
        self.query('channel={}'.format(int(channel)))
        
    @property
    def target_temperature(self):
        return float(self.query('target?'))
    @target_temperature.setter
    def target_temperature(self, target_temperature):
        """
        target_temperature : float
            active channel target temperature in °C, 20 <= target_temperature <= 30
        """
        self.query('target={}'.format(target_temperature))
    
    @property
    def current(self):
        return float(self.query('current?'))
    @current.setter
    def current(self, current):
        """
        current : float
            active channel current in mA
        """
        self.query('current={}'.format(current))
    
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
        self.query('enable={}'.format(enable))
        
    @property
    def system_enable(self):
        return int(self.query('system?'))
    @system_enable.setter
    def system_enable(self, system_enable):
        """
        system_enable : int
            0 or 1, disable or enable laser system
        """
        self.query('system={}'.format(system_enable))
        
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
        self.system_enable_checkBox.stateChanged.connect(self.system_enable)
        
        enable_checkBoxes = [self.enable_ch1_checkBox, self.enable_ch2_checkBox,
                          self.enable_ch3_checkBox, self.enable_ch4_checkBox]
        for checkBox in enable_checkBoxes:
            checkBox.stateChanged.connect(self.enable)
            
        set_current_spinBoxes = [self.current_ch1_doubleSpinBox, self.current_ch2_doubleSpinBox,
                               self.current_ch3_doubleSpinBox, self.current_ch4_doubleSpinBox]
        for spinBox in set_current_spinBoxes:
            spinBox.valueChanged.connect(self.set_current)
            
        get_power_buttons = [self.get_power_ch1_pushButton, self.get_power_ch2_pushButton,
                             self.get_power_ch3_pushButton, self.get_power_ch4_pushButton]
        for pushButton in get_power_buttons:
            pushButton.clicked.connect(self.get_power)
            
        target_T_spinBoxes = [self.target_T_ch1_doubleSpinBox, self.target_T_ch2_doubleSpinBox,
                              self.target_T_ch3_doubleSpinBox, self.target_T_ch4_doubleSpinBox]
        for spinBox in target_T_spinBoxes:
            spinBox.valueChanged.connect(self.set_target_temperature)
            
        get_T_pushButtons = [self.get_T_ch1_pushButton, self.get_T_ch2_pushButton,
                             self.get_T_ch3_pushButton, self.get_T_ch4_pushButton]
        for pushButton in get_T_pushButtons:
            pushButton.clicked.connect(self.get_temperature)
        
    def system_enable(self):
        if self.system_enable_checkBox.isChecked():
            self.MCLS1.system_enable = 1
        else:
            self.MCLS1.system_enable = 0
    
    def enable(self):
        if self.sender() == self.enable_ch1_checkBox:
            self.MCLS1.channel = 1
        elif self.sender() == self.enable_ch2_checkBox:
            self.MCLS1.channel = 2
        elif self.sender() == self.enable_ch3_checkBox:
            self.MCLS1.channel = 3
        elif self.sender() == self.enable_ch4_checkBox:
            self.MCLS1.channel = 4
        if self.sender().isChecked():
            self.MCLS1.enable = 1
        else:
            self.MCLS1.enable = 0

    def set_current(self):
        if self.sender() == self.current_ch1_doubleSpinBox:
            self.MCLS1.channel = 1
            current = self.current_ch1
        elif self.sender() == self.current_ch2_doubleSpinBox:
            self.MCLS1.channel = 2
            current = self.current_ch2
        elif self.sender() == self.current_ch3_doubleSpinBox:
            self.MCLS1.channel = 3
            current = self.current_ch3
        elif self.sender() == self.current_ch4_doubleSpinBox:
            self.MCLS1.channel = 4
            current = self.current_ch4
        self.MCLS1.current = current
        
    def get_power(self):
        if self.sender() == self.get_power_ch1_pushButton:
            self.MCLS1.channel = 1
            self.power_ch1_lineEdit.setText(str(self.MCLS1.power))
        elif self.sender() == self.get_power_ch2_pushButton:
            self.MCLS1.channel = 2
            self.power_ch2_lineEdit.setText(str(self.MCLS1.power))
        elif self.sender() == self.get_power_ch3_pushButton:
            self.MCLS1.channel = 3
            self.power_ch3_lineEdit.setText(str(self.MCLS1.power))
        elif self.sender() == self.get_power_ch4_pushButton:
            self.MCLS1.channel = 4
            self.power_ch4_lineEdit.setText(str(self.MCLS1.power))
    
    def set_target_temperature(self):
        if self.sender() == self.target_T_ch1_doubleSpinBox:
            self.MCLS1.channel = 1
            target_T = self.target_T_ch1
        elif self.sender() == self.target_T_ch2_doubleSpinBox:
            self.MCLS1.channel = 2
            target_T = self.target_T_ch2
        elif self.sender() == self.target_T_ch3_doubleSpinBox:
            self.MCLS1.channel = 3
            target_T = self.target_T_ch3
        elif self.sender() == self.target_T_ch4_doubleSpinBox:
            self.MCLS1.channel = 4
            target_T = self.target_T_ch4
        self.MCLS1.target_temperature = target_T
    
    def get_temperature(self):
        if self.sender() == self.get_T_ch1_pushButton:
            self.MCLS1.channel = 1
            self.T_ch1_lineEdit.setText(str(self.MCLS1.temperature))
        elif self.sender() == self.get_T_ch2_pushButton:
            self.MCLS1.channel = 2
            self.T_ch2_lineEdit.setText(str(self.MCLS1.temperature))
        elif self.sender() == self.get_T_ch3_pushButton:
            self.MCLS1.channel = 3
            self.T_ch3_lineEdit.setText(str(self.MCLS1.temperature))
        elif self.sender() == self.get_T_ch4_pushButton:
            self.MCLS1.channel = 4
            self.T_ch4_lineEdit.setText(str(self.MCLS1.temperature))
        
        
if __name__ == '__main__' :
    
    myMCLS1 = thorlabs_MCLS1('COM8')
    
    ui_app = QtWidgets.QApplication([])
    ui = thorlabs_MCLS1_ui(myMCLS1)
    ui.show()
    ui_app.exec()