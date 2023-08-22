# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 12:10:44 2023

@author: deankos
"""

import pyvisa

class visa_instrument():
    """
    Instrument using the VISA communication protocol.
    
    address: str; instrument address obtained e.g. from pyvisa ResourceManager or NI MAX
    """
    
    def __init__(self, address = '', remove_termination = True):
        self.remove_termination = remove_termination
        resource_manager = pyvisa.ResourceManager()
        self.instrument = resource_manager.open_resource(address)
        
    def write(self, *args, **kwargs):
        self.instrument.write(*args, **kwargs)
        
    def read(self, *args, **kwargs):
        if self.remove_termination:
            return self.instrument.read(*args, **kwargs).rstrip()
        else:
            return self.instrument.read(*args, **kwargs)
        
    def query(self, *args, **kwargs):
        if self.remove_termination:
            return self.instrument.query(*args, **kwargs).rstrip()
        else:
            return self.instrument.query(*args, **kwargs)
    
    def close(self):
        self.instrument.close()


if __name__ == '__main__' :
    
    myResourceManager = pyvisa.ResourceManager()
    for resource in myResourceManager.list_resources():
        print(resource)
    
    resource = visa_instrument(address = 'GPIB0::27::INSTR')