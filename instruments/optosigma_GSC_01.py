# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 16:47:42 2023

@author: deankos
"""

import serial

class optosigma_GSC_01():
    
    def __init__(self, address=''):
        self.reset()