# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 14:33:02 2024

@author: deankos
"""

from nanomol.instruments.serial_instrument import serial_instrument

class tenma_72_2705(serial_instrument):
    
    def __init__(self, port):
        settings = {'baudrate': 9600,
                    'timeout': 1 }
        super().__init__(port=port, port_settings=settings)
        
    @property
    def current(self):
        """ returns measured output current in A """
        return float(self.query('IOUT1?'))
    @current.setter
    def current(self, current):
        """ set output current in A """
        self.write('ISET1:{:.3}'.format(float(current)) )
    
    def current_setting(self):
        """ returns set output current """
        return float(self.query('ISET1?'))
    
    @property
    def voltage(self):
        """ returns measured output voltage in V """
        return float(self.query('VOUT1?'))
    @voltage.setter
    def voltage(self, voltage):
        """ set output voltage in V """
        self.write('VSET1:{:.2}'.format(float(voltage)) )
    
    def voltage_setting(self):
        """ returns set output voltage """
        return float(self.query('VSET1?'))
    

if __name__ == '__main__' :
    
    myTenma = tenma_72_2705('COM5')
    
    # ui_app = QtWidgets.QApplication([])
    # ui = optosigma_GSC_01_ui(myGSC01)
    # ui.show()
    # ui_app.exec()