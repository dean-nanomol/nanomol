# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 15:30:07 2023

@author: deankos
"""

import numpy as np
import os
import time
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

class newport_CONEX_MFA_CC(serial_instrument):
    
    def __init__(self, port):
        settings = {'baudrate': 921600,
                    'timeout': 1,
                    'xonxoff': True }
        termination = '\r\n'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
        
    def move_relative(self, displacement):
        self.write('1pr{:.6f}'.format(displacement))
    
    def move_absolute(self, position):
        self.write('1pa{:.6f}'.format(position))
    
    @property
    def position(self):
        return self.query('1tp')
    
    def home(self):
        return self.write('1or')
    
    def state(self):
        return self.query('1ts')
    
        
if __name__ == '__main__' :
    
    myMFACC = newport_CONEX_MFA_CC('COM3')
    
    # ui_app = QtWidgets.QApplication([])
    # ui = optosigma_GSC_01_ui(myGSC01)
    # ui.show()
    # ui_app.exec()