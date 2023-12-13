# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:39:43 2023

@author: deankos
"""

from nanomol.instruments.keithley_2600A import keithley_2600A

class keithley_2600_LED_driver():
    """ Keithley SMU used to drive an LED """
    
    def __init__(self, smu):
        super().__init__()