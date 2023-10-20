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
        """
        pulses : int
            Number of pulses to move by from current position, positive or negative.
        """
        if pulses < 0:
            command_state = self.query('M:1-P{}'.format(int(abs(pulses)) ) )
        elif pulses > 0:
            command_state = self.query('M:1+P{}'.format(int(pulses)) )
        if command_state == 'OK':
            command_state = self.query('G:')
        return command_state
    
    def move_absolute(self, position):
        """
        position : int
            Absolute position to move to, in number of pulses relative to current origin.
        """
        if position < 0:
            command_state = self.query('A:1-P{}'.format(int(abs(position)) ) )
        elif position >= 0:
            command_state = self.query('A:1+P{}'.format(int(position)) )
        if command_state == 'OK':
            command_state = self.query('G:')
        return command_state
    
    def jog(self, direction):
        """
        Start jogging in given direction. Speed is set by jog_speed property.
        CAUTION: if jog is not followed by a stop command, stage will move until reaching a limit sensor.
        
        direction : str
            '+' positive direction, '-' negative direction
        """
        command_state = self.query('J:1' + direction)
        if command_state == 'OK':
            command_state = self.query('G:')
        return command_state
    
    def decelerate_stop(self):
        return self.query('L:1')
    
    def stop(self):
        return self.query('L:E')
    
    @property
    def jog_speed(self):
        """ jog speed in pulses per second """
        return int(self.query('V:J'))
    @jog_speed.setter
    def jog_speed(self, speed):
        """ set jog speed in pulses per second, 100-20000pps. Factory preset 500pps. """
        return self.query('S:J{}'.format(int(speed)) )
    
    @property
    def position(self):
        """ absolute position in pulses """
        device_state = self.query('Q:')
        position = device_state.split(',', 1)[0]
        position = position.replace(' ', '')
        return int(position)
    @position.setter
    def position(self, position):
        self.move_absolute(position)
    
    def origin(self):
        """ set current stage position as origin """
        command_state = self.query('R:1')
        return command_state
    
    def state(self):
        """
        Returns
        device_state : str
            string of 3 letters: 's1,s2,s3'
            s1: X: command error
                K: command accepted normally
            s2: L: stage stopped at limit sensor
                K: stage stopped normally
            s3: B: stage busy
                R: stage ready 
        """
        device_state = self.query('Q:')
        device_state = device_state.split(',', 1)[1]
        return device_state
            
        
if __name__ == '__main__' :
    
    myGSC01 = optosigma_GSC_01('COM1')