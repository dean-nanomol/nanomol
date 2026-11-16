# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:39:43 2023

@author: deankos
"""

import os
import time
import threading
import traceback
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal
from nanomol.instruments.keithley_2600A import keithley_2600A
from nanomol.utils.interactive_ui import interactive_ui

class keithley_2600_LED_driver_ui(interactive_ui):
    """
    Keithley SMU used to drive an LED. 
    """
    
    # widgets can only be changed from the main thread, the LED threads request it with these signals
    LED_stopped_by_error_signal = pyqtSignal()
    LED_measured_signal = pyqtSignal(float, float)
    
    def __init__(self, smu):
        super().__init__()
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'keithley_2600_LED_driver.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.I_limit_doubleSpinBox.valueChanged.connect(self.set_I_limit)
        self.V_limit_doubleSpinBox.valueChanged.connect(self.set_V_limit)
        self.I_constant_current_doubleSpinBox.valueChanged.connect(self.set_I_constant_current)
        self.V_constant_voltage_doubleSpinBox.valueChanged.connect(self.set_V_constant_voltage)
        self.constant_current_radioButton.toggled.connect(self.set_smu_mode)
        self.constant_voltage_radioButton.toggled.connect(self.set_smu_mode)
        self.on_pushButton.toggled.connect(self.ON)
        self.off_pushButton.clicked.connect(self.OFF)
        self.toggle_pushButton.toggled.connect(self.toggle)
        self.LED_stopped_by_error_signal.connect(self.show_LED_off)
        self.LED_measured_signal.connect(self.show_LED_measurement)
        self.set_smu_mode()
        self.I_source_range_comboBox.currentTextChanged.connect(self.set_I_source_range)
        self.V_source_range_comboBox.currentTextChanged.connect(self.set_V_source_range)
        self.set_I_source_range()
        self.set_V_source_range()
        self.set_I_limit()
        self.set_V_limit()
        self.OFF()
        
    def set_I_limit(self):
        self.smu.set_source_limit('a', 'i', self.I_limit/1e+3)
        
    def set_V_limit(self):
        self.smu.set_source_limit('a', 'v', self.V_limit)
        
    def set_I_source_range(self):
        self.smu.set_source_range('a', 'i', self.I_source_range_comboBox.currentText() )
        self.smu.set_measure_range('a', 'i', self.I_source_range_comboBox.currentText() )
        
    def set_V_source_range(self):
        self.smu.set_source_range('a', 'v', self.V_source_range_comboBox.currentText() )
        self.smu.set_measure_range('a', 'v', self.V_source_range_comboBox.currentText() )
        
    def set_I_constant_current(self, I_constant_current):
        self.smu.set_source_level('a', 'i', I_constant_current/1e+3)
        
    def set_V_constant_voltage(self, V_constant_voltage):
        self.smu.set_source_level('a', 'v', V_constant_voltage)
    
    def set_smu_mode(self):
        if self.constant_current_radioButton.isChecked():
            self.smu.set_source_function('a', 0)
            self.mode = 'constant_current'
        elif self.constant_voltage_radioButton.isChecked():
            self.smu.set_source_function('a', 1)
            self.mode = 'constant_voltage'
    
    def ON(self, checked):
        # checked state is passed by pushButton. If toggled to unchecked state, turn OFF
        if checked:
            self.LED_is_running = True
            self.set_LED_output(1)
            measure_thread = threading.Thread(target=self.measure_thread)
            measure_thread.start()
        else:
            self.OFF()
        
    def set_LED_output(self, output):
        """
        output : int
            0 for OFF, 1 for ON
        self.output keeps the last output state set, so that it can be read, e.g. by experiments,
        without querying the smu from another thread.
        """
        self.smu.set_output('a', output)
        self.output = output
        
    def OFF(self):
        self.set_LED_output(0)
        self.LED_is_running = False
        self.on_pushButton.setChecked(False)
        self.toggle_pushButton.setChecked(False)
        self.i = 0
        self.v = 0
    
    def measure_thread(self, measure_interval=0.1):
        """
        Measure actual I and V output. Run as thread with values updated every measure_interval seconds.
        self.i, self.v contain the latest measured values.
        """
        error = None
        try:
            while self.LED_is_running:
                self.i, self.v = self.smu.measure('a', 'iv')
                self.LED_measured_signal.emit(self.i, self.v)
                time.sleep(measure_interval)
        except BaseException as exception:
            error = exception
            raise
        finally:
            # always runs, also when the thread is stopped by an error
            self.end_LED_thread(error)
    
    def show_LED_measurement(self, i, v):
        """
        Show the measured LED current and voltage. Runs in the main thread, called through LED_measured_signal.
        
        i : float
            measured current in A, shown in mA
        v : float
            measured voltage in V
        """
        self.measured_I_lineEdit.setText('{:.3f}'.format(i*1e+3))
        self.measured_V_lineEdit.setText('{:.4f}'.format(v))
    
    def toggle(self, checked):
        if checked:
            self.LED_is_running = True
            measure_thread = threading.Thread(target=self.measure_thread)
            toggle_thread = threading.Thread(target=self.toggle_thread)
            measure_thread.start()
            toggle_thread.start()
        else:
            self.OFF()
        
    def toggle_thread(self):
        error = None
        try:
            # LED_is_running is False after OFF(), or after an error in measure_thread
            while self.toggle_pushButton.isChecked() and self.LED_is_running:
                self.set_LED_output(1)
                time.sleep(self.toggle_ON_time)
                self.set_LED_output(0)
                time.sleep(self.toggle_OFF_time)
        except BaseException as exception:
            error = exception
            raise
        finally:
            # always runs, also when the thread is stopped by an error
            self.end_LED_thread(error)
    
    def end_LED_thread(self, error=None):
        """
        Called when measure_thread or toggle_thread ends. After an error, turns the LED output off and
        stops the other LED thread. Nothing is needed after a normal end, which is started by OFF().
        
        error : BaseException or None
            exception that stopped the thread. None if the thread ended normally.
        """
        if error is None:
            return
        self.LED_is_running = False  # stops the other LED thread
        try:
            self.set_LED_output(0)
        except Exception as exception:
            print('Error while turning off the LED:')
            traceback.print_exception(type(exception), exception, exception.__traceback__)
        self.i = 0
        self.v = 0
        self.LED_stopped_by_error_signal.emit()
    
    def show_LED_off(self):
        """
        Uncheck the ON and toggle buttons after the LED was turned off because of an error.
        Signals are blocked, so that ON() and toggle() are not called and the smu is not contacted again.
        """
        for button in [self.on_pushButton, self.toggle_pushButton]:
            button.blockSignals(True)
            button.setChecked(False)
            button.blockSignals(False)
            

if __name__ == '__main__' :
    
    myKeithley = keithley_2600A(address = 'GPIB0::26::INSTR')
    
    ui_app = QtWidgets.QApplication([])
    ui = keithley_2600_LED_driver_ui(myKeithley)
    ui.show()
    ui_app.exec()