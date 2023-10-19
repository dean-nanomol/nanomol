# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 16:47:42 2023

@author: deankos
"""

from nanomol.instruments.serial_instrument import serial_instrument

class optosigma_GSC_01(serial_instrument):
    
    def __init__(self, port):
        settings = {'baudrate': 9600,
                    'rtscts': True,
                    'timeout': 1 }
        termination = '\r\n'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
    
    def home(self):
        command_state = self.query('H:1')
        return command_state
        
    def move_relative(self, pulses):
        if pulses < 0:
            command_state = self.query('M:1-P{}'.format(int(abs(pulses)) ) )
        elif pulses > 0:
            command_state = self.query('M:1+P{}'.format(int(pulses)) )
        if command_state == 'OK':
            command_state = self.query('G:')
        return command_state
    
    def position(self):
        device_state = self.query('Q:')
        position = device_state.split(',', 1)[0]
        position = position.replace(' ', '')
        return int(position)
    
    def state(self):
        device_state = self.query('Q:')
        device_state = device_state.split(',', 1)[1]
        return device_state
            
        
if __name__ == '__main__' :
    
    myGSC01 = optosigma_GSC_01('COM1')