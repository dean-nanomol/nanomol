# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 15:30:07 2023

@author: deankos
"""

import numpy as np
import os
import time
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
    
    @property
    def position(self):
        return self.query('1tp')
    
    @property
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
        ui_file_path = os.path.join(os.path.dirname(__file__), 'newport_CONEX_MFA_CC_XY_ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
    
        
if __name__ == '__main__' :
    
    myMFACC = newport_CONEX_MFA_CC('COM4')
    
    # ui_app = QtWidgets.QApplication([])
    # ui = optosigma_GSC_01_ui(myGSC01)
    # ui.show()
    # ui_app.exec()