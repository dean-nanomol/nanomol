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
    
    def output(self, output):
        """ 0: OFF ; 1:ON """
        self.write('OUT{}'.format(int(output)) )
        
    def status(self):
        """
        Returns
        status : str
            string of 8 bits. bit 0 is last.
            bit 0: 0: constant current; 1:constant voltage
            bit 6: 0: output OFF; 1: output ON
            bits 1,2,3,4,5,7: not used
            e.g. '00010010': OFF, constant current; '01010011': ON, constant voltage
        """
        status = self.query('STATUS?').encode()
        status_int = ord(status)
        status_bin = format(status_int, 'b').zfill(8)
        status = status_bin
        return status

if __name__ == '__main__' :
    
    myTenma = tenma_72_2705('COM5')
    
    # ui_app = QtWidgets.QApplication([])
    # ui = optosigma_GSC_01_ui(myGSC01)
    # ui.show()
    # ui_app.exec()