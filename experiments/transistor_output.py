# -*- coding: utf-8 -*-
"""
Created on Tue May 21 17:12:59 2024

@author: deankos
"""

import numpy as np
import threading
import time
import os
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.utils.interactive_ui import interactive_ui

class transistor_output(interactive_ui):
    """
    Class for measurement of transistor output curves.
    "sweep" refers to the outer voltage loop, V_GS.
    "curve" refers to the inner voltage loop, V_DS.
    Data can only be saved if an hdf5_datafile object is passed upon object creation.
    Data plotting and saving can be turned on/off.
    """
    
    update_plots_signal = pyqtSignal()
    
    def __init__(self,smu,  datafile=None):
        super().__init__()
        if datafile is not None:
            self.datafile = datafile
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'transistor_output.ui')
        uic.loadUi(ui_file_path, self)
        # set gate-source and drain-source channels
        self.connect_widgets_by_name()
        self.start_pushbutton.clicked.connect(self.start_measurement)
        self.stop_pushbutton.clicked.connect(self.stop_measurement)
        self.sweep_one_way_radioButton.clicked.connect(self.set_sweep_loop)
        self.sweep_loop_radioButton.clicked.connect(self.set_sweep_loop)
        self.curve_one_way_radioButton.clicked.connect(self.set_curve_loop)
        self.curve_loop_radioButton.clicked.connect(self.set_curve_loop)
        self.sweep_direction_positive_radioButton.clicked.connect(self.set_sweep_direction)
        self.sweep_direction_negative_radioButton.clicked.connect(self.set_sweep_direction)
        self.curve_direction_positive_radioButton.clicked.connect(self.set_curve_direction)
        self.curve_direction_negative_radioButton.clicked.connect(self.set_curve_direction)
        self.plot_widgets_set_up = False
        self.set_measurement_mode()
        self.setup_plot_widgets()
        self.update_plots_signal.connect(self.update_plots)
        self.set_sweep_direction()  # sweep is the external loop, V1
        self.set_sweep_loop()
        self.set_curve_direction()  # curve is the internal loop, V2
        self.set_curve_loop()
        self.measurement_is_running = False  # flag to start and stop a measurement
    
    def start_measurement(self):
        if not self.measurement_is_running:  # do nothing if measurement is already running
            self.measurement_is_running = True
            measurement_thread = threading.Thread(target=self.run_measurement)
            measurement_thread.start()
            
    def stop_measurement(self):
        if self.measurement_is_running:
            self.measurement_is_running = False
            
    def run_measurement(self):
        self.configure_measurement()
        self.clear_plots()
        # set channels to start from first point when output is turned on
        self.V1_active = self.V1[0]
        self.smu.set_source_level(self.V1_ch, 'v', self.V1_active)
        self.color_index = 0
        self.smu.set_output(self.V1_ch, 1)
        for self.measurement_counter in range(self.N_measurements):
            for self.V1_active in self.V1:
                if self.save_data_checkBox.isChecked():
                    self.save_curve_attrs()
                # reset curve datasets for new curve
                self.initialise_datasets()
                self.smu.set_source_level(self.V1_ch, 'v', self.V1_active)
                self.V2_active = self.V2[0]
                self.smu.set_source_level(self.V2_ch, 'v', self.V2_active)
                # prepare new plot line for upcoming data
                if self.live_plotting_checkBox.isChecked():
                    self.create_new_plot_lines()
                self.color_index += 1
                self.smu.set_output(self.V2_ch, 1)
                if self.first_point_delay != 0:
                    time.sleep(self.first_point_delay)
                t0 = time.time()
                for self.V2_active in self.V2:
                    self.smu.set_source_level(self.V2_ch, 'v', self.V2_active)
                    measured_I1, measured_V1 = self.smu.measure(self.V1_ch, 'iv')
                    measured_I2, measured_V2 = self.smu.measure(self.V2_ch, 'iv')
                    compliance_V1 = self.smu.get_compliance(self.V1_ch)
                    compliance_V2 = self.smu.get_compliance(self.V2_ch)
                    self.data[self.dataset_labels['time']].append(time.time() - t0)
                    self.data[self.dataset_labels['measured_V1']].append(measured_V1)
                    self.data[self.dataset_labels['measured_I1']].append(measured_I1)
                    self.data[self.dataset_labels['measured_V2']].append(measured_V2)
                    self.data[self.dataset_labels['measured_I2']].append(measured_I2)
                    self.data[self.dataset_labels['calculated_V1']].append(self.V1_active)
                    self.data[self.dataset_labels['calculated_V2']].append(self.V2_active)
                    self.data[self.dataset_labels['compliance_V1']].append(compliance_V1)
                    self.data[self.dataset_labels['compliance_V2']].append(compliance_V2)
                    if self.live_plotting_checkBox.isChecked():
                        self.update_plots_signal.emit()
                    if not self.measurement_is_running:
                        break
                    if self.delay_points != 0:
                        time.sleep(self.delay_points)
                self.smu.set_output(self.V2_ch, 0)
                if self.save_data_checkBox.isChecked():
                    self.save_data()
                if not self.measurement_is_running:
                    break
                if self.delay_curves != 0:
                    time.sleep(self.delay_curves)
        self.smu.set_output(self.V1_ch, 0)
        self.measurement_is_running = False
            
    def configure_measurement(self):
        """
        Define voltages to apply, save instrument settings and basic attributes.
        """
        self.smu.set_source_function('a', 1)
        self.smu.set_source_function('b', 1)
        self.V1_ch, self.V2_ch = self.ch_GS, self.ch_DS
        self.V1 = np.arange(self.V_GS_min_output, self.V_GS_max_output + self.V_GS_step_output, self.V_GS_step_output)
        self.V2 = np.arange(self.V_DS_min_output, self.V_DS_max_output + self.V_DS_step_output, self.V_DS_step_output)
        self.dataset_labels = {
            'time' : 'time',
            'measured_V1' : 'measured_V_{}'.format(self.V1_label),
            'measured_I1' : 'measured_I_{}'.format(self.V1_label),
            'measured_V2' : 'measured_V_{}'.format(self.V2_label),
            'measured_I2' : 'measured_I_{}'.format(self.V2_label),
            'calculated_V1' : 'calculated_V_{}'.format(self.V1_label),
            'calculated_V2' : 'calculated_V_{}'.format(self.V2_label),
            'compliance_V1' : 'compliance_V_{}'.format(self.V1_label),
            'compliance_V2' : 'compliance_V_{}'.format(self.V2_label) }
        if self.sweep_direction == -1:
            self.V1 = np.flip(self.V1)
        if self.sweep_loop:
            self.V1 = np.append(self.V1, np.flip(self.V1) )
        if self.curve_direction == -1:
            self.V2 = np.flip(self.V2)
        if self.curve_loop:
            self.V2 = np.append(self.V2, np.flip(self.V2) )
        # save measurement settings and attributes
        if self.save_data_checkBox.isChecked():
            self.save_sweep_attrs()
    
    def initialise_datasets(self):
        # initialise all datasets with empty lists
        self.data = {}
        for label in self.dataset_labels.values():
            self.data[label] = []
            
    def save_sweep_attrs(self):
        active_sweep_name = self.datafile.get_unique_group_name(self.datafile, basename='sweep', max_N=1000)
        self.active_sweep_group =  self.datafile.create_group(active_sweep_name)
        self.active_sweep_group.attrs.create('description', self.description)
        self.active_sweep_group.attrs.create('measurement_mode', self.measurement_mode)
        self.active_sweep_group.attrs.create('GS_channel', self.ch_GS)
        self.active_sweep_group.attrs.create('DS_channel', self.ch_DS)
        for key, value in self.smu.get_settings().items():
            self.active_sweep_group.attrs.create('keithley_{}'.format(key), value)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()) )
        self.active_sweep_group.attrs.create('timestamp', timestamp )
    
    def save_curve_attrs(self):
        active_curve_name = self.datafile.get_unique_group_name(self.active_sweep_group, basename='curve')
        self.active_curve_group = self.active_sweep_group.create_group(active_curve_name)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()) )
        self.active_curve_group.attrs.create('timestamp', timestamp )
        self.active_curve_group.attrs.create('V_{}'.format(self.V1_label), data=self.V1_active)
        self.active_curve_group.attrs.create('measurement_counter', data=self.measurement_counter)
        
    def save_data(self):
        # write data to hdf5 datafile
        for dataset_name, data in self.data.items():
            if dataset_name == 'time':  # shift time to start from zero
                data = np.array(data)
                data -= data[0]
            self.active_curve_group.create_dataset(dataset_name, data=np.array(data) )
        self.datafile.flush()
    
    def set_measurement_mode(self):
        self.measurement_mode = 'output'
        self.V1_label, self.V2_label = 'GS', 'DS'
        if self.plot_widgets_set_up:
            self.set_plot_labels()
            
    def set_sweep_direction(self):
        if self.sweep_direction_positive_radioButton.isChecked():
            self.sweep_direction = 1
        elif self.sweep_direction_negative_radioButton.isChecked():
            self.sweep_direction = -1
    
    def set_sweep_loop(self):
        if self.sweep_one_way_radioButton.isChecked():
            self.sweep_loop = False
        elif self.sweep_loop_radioButton.isChecked():
            self.sweep_loop = True
    
    def set_curve_direction(self):
        if self.curve_direction_positive_radioButton.isChecked():
            self.curve_direction = 1
        elif self.curve_direction_negative_radioButton.isChecked():
            self.curve_direction = -1
    
    def set_curve_loop(self):
        if self.curve_one_way_radioButton.isChecked():
            self.curve_loop = False
        elif self.curve_loop_radioButton.isChecked():
            self.curve_loop = True
        
    def setup_plot_widgets(self):
        # plots occasionally freeze, use this to reset
        self.plot_layout.removeWidget(self.I1_vs_V2)
        self.plot_layout.removeWidget(self.I2_vs_V2)
        self.I1_vs_V2.deleteLater()
        self.I2_vs_V2.deleteLater()
        self.I1_vs_V2 = None
        self.I2_vs_V2 = None
        self.I2_vs_V2 = pg.PlotWidget()
        self.I1_vs_V2 = pg.PlotWidget()
        self.plot_layout.addWidget(self.I2_vs_V2)
        self.plot_layout.addWidget(self.I1_vs_V2)
        self.I2_vs_V2.setBackground('w')
        self.I1_vs_V2.setBackground('w')
        self.plot_widgets_set_up = True
        self.set_plot_labels()
        
    def clear_plots(self):
        self.I2_vs_V2.clear()
        self.I1_vs_V2.clear()
    
    def set_plot_labels(self):
        # setting labels when measurement thread is already running seems to crash the program
        # likely because Qt objects can't be accessed from a thread other than where they were created
        self.I2_vs_V2.setLabel('bottom', 'V_{} [V]'.format(self.V2_label) )
        self.I2_vs_V2.setLabel('left', 'I_{} [A]'.format(self.V2_label) )
        self.I1_vs_V2.setLabel('bottom', 'V_{} [V]'.format(self.V2_label) )
        self.I1_vs_V2.setLabel('left', 'I_{} [A]'.format(self.V1_label) )
        self.I2_vs_V2.addLegend()
        self.I1_vs_V2.addLegend()
        
    def create_new_plot_lines(self):
        color = pg.intColor(self.color_index, hues=self.V1.size*self.N_measurements)
        pen = pg.mkPen(color=color)
        self.I2_vs_V2_line = self.I2_vs_V2.plot(self.data[self.dataset_labels['measured_V2']],
                                                self.data[self.dataset_labels['measured_I2']],
                                                pen=pen, name='V_{}={}'.format(self.V1_label, self.V1_active) )
        self.I1_vs_V2_line = self.I1_vs_V2.plot(self.data[self.dataset_labels['measured_V2']],
                                                self.data[self.dataset_labels['measured_I1']],
                                                pen=pen, name='V_{}={}'.format(self.V1_label, self.V1_active) )
        
    def update_plots(self):
        self.I2_vs_V2_line.setData(self.data[self.dataset_labels['measured_V2']],
                                   self.data[self.dataset_labels['measured_I2']] )
        self.I1_vs_V2_line.setData(self.data[self.dataset_labels['measured_V2']],
                                   self.data[self.dataset_labels['measured_I1']] )
    
    def shutdown(self):
        self.datafile.close()
        self.smu.close()
    
        
if __name__ == '__main__' :
    
    from nanomol.utils.hdf5_datafile import hdf5_datafile
    from nanomol.utils.hdf5_viewer import hdf5_viewer
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('USB0::0x05E6::0x2604::4101847::INSTR')
    
    experiment_app = QtWidgets.QApplication([])
    
    experiment = transistor_output(smu, datafile=datafile)
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    experiment.show()
    smu_ui.show()
    datafile_viewer.show()
    
    experiment_app.exec()
    