# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 15:30:07 2023

@author: deankos
"""

import os
import time
import threading
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

class newport_CONEX_MFA_CC(serial_instrument):
    """ Class for Newport CONEX MFA-CC closed loop stage-controller positioning system. """
    
    def __init__(self, port):
        settings = {'baudrate': 921600,
                    'timeout': 1,
                    'xonxoff': True }
        termination = '\r\n'
        super().__init__(port=port, port_settings=settings, termination_character=termination)
        
    def move_relative(self, displacement):
        """
        displacement : float
            Displacement from current position in mm, positive or negative.
        """
        self.write('1pr{:.6f}'.format(displacement))
    
    def move_absolute(self, position):
        """
        position : float
            Target absolute position in mm.
        """
        self.write('1pa{:.6f}'.format(position))
    
    def time_for_move_relative(self, displacement):
        """
        displacement : float
            Displacement in mm, >0.
        Returns
        time : float
            Time required to move by displacement, in seconds.
        """
        time_to_parse = self.query('1pt{:.6f}'.format(displacement))
        time = time_to_parse.split('PT', 1)[1]
        return float(time)
    
    def position(self):
        position_str = self.query('1tp')
        position = position_str.split('TP', 1)[1]
        return float(position)
    
    def is_moving(self):
        state = self.state()[-2:]
        if state == '28':
            return True
        else:
            return False
    
    def state(self):
        return self.query('1ts')
    
    @property
    def software_limit_min(self):
        return self.query('1sl?')
    @software_limit_min.setter
    def software_limit_min(self, software_limit_min):
        self.write('1sl{:.6f}'.format(software_limit_min))
    
    @property
    def software_limit_max(self):
        return self.query('1sr?')
    @software_limit_max.setter
    def software_limit_max(self, software_limit_max):
        self.write('1sr{:.6f}'.format(software_limit_max))   
    
    def home(self):
        return self.write('1or')
    
    def get_error(self):
        """ returns most recent error, see manual """
        return self.query('1te')
    
    def configuration(self):
        """ list all current configuration parameters, see manual """
        self.reset_input_buffer()
        self.write('1zt')
        configuration = []
        time.sleep(0.1)
        while self.instrument.in_waiting:
            configuration.append(self.read())
        return configuration
    
    def reset(self):
        """ reset controller, equivalent to power cycling """
        self.write('1rs')

class newport_CONEX_MFA_CC_XY_ui(interactive_ui):
    """
    User interface for 2 axes CONEX-MFA-CC.
    """
    def __init__(self, stage_X, stage_Y):
        super().__init__()
        self.stage_X = stage_X
        self.stage_Y = stage_Y
        ui_file_path = os.path.join(os.path.dirname(__file__), 'newport_CONEX_MFA_CC_XY.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.state_X_pushButton.clicked.connect(self.state_X_update)
        self.state_Y_pushButton.clicked.connect(self.state_Y_update)
        self.update_positions_pushButton.clicked.connect(self.update_positions)
        self.move_relative_neg_X_pushButton.clicked.connect(self.move_relative_X)
        self.move_relative_pos_X_pushButton.clicked.connect(self.move_relative_X)
        self.move_relative_neg_Y_pushButton.clicked.connect(self.move_relative_Y)
        self.move_relative_pos_Y_pushButton.clicked.connect(self.move_relative_Y)
        self.move_absolute_X_pushButton.clicked.connect(self.move_absolute)
        self.move_absolute_Y_pushButton.clicked.connect(self.move_absolute)
        self.home_X_pushButton.clicked.connect(self.home_X)
        self.home_Y_pushButton.clicked.connect(self.home_Y)
        self.reset_X_pushButton.clicked.connect(self.reset_X)
        self.reset_Y_pushButton.clicked.connect(self.reset_Y)
        
    def state_X_update(self):
        state = self.stage_X.state()
        self.state_X_lineEdit.setText(state)
    
    def state_Y_update(self):
        state = self.stage_Y.state()
        self.state_Y_lineEdit.setText(state)
    
    def move_absolute(self):
        if self.sender() == self.move_absolute_X_pushButton and not self.stage_X.is_moving():
            self.stage_X.move_absolute(self.move_absolute_position_X)
            motion_thread = threading.Thread(target=self.wait_for_motion_completed, args=(self.stage_X,) )
            motion_thread.start()
        elif self.sender() == self.move_absolute_Y_pushButton and not self.stage_Y.is_moving():
            self.stage_Y.move_absolute(self.move_absolute_position_Y)
            motion_thread = threading.Thread(target=self.wait_for_motion_completed, args=(self.stage_Y,) )
            motion_thread.start()
    
    def move_relative_X(self):
        if not self.stage_X.is_moving():
            if self.sender() == self.move_relative_neg_X_pushButton:
                direction = -1
            elif self.sender() == self.move_relative_pos_X_pushButton:
                direction = 1
            if self.custom_step_X_checkBox.isChecked():
                step = float(self.move_relative_custom_step_X)
            else:
                step = float(self.move_relative_step_X)
            self.stage_X.move_relative(step * direction)
            self.stage_X.move_relative(step * direction)
            motion_thread = threading.Thread(target=self.wait_for_motion_completed, args=(self.stage_X,) )
            motion_thread.start()
    
    def move_relative_Y(self):
        if not self.stage_Y.is_moving():
            if self.sender() == self.move_relative_neg_Y_pushButton:
                direction = -1
            elif self.sender() == self.move_relative_pos_Y_pushButton:
                direction = 1
            if self.custom_step_Y_checkBox.isChecked():
                step = float(self.move_relative_custom_step_Y)
            else:
                step = float(self.move_relative_step_Y)
            self.stage_Y.move_relative(step * direction)
            motion_thread = threading.Thread(target=self.wait_for_motion_completed, args=(self.stage_Y,) )
            motion_thread.start()
                                    
    def wait_for_motion_completed(self, stage):
        # called within a thread to avoid blocking gui during motion, update position when finished
        while stage.is_moving():
            time.sleep(0.05)
        self.update_position(stage)
        
    def update_position(self, stage):
        position = stage.position()
        if stage == self.stage_X:
            self.position_X_lineEdit.setText('{:.6f}'.format(position))
        elif stage == self.stage_Y:
            self.position_Y_lineEdit.setText('{:.6f}'.format(position))
    
    def update_positions(self):
        self.position_X_lineEdit.setText('{:.6f}'.format(self.stage_X.position()) )
        self.position_Y_lineEdit.setText('{:.6f}'.format(self.stage_Y.position()) )
            
    def home_X(self):
        self.stage_X.home()
        
    def home_Y(self):
        self.stage_Y.home()
        
    def reset_X(self):
        self.stage_X.reset()
        
    def reset_Y(self):
        self.stage_Y.reset()
    
        
if __name__ == '__main__' :
    
    myMFACC_X = newport_CONEX_MFA_CC('COM6')
    myMFACC_Y = newport_CONEX_MFA_CC('COM5')
    
    ui_app = QtWidgets.QApplication([])
    ui = newport_CONEX_MFA_CC_XY_ui(myMFACC_X, myMFACC_Y)
    ui.show()
    ui_app.exec()