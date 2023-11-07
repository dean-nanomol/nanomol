# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 16:47:42 2023

@author: deankos
"""

import numpy as np
import os
import time
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

class GSC01_SoftLimitExceededError(Exception):
    def __init__(self, target, limit_min, limit_max):
        self.message = 'Target position {} exceeds soft limits: [{}, {}]'.format(target, limit_min, limit_max)
        super().__init__(self.message)

class GSC01_LimitSensorTriggeredError(Exception):
    def __init__(self):
        self.message = 'Limit sensor triggered'
        super().__init__(self.message)

class optosigma_GSC_01(serial_instrument):
    """
    Class for OptoSigma GSC-01 stage controller. Motion is open loop through stepper motor, controller sends
    pulses and keeps track of number of sent pulses. Stages have physical limit sensors and cannot move beyond
    these limits. The class implements "soft limits" set by the user, move commands (EXCEPT jog) check these
    limits are not exceeded before moving.
    """
    
    def __init__(self, port):
        settings = {'baudrate': 9600,
                    'rtscts': True,
                    'timeout': 1 }
        termination = '\r\n'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
        self.software_limit_min = -np.inf
        self.software_limit_max = np.inf
        self.query_interval = 0.05
    
    def home(self):
        """ Return to home position near negative limit sensor. """
        command_state = self.query('H:1')
        return command_state
        
    def move_relative(self, pulses):
        """
        pulses : int
            Number of pulses to move by from current position, positive or negative.
        """
        if self.software_limit_min <= (self.position + pulses) <= self.software_limit_max:
            if pulses < 0:
                command_state = self.query('M:1-P{}'.format(int(abs(pulses)) ) )
            elif pulses > 0:
                command_state = self.query('M:1+P{}'.format(int(pulses)) )
            if command_state == 'OK':
                command_state = self.query('G:')
            if command_state == 'OK':
                while self.is_busy():
                    time.sleep(self.query_interval)
                if self.limit_sensor_triggered():
                    raise GSC01_LimitSensorTriggeredError()
        else:
            raise GSC01_SoftLimitExceededError(self.position + pulses, self.software_limit_min, self.software_limit_max)      
    
    def move_absolute(self, position):
        """
        position : int
            Absolute position to move to, in number of pulses relative to current origin.
        """
        if self.software_limit_min <= position <= self.software_limit_max:
            if position < 0:
                command_state = self.query('A:1-P{}'.format(int(abs(position)) ) )
            elif position >= 0:
                command_state = self.query('A:1+P{}'.format(int(position)) )
            if command_state == 'OK':
                command_state = self.query('G:')
            if command_state == 'OK':
                while self.is_busy():
                    time.sleep(self.query_interval)
                if self.limit_sensor_triggered():
                    raise GSC01_LimitSensorTriggeredError()
        else:
            raise GSC01_SoftLimitExceededError(position, self.software_limit_min, self.software_limit_max)
    
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
    
    def move_speed(self, speed_min, speed_max, acceleration):
        """
        Speed and acceleration for absolute and relative move commands
        
        speed_min : int
            Speed when motion starts, in pulses per second. Factory preset 500pps. 
        speed_max : TYPE
            Max speed reached during motion, in pulses per second. Factory preset 5000pps.
        acceleration : TYPE
            Acceleration/deceleration time. Factory preset 200ms.
        """
        return self.query('D:1S{}F{}R{}'.format(int(speed_min), int(speed_max), int(acceleration)) )
    
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
    
    def origin(self):
        """ set current stage position as origin """
        self.software_limit_min += self.position
        self.software_limit_max += self.position
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
    
    def is_busy(self):
        """ Returns True if stage is currently moving, False otherwise """
        device_state = self.state()
        motion_state = device_state.split(',', 2)[2]
        if motion_state == 'B':
            return True
        elif motion_state == 'R':
            return False
        
    def limit_sensor_triggered(self):
        """ Returns True if stage has stopped by triggering a limit sensor, False otherwise """
        device_state = self.state()
        limit_sensor_state = device_state.split(',', 2)[1]
        if limit_sensor_state == 'L':
            return True
        elif limit_sensor_state == 'K':
            return False

class optosigma_GSC_01_ui(interactive_ui):
    """
    User interface for OptoSigma GSC-01 controller.
    """
    
    def __init__(self, GSC01):
        super().__init__()
        self.GSC01 = GSC01
        ui_file_path = os.path.join(os.path.dirname(__file__), 'optosigma_GSC_01.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.device_state_pushButton.clicked.connect(self.show_state)
        self.update_position_pushButton.clicked.connect(self.update_position)
        self.move_to_pushButton.clicked.connect(self.move_to)
        self.move_relative_positive_pushButton.clicked.connect(self.move_relative)
        self.move_relative_negative_pushButton.clicked.connect(self.move_relative)
        self.jog_positive_pushButton.pressed.connect(self.jog_start)
        self.jog_negative_pushButton.pressed.connect(self.jog_start)
        self.jog_positive_pushButton.released.connect(self.jog_stop)
        self.jog_negative_pushButton.released.connect(self.jog_stop)
        self.jog_speed_comboBox.currentTextChanged.connect(self.set_jog_speed)
        self.custom_jog_speed_spinBox.valueChanged.connect(self.set_jog_speed)
        self.set_current_software_min_pushButton.clicked.connect(self.set_soft_limit)
        self.set_current_software_max_pushButton.clicked.connect(self.set_soft_limit)
        self.software_limit_min_spinBox.valueChanged.connect(self.set_soft_limit)
        self.software_limit_max_spinBox.valueChanged.connect(self.set_soft_limit)
        self.origin_pushButton.clicked.connect(self.origin)
        self.home_pushButton.clicked.connect(self.home)
        self.update_position()
        self.set_jog_speed()
        
    def update_position(self):
        position = self.GSC01.position
        self.current_position_lineEdit.setText(str(position))
    
    def move_to(self):
        self.GSC01.move_absolute(self.absolute_move_position)
        self.update_position()
        
    def move_relative(self):
        if self.move_relative_pulses == 'custom':
            self.move_relative_pulses = self.custom_move_pulses
        if self.sender() == self.move_relative_positive_pushButton:
            self.GSC01.move_relative(int(self.move_relative_pulses))
        elif self.sender() == self.move_relative_negative_pushButton:
            self.GSC01.move_relative(-int(self.move_relative_pulses))
        self.update_position()
        
    def set_jog_speed(self):
        if self.jog_speed == 'custom':
            self.GSC01.jog_speed = self.custom_jog_speed
        else:
            self.GSC01.jog_speed = self.jog_speed
    
    def jog_start(self):
        if self.sender() == self.jog_positive_pushButton:
            self.GSC01.jog('+')
        elif self.sender() == self.jog_negative_pushButton:
            self.GSC01.jog('-')
    
    def jog_stop(self):
        self.GSC01.stop()
        self.update_position()
        
    def set_soft_limit(self):
        if self.sender() == self.set_current_soft_min_pushButton:
            self.GSC01.software_limit_min = self.GSC01.position
            self.software_limit_min_spinBox.setValue(self.GSC01.software_limit_min)
        elif self.sender() == self.set_current_soft_max_pushButton:
            self.GSC01.software_limit_max = self.GSC01.position
            self.software_limit_max_spinBox.setValue(self.GSC01.software_limit_max)
        elif self.sender() == self.software_limit_min_spinBox:
            self.GSC01.software_limit_min = self.software_limit_min
        elif self.sender() == self.software_limit_max_spinBox:
            self.GSC01.software_limit_max = self.software_limit_max
    
    def show_state(self):
        state = self.GSC01.state()
        state += '; soft limits [{},{}]'.format(self.GSC01.software_limit_min, self.GSC01.software_limit_max)
        state += '; position: {}'.format(self.GSC01.position)
        self.device_state_lineEdit.setText(state)
        
    def origin(self):
        self.GSC01.origin()
        self.update_position()
        
    def home(self):
        self.GSC01.home()
        
if __name__ == '__main__' :
    
    myGSC01 = optosigma_GSC_01('COM1')
    
    ui_app = QtWidgets.QApplication([])
    ui = optosigma_GSC_01_ui(myGSC01)
    ui.show()
    ui_app.exec()