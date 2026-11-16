# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 12:10:44 2023

@author: deankos
"""

import threading
import pyvisa

class visa_instrument():
    """
    Instrument using the VISA communication protocol.
    
    address: str; instrument address obtained e.g. from pyvisa ResourceManager or NI MAX
    
    write, read and query can be called from several threads. Each call holds self.lock until it is complete,
    so that another thread cannot send a command between the write and the read of a query, and each query
    reads its own reply. Use "with instrument.lock:" around a sequence of commands that must not be
    interrupted by commands from other threads.
    """
    
    def __init__(self, address = None, remove_termination = True):
        self.remove_termination = remove_termination
        resource_manager = pyvisa.ResourceManager()
        self.instrument = resource_manager.open_resource(address)
        # reentrant lock: a thread already holding it, e.g. in a "with instrument.lock:" block, can take it again
        self.lock = threading.RLock()
        
    def write(self, *args, **kwargs):
        with self.lock:
            self.instrument.write(*args, **kwargs)
        
    def read(self, *args, **kwargs):
        with self.lock:
            if self.remove_termination:
                return self.instrument.read(*args, **kwargs).rstrip()
            else:
                return self.instrument.read(*args, **kwargs)
        
    def query(self, *args, **kwargs):
        with self.lock:
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