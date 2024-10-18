# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 14:47:39 2023

@author: deankos
"""

import os
import numpy as np
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
        
    def get_compliance(self, ch):
        """
        ch : str
            channel, 'a' or 'b'

        Returns
        compliance : int
            source compliance state. 0: source not in compliance; 1: source in compliance
        """
        compliance_state = self.query('print(smu{}.source.compliance)'.format(ch))
        compliance_state = (compliance_state == 'true')
        return int(compliance_state)
                          
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

    def load_script(self, script, script_name=''):
        """
        script : list of str
            List of commands making up the script. Each list item is one valid command.
        script_name : str, optional
            Name assigned to script in instrument runtime environment. If script_name='' set as anonymous script.
        """
        self.write('loadscript {}'.format(script_name))
        for command in script:
            self.write(command)
        self.write('endscript')
        
    def run_script(self, script_name=None):
        """
        script_name : str, optional
            Name assigned to script in instrument runtime environment. If None, run the anonymous script.
        """
        if script_name is not None:
            self.write('{}.run()'.format(script_name))
        else:
            self.write('run()')
        
    def generate_linear_iv_sweep_script(self, sweep_ch, start_V, end_V, step_V, loop=False, secondary_ch=None):
        """
        sweep_ch : str
            channel, 'a' or 'b', where the sweep runs
        start_V : float
            sweep start voltage in V
        end_V : float
            sweep end voltage in V
        step_V : float
            sweep step in V
        loop : bool, optional
            if True, also runs the inverse sweep to do a loop sweep. The default is False.
        secondary_ch : str, optional
            channel, 'a' or 'b'. If given, records i and v measurements on this secondary channel in addition to those
            of sweep channel. secondary_ch should be different from sweep_ch. The default is None.

        Returns
        script : list of str
            List of TSP commands for a linear i-v sweep.
        """
        N_points = round( (end_V - start_V) / step_V ) +1
        script = []
        script.extend(
                ['smu{}.nvbuffer1.clear()'.format(sweep_ch),
                 'smu{}.nvbuffer2.clear()'.format(sweep_ch),
                 'smu{}.nvbuffer1.appendmode = 1'.format(sweep_ch),
                 'smu{}.nvbuffer2.appendmode = 1'.format(sweep_ch),
                 'smu{}.nvbuffer1.collectsourcevalues = 1'.format(sweep_ch),
                 'smu{}.nvbuffer2.collectsourcevalues = 1'.format(sweep_ch),
                 'smu{}.nvbuffer1.collecttimestamps = 1'.format(sweep_ch),
                 'smu{}.nvbuffer2.collecttimestamps = 1'.format(sweep_ch),
                 'smu{}.trigger.measure.iv(smu{}.nvbuffer1, smu{}.nvbuffer2)'.format(sweep_ch, sweep_ch, sweep_ch),
                 'smu{}.trigger.source.linearv({}, {}, {})'.format(sweep_ch, start_V, end_V, N_points),
                 'smu{}.trigger.source.action = 1'.format(sweep_ch),
                 'smu{}.trigger.measure.action = 1'.format(sweep_ch),
                 'smu{}.trigger.count = {}'.format(sweep_ch, N_points)
                 ])
        if secondary_ch is not None:
            script.extend(
                ['smu{}.nvbuffer1.clear()'.format(secondary_ch),
                 'smu{}.nvbuffer2.clear()'.format(secondary_ch),
                 'smu{}.nvbuffer1.appendmode = 1'.format(secondary_ch),
                 'smu{}.nvbuffer2.appendmode = 1'.format(secondary_ch),
                 'smu{}.nvbuffer1.collectsourcevalues = 1'.format(secondary_ch),
                 'smu{}.nvbuffer2.collectsourcevalues = 1'.format(secondary_ch),
                 'smu{}.nvbuffer1.collecttimestamps = 1'.format(secondary_ch),
                 'smu{}.nvbuffer2.collecttimestamps = 1'.format(secondary_ch),
                 'smu{}.trigger.measure.iv(smu{}.nvbuffer1, smu{}.nvbuffer2)'.format(secondary_ch, secondary_ch, secondary_ch),
                 'smu{}.trigger.measure.action = 1'.format(secondary_ch),
                 'smu{}.trigger.measure.stimulus = smu{}.trigger.SOURCE_COMPLETE_EVENT_ID'.format(secondary_ch, sweep_ch),
                 'smu{}.trigger.count = {}'.format(secondary_ch, N_points)
                 ])
        if loop:
            # if running a loop, maintain source voltage at the end of the forward sweep
            script.append('smu{}.trigger.endsweep.action = smu{}.SOURCE_HOLD'.format(sweep_ch, sweep_ch))
        else:
            # otherwise, turn it off
            script.append('smu{}.trigger.endsweep.action = smu{}.SOURCE_IDLE'.format(sweep_ch, sweep_ch))
        if secondary_ch is not None:
            script.extend(
                ['smu{}.source.output = 1'.format(secondary_ch),
                 'smu{}.trigger.initiate()'.format(secondary_ch)
                 ])
        script.extend(
                ['smu{}.source.output = 1'.format(sweep_ch),
                 'smu{}.trigger.initiate()'.format(sweep_ch),
                 'waitcomplete()',
                 'print(status.operation.sweeping.condition)',
                 ])
        if loop:
            # execute another sweep with inverted start_V and end_V
            script.extend(
                ['smu{}.trigger.source.linearv({}, {}, {})'.format(sweep_ch, end_V, start_V, N_points),
                 'smu{}.trigger.initiate()'.format(sweep_ch),
                 'waitcomplete()'
                 ])
        script.append('smu{}.source.output = 0'.format(sweep_ch))
        if secondary_ch is not None:
            script.append('smu{}.source.output = 0'.format(secondary_ch))
        return script
    
    def read_buffer(self, buffer_name, data_types):
        """
        buffer_name : str
            name of the buffer to be read, for example smua.nvbuffer1
        data_types : list of str
            reading buffer subtables to be read. Must include one or more of the following:
                'readings' : measured values
                'statuses' : equipment status for each reading
                'sourcevalues' : source value being output when readings were acquired
                'timestamps' : timestamp for each reading, relative to time of first reading
                
        Returns
        data_dict : dict
            dictionary keys are the data_types
        """
        data_size = len(data_types)
        data_buffers = ['{}.'.format(buffer_name) + d_type for d_type in data_types]
        data_buffers = ', '.join(data_buffers)
        buffer_content = self.query('printbuffer(1, {}.n, {})'.format(buffer_name, data_buffers) )
        # split instrument reply into list of str values
        buffer_content = buffer_content.split(', ')
        # instrument returns consecutive list of all data, with metadata immediately following each reading value
        data_dict = {}
        for i, d_type in enumerate(data_types):
            # take one item from list every data_size items to get all data of the same type
            data = buffer_content[i::data_size]
            data_dict[d_type] = np.array(data, dtype=float)
        return data_dict
    

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
    
    #myKeithley = keithley_2600A(address = 'GPIB0::27::INSTR')
    myKeithley = keithley_2600A(address = 'USB0::0x05E6::0x2604::4101847::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600A_ui(myKeithley)
    ui.show()
    ui_app.exec()