# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 16:25:23 2024

@author: deankos
"""

import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

class arduino_shutter_controller(serial_instrument):
    """
    Class to interact with Arduino solenoid shutter controller.
    See: nanomol\instruments\arduino\arduino_solenoid_shutter
    """
    
    def __init__(self, port):
        settings = {'baudrate': 115200,
                    'timeout': 1 }
        termination = '\n'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
        
    def enable_shutter(self, shutter_pin):
        """
        shutter_pin : int
            Arduino digital pin connected to the shutter to be opened
        """
        self.write('enable,{:d}'.format(shutter_pin))
        
    def disable_shutter(self, shutter_pin):
        """
        shutter_pin : int
            Arduino digital pin connected to the shutter to be opened
        """
        self.write('disable,{:d}'.format(shutter_pin))
    
    def open_shutter(self, shutter_pin):
        self.write('open,{:d}'.format(shutter_pin))
    
    def close_shutter(self, shutter_pin):
        self.write('close,{:d}'.format(shutter_pin))
    
    def status(self):
        """
        Returns
        status : int
            status (0: closed, 1: open) of each shutter, in ascending Arduino pin number order
        """
        return self.query('status?')

class arduino_shutter_controller_ui(interactive_ui):
    
    def __init__(self, shutter_controller):
        super().__init__()
        self.shutter_controller = shutter_controller
        ui_file_path = os.path.join(os.path.dirname(__file__), 'arduino_shutter_controller.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.shutter_2_open_pushButton.clicked.connect(self.open_shutter)
        self.shutter_2_close_pushButton.clicked.connect(self.close_shutter)
        self.read_state_pushButton.clicked.connect(self.read_state)
        
    def open_shutter(self):
        if self.sender() == self.shutter_2_open_pushButton:
            shutter_pin = 2
        self.shutter_controller.open_shutter(shutter_pin)
    
    def close_shutter(self):
        if self.sender() == self.shutter_2_close_pushButton:
            shutter_pin = 2
        self.shutter_controller.close_shutter(shutter_pin)
        
    def read_state(self):
        state = self.shutter_controller.status()
        self.state_lineEdit.setText(state)

if __name__ == '__main__' :
    
    myShutterController = arduino_shutter_controller('COM7')
    
    ui_app = QtWidgets.QApplication([])
    ui = arduino_shutter_controller_ui(myShutterController)
    ui.show()
    ui_app.exec()