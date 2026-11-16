# -*- coding: utf-8 -*-
"""
Created on Mon Sep  4 17:50:35 2023

@author: deankos
"""

import numpy as np
import threading
import time
import traceback
import os
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal
import pyqtgraph as pg
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.instruments.keithley_2600_LED_driver import keithley_2600_LED_driver_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class current_vs_time_LED(interactive_ui):
    """
    Class to measure transistor output over time. Set V_GS and V_DS and start measurement.
    Measurements always record time and measured V and I values for both channels.
    Run measurement until the time limit, or set time limit to -1 to run indefinitely.
    """
    
    update_plots_signal = pyqtSignal()
    # plots can only be modified from the main thread, the measurement thread requests it with these signals
    clear_plots_signal = pyqtSignal()
    create_new_plot_lines_signal = pyqtSignal()
    
    def __init__(self, datafile, smu, LED):
        super().__init__()
        self.datafile = datafile
        self.smu = smu
        self.LED = LED
        ui_file_path = os.path.join(os.path.dirname(__file__), 'current_vs_time_LED.ui')
        uic.loadUi(ui_file_path, self)
        self.connect_widgets_by_name()
        self.start_pushbutton.clicked.connect(self.start_measurement)
        self.stop_pushbutton.clicked.connect(self.stop_measurement)
        self.shutdown_pushbutton.clicked.connect(self.shutdown)
        self.update_plots_signal.connect(self.update_plots)
        self.clear_plots_signal.connect(self.clear_plots)
        self.create_new_plot_lines_signal.connect(self.create_new_plot_lines)
        self.setup_plot_widgets()
        self.measurement_is_running = False
        
    def start_measurement(self):
        if not self.measurement_is_running:  # do nothing if measurement is already running
            self.measurement_is_running = True
            measurement_thread = threading.Thread(target=self.run_measurement)
            measurement_thread.start()
            
    def stop_measurement(self):
        if self.measurement_is_running:
            self.measurement_is_running = False
            
    def run_measurement(self):
        # used by end_measurement() to know which outputs to turn off and whether there is data to save
        self.channels_in_use = [self.ch_GS, self.ch_DS]
        self.unsaved_data = False
        error = None
        try:
            self.clear_plots_signal.emit()
            self.configure_measurement()
            self.unsaved_data = True
            self.create_new_plot_lines_signal.emit()
            self.smu.set_source_level(self.ch_GS, 'v', self.V_GS)
            self.smu.set_source_level(self.ch_DS, 'v', self.V_DS)
            active_V_GS = self.V_GS
            active_V_DS = self.V_DS
            t0 = time.time()
            t = 0
            self.smu.set_output(self.ch_GS, 1)
            self.smu.set_output(self.ch_DS, 1)
            while self.measurement_is_running:
                if t > self.t_limit:
                    self.measurement_is_running = False
                if self.V_GS != active_V_GS:
                    # set voltage only if changed
                    self.smu.set_source_level(self.ch_GS, 'v', self.V_GS)
                if self.V_DS != active_V_DS:
                    self.smu.set_source_level(self.ch_DS, 'v', self.V_DS)
                measured_I_GS, measured_V_GS = self.smu.measure(self.ch_GS, 'iv')
                measured_I_DS, measured_V_DS = self.smu.measure(self.ch_DS, 'iv')
                if self.use_LED_checkBox.isChecked():
                    LED_output = self.LED.output  # last state set by the LED driver, not queried from the smu
                    measured_LED_I = self.LED.i
                    measured_LED_V = self.LED.v
                    self.data['LED_output'].append(LED_output)
                    self.data['measured_LED_current'].append(measured_LED_I)
                    self.data['measured_LED_voltage'].append(measured_LED_V)
                self.data['time'].append(t)
                self.data['V_GS'].append(measured_V_GS)
                self.data['I_GS'].append(measured_I_GS)
                self.data['V_DS'].append(measured_V_DS)
                self.data['I_DS'].append(measured_I_DS)
                self.update_plots_signal.emit()
                t = time.time() - t0
        except BaseException as exception:
            error = exception
            raise
        finally:
            # always runs, also when the measurement is stopped by an error
            self.end_measurement(error)
        
    def end_measurement(self, error=None):
        """
        Called at the end of every measurement, also when the measurement is stopped by an error.
        Turns off the smu outputs and saves the data measured. After an error, the error message is saved
        as attribute 'error' of the data group. Each step is attempted even if the previous one fails.
        The LED is not changed: it is controlled from the LED driver window.
        
        error : BaseException or None
            exception that stopped the measurement. None if it ended normally or was stopped by the user.
        """
        cleanup_errors = []
        for ch in self.channels_in_use:
            try:
                self.smu.set_output(ch, 0)
            except Exception as exception:
                cleanup_errors.append(exception)
        if self.unsaved_data:
            # set before saving, so that data is not saved twice
            self.unsaved_data = False
            try:
                self.save_data(error)
            except Exception as exception:
                cleanup_errors.append(exception)
        self.measurement_is_running = False
        for exception in cleanup_errors:
            print('Error while ending the measurement:')
            traceback.print_exception(type(exception), exception, exception.__traceback__)
        if len(cleanup_errors) > 0 and error is None:
            # no other error is being raised: raise one, so that whoever started the measurement knows
            raise RuntimeError('measurement did not end correctly, see the errors printed above') from cleanup_errors[0]
        
    def configure_measurement(self):
        self.smu.set_source_function('a', 1)
        self.smu.set_source_function('b', 1)
        self.initialise_datasets()
        if self.t_limit == -1:
            self.t_limit = np.inf
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()) )
        
    def initialise_datasets(self):
        self.data = {'time': [],
                     'V_GS': [],
                     'I_GS': [],
                     'V_DS': [],
                     'I_DS': []  }
        if self.use_LED_checkBox.isChecked():
            self.data.update({'LED_output': [],
                              'measured_LED_current': [],
                              'measured_LED_voltage': [] })
        
    def save_data(self, error=None):
        """
        write data to hdf5 datafile
        
        error : BaseException, optional
            exception that stopped the measurement, saved as attribute 'error' of the data group
        """
        active_group = self.datafile.get_unique_group_name(self.datafile, basename=self.description, max_N=100)
        self.active_group =  self.datafile.create_group(active_group)
        self.active_group.attrs.create('description', self.description)
        self.active_group.attrs.create('timestamp', self.timestamp)
        self.active_group.attrs.create('channel_GS', self.ch_GS)
        self.active_group.attrs.create('channel_DS', self.ch_DS)
        if error is not None:
            self.active_group.attrs.create('error', ''.join(traceback.format_exception(type(error), error, error.__traceback__)))
        for dataset_name, data in self.data.items():
            self.active_group.create_dataset(dataset_name, data=np.array(data) )
        self.datafile.flush()
        # smu settings are read last, so that the data is already saved if the smu does not respond
        for key, value in self.smu.get_settings().items():
            self.active_group.attrs.create('keithley_{}'.format(key), value)
        self.datafile.flush()
    
    def setup_plot_widgets(self):
        self.plot_layout.removeWidget(self.I_DS_vs_time)
        self.plot_layout.removeWidget(self.I_GS_vs_time)
        self.I_DS_vs_time.deleteLater()
        self.I_GS_vs_time.deleteLater()
        self.I_GS_vs_time = None
        self.I_DS_vs_time = None
        self.I_GS_vs_time = pg.PlotWidget()
        self.I_DS_vs_time = pg.PlotWidget()
        self.plot_layout.addWidget(self.I_GS_vs_time)
        self.plot_layout.addWidget(self.I_DS_vs_time)
        self.I_GS_vs_time.setBackground('w')
        self.I_DS_vs_time.setBackground('w')
        self.I_DS_vs_time.setLabel('bottom', 'time [s]', color='black')
        self.I_DS_vs_time.setLabel('left', 'I_DS [A]', color='black')
        self.I_GS_vs_time.setLabel('left', 'I_GS [A]', color='black')

    def clear_plots(self):
        self.I_GS_vs_time.clear()
        self.I_DS_vs_time.clear()
        
    def create_new_plot_lines(self):
        pen_I = pg.mkPen(color='r')
        self.I_GS_vs_time_line = self.I_GS_vs_time.plot(self.data['time'], self.data['I_GS'], pen=pen_I )
        self.I_DS_vs_time_line = self.I_DS_vs_time.plot(self.data['time'], self.data['I_DS'], pen=pen_I )
    
    def update_plots(self):
        self.I_GS_vs_time_line.setData(self.data['time'], self.data['I_GS'] )
        self.I_DS_vs_time_line.setData(self.data['time'], self.data['I_DS'] )
    
    def shutdown(self):
        self.datafile.close()
        self.smu.close()
        
if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('GPIB0::27::INSTR')
    LED_smu = keithley_2600A('GPIB0::26::INSTR')
    
    experiment_app = QtWidgets.QApplication([])
    
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    LED_ui = keithley_2600_LED_driver_ui(LED_smu)
    experiment = current_vs_time_LED(datafile, smu, LED_ui)
 
    smu_ui.show()
    LED_ui.show()
    datafile_viewer.show()
    experiment.show()
    
    experiment_app.exec()