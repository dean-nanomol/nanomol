# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 17:12:59 2024

@author: deankos
"""

import numpy as np
#import os
import time
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
#from nanomol.utils.interactive_ui import interactive_ui

class thorlabs_MCLS1(serial_instrument):
    
    def __init__(self, port):
        settings = {'baudrate': 115200,
                    'timeout': 1 }
        termination = '\r'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
        
if __name__ == '__main__' :
    
    myMCLS1 = thorlabs_MCLS1('COM4')
    
    #ui_app = QtWidgets.QApplication([])
    #ui = thorlabs_MCLS1_ui(myGSC01)
    #ui.show()
    #ui_app.exec()