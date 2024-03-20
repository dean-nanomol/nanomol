# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 16:59:42 2023

@author: deankos
"""

import serial

class serial_instrument():
    """
    Wrapper for serial.Serial class of pyserial. Functions include binary conversions and termination
    characters, so they directly accept and return python strings.
    """
    
    def __init__(self, port=None, port_settings={}, termination_character='\n'):
        """
        port : str
            Communication port to open, for example 'COM1'
        port_settings : dict
            Dictionary of port settings. See pySerial API documentation for full parameter list.
        termination_character : str
            Termination character for all messages, usually '\n', '\r' or '\r\n'
        """
        
        self.instrument = serial.Serial(port, **port_settings)
        self.termination_character = termination_character
        
    def write(self, command):
        """ command : str """
        binary_command = (command + self.termination_character).encode()
        self.instrument.write(binary_command)
        
    def read(self):
        """ read from buffer until next termination character """
        message = self.instrument.read_until(expected = self.termination_character.encode() )
        message = message.decode()
        return message.rstrip()
    
    def query(self, command):
        """ send command and return reply """
        self.write(command)
        return self.read()
    
    def reset_input_buffer(self):
        """ clear input buffer, discarding contents """ 
        self.instrument.reset_input_buffer()
    
    def close(self):
        self.instrument.close()
        
        
if __name__ == '__main__' :
    
    settings = {'baudrate': 9600,
                'rtscts': True,
                'timeout': 5 }
    termination = '\r\n'
    
    mySerialInstrument = serial_instrument(port='COM1', port_settings=settings, termination_character=termination)