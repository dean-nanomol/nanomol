# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:39:43 2023

@author: deankos
"""

import os
from PyQt5 import QtWidgets, uic
from nanomol.instruments.visa_instrument import visa_instrument
from nanomol.instruments.keithley_2600A import keithley_2600A

class keithley_2600_LED_driver_ui():
    """ Keithley SMU used to drive an LED """
    
    def __init__(self, smu):
        super().__init__()
        self.smu = smu
        
    