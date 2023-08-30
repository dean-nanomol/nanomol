# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 14:47:39 2023

@author: deankos
"""

import os
from functools import partial
from PyQt5 import QtWidgets, uic
from nanomol.instruments.visa_instrument import visa_instrument

class keithley_2600A(visa_instrument):
    
    def __init__(self, address=''):
        super().__init__(address)
        self.reset()
    
    def get_source_function(self, ch):
        """
        ch : str
            channel, 'a' or 'b'

        Returns
        function : int
            source function type, 0 for current source, 1 for voltage source
        """
        return int( float( self.query('print(smu{}.source.func)'.format(ch)) ) )
    
    def set_source_function(self, ch, function):
        """
        ch : str
            channel, 'a' or 'b'
        function : int
            0 for current source, 1 for voltage source
        """
        self.write('smu{}.source.func = {}'.format(ch, function))
    
    def get_source_level(self, ch, Y):
        """
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type, 'v' or 'i'

        Returns
        level : float
            source output level
        """
        return float( self.query('print(smu{}.source.level{})'.format(ch, Y) ) )
    
    def set_source_level(self, ch, Y, level):
        """
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type, 'v' or 'i'
        level : float
            voltage in V or current in A
        """
        
        self.write('smu{}.source.level{} = {}'.format(ch, Y, level) )
        
    def get_source_limit(self, ch, Y):
        """
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type, 'v' or 'i'

        Returns
        limit : float
            source compliance limit
        """
        return float( self.query('print(smu{}.source.limit{})'.format(ch, Y)) )
        
    def set_source_limit(self, ch, Y, limit):
        """       
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type: 'v' or 'i'
        limit : float
            compliance limit; voltage in V or current in A
        """
        self.write('smu{}.source.limit{} = {}'.format(ch, Y, limit) )
        
    def get_source_range(self, ch, Y):
        """
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type, 'v' or 'i'

        Returns
        range : float
            source range setting
        """
        return float( self.query('print(smu{}.source.range{})'.format(ch, Y)) )
        
    def set_source_range(self, ch, Y, range_value):
        """       
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type: 'v' or 'i'
        range_value : float
            source range; voltage in V or current in A
        """
        self.write('smu{}.source.range{} = {}'.format(ch, Y, range_value) )
        
    def measure(self, ch, Y):
        """
        ch : str
            channel, 'a' or 'b'
        Y : str
            measurement type: 'v' voltage, 'i' current, 'iv' for current and voltage pair,
            'r' resistance, 'p' power

        Returns
        measurement : float or [float, float]
            measured value(s)
        """
        if Y == 'iv':
            measurement = self.query('print(smu{}.measure.{}())'.format(ch, Y)).split('\t')
            return [float(i) for i in measurement]
        else:
            return self.query('print(smu{}.measure.{}())'.format(ch, Y))
        
    def get_measure_range(self, ch, Y):
        """
        ch : str
            channel, 'a' or 'b'
        Y : str
            measurement type, 'v' or 'i'

        Returns
        range : float
            measurement range setting
        """
        return float( self.query('print(smu{}.measure.range{})'.format(ch, Y)) )
        
    def set_measure_range(self, ch, Y, range_value):
        """       
        ch : str
            channel, 'a' or 'b'
        Y : str
            source type: 'v' or 'i'
        range_value : float
            measurement range; voltage in V or current in A
        """
        self.write('smu{}.measure.range{} = {}'.format(ch, Y, range_value) )
        
    def get_nplc(self, ch):
        """
        ch : str
            channel, 'a' or 'b'

        Returns
        nplc : float
            measurement integration time in number of power line cycles (nplc)
        """
        return float( self.query('print(smu{}.measure.nplc)'.format(ch)) )
    
    def set_nplc(self, ch, nplc):
        """
        ch : str
            channel, 'a' or 'b'
        nplc : float
            measurement integration time in number of power line cycles (nplc)
        """
        self.write('smu{}.measure.nplc = {}'.format(ch, nplc))
                          
    def get_output(self, ch):
        """
        ch : str
            channel, 'a' or 'b'

        Returns
        output : int
            output state, 0 for OFF, 1 for ON, 2 for OFF in HIGH Z mode
        """
        return int( float( self.query('print(smu{}.source.output)'.format(ch)) ) )
    
    def set_output(self, ch, output):
        """       
        ch : str
            channel, 'a' or 'b'
        output : int
            output state: 0 for OFF, 1 for ON, 2 for OFF in HIGH Z mode
        """
        self.write('smu{}.source.output = {}'.format(ch, output) )
    
    def reset(self):
        self.write('reset()')
        
    def get_settings(self):
        settings = {'a_function': self.get_source_function('a'),
                    'b_function': self.get_source_function('b'),
                    'a_V_source_limit': self.get_source_limit('a', 'v'),
                    'b_V_source_limit': self.get_source_limit('b', 'v'),
                    'a_I_source_limit': self.get_source_limit('a', 'i'),
                    'b_I_source_limit': self.get_source_limit('b', 'i'),
                    'a_V_source_range': self.get_source_range('a', 'v'),
                    'b_V_source_range': self.get_source_range('b', 'v'),
                    'a_I_source_range': self.get_source_range('a', 'i'),
                    'b_I_source_range': self.get_source_range('b', 'i'),
                    'a_V_measure_range': self.get_measure_range('a', 'v'),
                    'b_V_measure_range': self.get_measure_range('b', 'v'),
                    'a_I_measure_range': self.get_measure_range('a', 'i'),
                    'b_I_measure_range': self.get_measure_range('b', 'i'),
                    'a_nplc': self.get_nplc('a'),
                    'b_nplc': self.get_nplc('b')
                    }
        return settings


class keithley_2600A_ui(QtWidgets.QWidget):
    """
    User interface for basic settings of Keithley 2600A instruments.
    """
    
    def __init__(self, keithley):
        super().__init__()
        self.keithley = keithley
        ui_file_path = os.path.join(os.path.dirname(__file__), 'keithley_2600A.ui')
        uic.loadUi(ui_file_path, self)
        self.V_source_range_a_comboBox.currentTextChanged.connect(self.update_setting)
        self.V_source_limit_a_doubleSpinBox.valueChanged.connect(self.update_setting)
        self.V_measure_range_a_comboBox.currentTextChanged.connect(self.update_setting)
        self.I_source_range_a_comboBox.currentTextChanged.connect(self.update_setting)
        self.I_source_limit_a_doubleSpinBox.valueChanged.connect(self.update_setting)
        self.I_measure_range_a_comboBox.currentTextChanged.connect(self.update_setting)
        self.nplc_a_doubleSpinBox.valueChanged.connect(self.update_setting)
        self.V_source_range_b_comboBox.currentTextChanged.connect(self.update_setting)
        self.V_source_limit_b_doubleSpinBox.valueChanged.connect(self.update_setting)
        self.V_measure_range_b_comboBox.currentTextChanged.connect(self.update_setting)
        self.I_source_range_b_comboBox.currentTextChanged.connect(self.update_setting)
        self.I_source_limit_b_doubleSpinBox.valueChanged.connect(self.update_setting)
        self.I_measure_range_b_comboBox.currentTextChanged.connect(self.update_setting)
        self.nplc_b_doubleSpinBox.valueChanged.connect(self.update_setting)
        self.update_all_settings()
        
    def update_setting(self, calling_widget=None):
        """
        Check which widget emitted the signal and update the corresponding keithley setting.
        If calling method directly pass calling_widget.
        """
        sender = self.sender()
        if sender is None:
            # function called without user interaction, e.g. through update_all_settings
            sender = calling_widget
        if sender == self.V_source_range_a_comboBox:
            self.keithley.set_source_range('a', 'v', sender.currentText() )
        elif sender == self.V_source_limit_a_doubleSpinBox:
            self.keithley.set_source_limit('a', 'v', sender.value() )
        elif sender == self.V_measure_range_a_comboBox:
            self.keithley.set_measure_range('a', 'v', sender.currentText() )
        elif sender == self.I_source_range_a_comboBox:
            self.keithley.set_source_range('a', 'i', sender.currentText() )
        elif sender == self.I_source_limit_a_doubleSpinBox:
            self.keithley.set_source_limit('a', 'i', sender.value() )
        elif sender == self.I_measure_range_a_comboBox:
            self.keithley.set_measure_range('a', 'i', sender.currentText() )
        elif sender == self.nplc_a_doubleSpinBox:
            self.keithley.set_nplc('a', sender.value() )
        elif sender == self.V_source_range_b_comboBox:
            self.keithley.set_source_range('b', 'v', sender.currentText() )
        elif sender == self.V_source_limit_b_doubleSpinBox:
            self.keithley.set_source_limit('b', 'v', sender.value() )
        elif sender == self.V_measure_range_b_comboBox:
            self.keithley.set_measure_range('b', 'v', sender.currentText() )
        elif sender == self.I_source_range_b_comboBox:
            self.keithley.set_source_range('b', 'i', sender.currentText() )
        elif sender == self.I_source_limit_b_doubleSpinBox:
            self.keithley.set_source_limit('b', 'i', sender.value() )
        elif sender == self.I_measure_range_b_comboBox:
            self.keithley.set_measure_range('b', 'i', sender.currentText() )
        elif sender == self.nplc_b_doubleSpinBox:
            self.keithley.set_nplc('b', sender.value() )
            
    def update_all_settings(self):
        """
        Read current state of all ui items and update keithley settings.
        """
        widgets = []
        widget_types = [QtWidgets.QDoubleSpinBox, QtWidgets.QComboBox]
        for widget_type in widget_types:
            widgets.extend(self.findChildren(widget_type))
        for widget in widgets:
            self.update_setting(calling_widget=widget)
    
if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::27::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600A_ui(myKeithley)
    ui.show()
    ui_app.exec()