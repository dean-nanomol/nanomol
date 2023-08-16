# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 14:47:39 2023

@author: deankos
"""

from nanomol.instruments.visa_instrument import visa_instrument

class keithley_2600A(visa_instrument):
    
    def __init__(self, address):
        super(keithley_2600A, self).__init__(address)
        self.reset()
    
    def source_function(self, ch, function):
        """
        set source type
        
        ch: str; channel, 'a', 'A', 'b', or 'B'
        function: int; 0 for current source, 1 for voltage source
        """
        self.write('smu{}.source.func = {}'.format(ch, function))
    
    def source(self, ch, Y, value):
        """
        set source ouput value
        
        ch: str; channel, 'a', 'A', 'b', or 'B'
        Y: str; source type: 'v', 'V', 'i', or 'I'
        value: float; voltage in V, or current in A
        """
        self.write('smu{}.source.level{} = {}'.format(ch, Y, value) )
        
    def limit(self, ch, Y, value):
        """
        set compliance limit value
        
        ch: str; channel, 'a', 'A', 'b', or 'B'
        Y: str; source type: 'v', 'V', 'i', or 'I'
        value: float; voltage in V, or current in A
        """
        self.write('smu{}.source.limit{} = {}'.format(ch, Y, value) )
        
    def reset(self):
        self.write('reset()')
    
if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::27::INSTR')