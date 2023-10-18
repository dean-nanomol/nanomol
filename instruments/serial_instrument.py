# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 16:59:42 2023

@author: deankos
"""

import serial

class serial_instrument():
    
    def __init__(self, port=None, port_settings={} ):
        self.instrument = serial.Serial(port, **port_settings)
        
if __name__ == '__main__' :
    
    settings = {'baudrate': 9600}
    mySerialInstrument = serial_instrument('COM1', settings)