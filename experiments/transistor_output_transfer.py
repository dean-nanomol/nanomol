# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 12:02:09 2023

@author: deankos
"""

import numpy as np
import threading
import time
import os
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic
from nanomol.instruments.keithley_2600A import keithley_2600A, keithley_2600A_ui
from nanomol.utils.interactive_ui import interactive_ui
from nanomol.utils.hdf5_datafile import hdf5_datafile
from nanomol.utils.hdf5_viewer import hdf5_viewer

class transistor_output_transfer(interactive_ui):
    
    def __init__(self, datafile, smu):
        super().__init__()
        self.datafile = datafile
        self.smu = smu
        ui_file_path = os.path.join(os.path.dirname(__file__), 'transistor_output_transfer.ui')
        uic.loadUi(ui_file_path, self)
        # set gate-source and drain-source channels
        self.smu_channels = {'GS': 'a', 'DS': 'b'}
        self.connect_widgets_by_name()
        self.output_mode_radiobutton.clicked.connect(self.set_measurement_mode)
        self.transfer_mode_radiobutton.clicked.connect(self.set_measurement_mode)
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
        self.set_measurement_mode()
        self.set_sweep_direction()  # sweep is the external loop, V1
        self.set_sweep_loop()
        self.set_curve_direction()  # curve is the internal loop, V2
        self.set_curve_loop()
        self.setup_plot_widgets()
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
        self.reset_plots()
        self.configure_measurement()
        # set channels to start from first point when output is turned on
        self.V1_active = self.V1[0]
        self.smu.set_source_level(self.V1_ch, 'v', self.V1_active)
        self.color_index = 0
        self.smu.set_output(self.V1_ch, 1)
        for self.V1_active in self.V1:
            active_curve_name = self.datafile.get_unique_group_name(self.active_sweep_group, basename='curve')
            self.active_curve_group = self.active_sweep_group.create_group(active_curve_name)
            self.active_curve_group.attrs.create('V_{}'.format(self.V1_label), data=self.V1_active)
            # reset curve datasets for new curve
            self.initialise_datasets()
            self.smu.set_source_level(self.V1_ch, 'v', self.V1_active)
            self.V2_active = self.V2[0]
            self.smu.set_source_level(self.V2_ch, 'v', self.V2_active)
            # prepare new plot line for upcoming data
            self.create_new_plot_lines()
            self.color_index += 1
            t0 = time.time()
            self.smu.set_output(self.V2_ch, 1)
            for self.V2_active in self.V2:
                self.smu.set_source_level(self.V2_ch, 'v', self.V2_active)
                measured_I1, measured_V1 = self.smu.measure(self.V1_ch, 'iv')
                measured_I2, measured_V2 = self.smu.measure(self.V2_ch, 'iv')
                self.data['time'].append(time.time() - t0)
                self.data['measured_V1'].append(measured_V1)
                self.data['measured_I1'].append(measured_I1)
                self.data['measured_V2'].append(measured_V2)
                self.data['measured_I2'].append(measured_I2)
                self.update_plots()
                if not self.measurement_is_running:
                    break
                if self.delay_points != 0:
                    time.sleep(self.delay_points)
            self.smu.set_output(self.V2_ch, 0)
            self.save_data()
            if not self.measurement_is_running:
                break
            if self.delay_curves != 0:
                time.sleep(self.delay_curves)
        self.smu.set_output(self.V1_ch, 0)
        self.measurement_is_running = False
            
    
    def configure_measurement(self):
        """
        Set output/transfer measurement type, define voltages to apply, save instrument settings and basic attributes.
        """
        active_sweep_name = self.datafile.get_unique_group_name(self.datafile, basename='sweep', max_N=1000)
        self.active_sweep_group =  self.datafile.create_group(active_sweep_name)
        self.smu.set_source_function('a', 1)
        self.smu.set_source_function('b', 1)
        if self.measurement_mode == 'output':
            self.V1_ch, self.V2_ch = self.smu_channels['GS'], self.smu_channels['DS']
            self.V1_label, self.V2_label = 'GS', 'DS'
            self.V1 = np.arange(self.V_GS_min_output, self.V_GS_max_output + self.V_GS_step_output, self.V_GS_step_output)
            self.V2 = np.arange(self.V_DS_min_output, self.V_DS_max_output + self.V_DS_step_output, self.V_DS_step_output)
        elif self.measurement_mode == 'transfer':
            self.V1_ch, self.V2_ch = self.smu_channels['DS'], self.smu_channels['GS']
            self.V1_label, self.V2_label = 'DS', 'GS'
            self.V1 = np.arange(self.V_DS_min_transfer, self.DS_max_transfer + self.V_DS_step_transfer, self.V_DS_step_transfer)
            self.V2 = np.arange(self.V_GS_min_transfer, self.GS_max_transfer + self.V_GS_step_transfer, self.V_GS_step_transfer)
        if self.sweep_direction == -1:
            self.V1 = np.flip(self.V1)
        if self.sweep_loop:
            self.V1 = np.append(self.V1, np.flip(self.V1) )
        if self.curve_direction == -1:
            self.V2 = np.flip(self.V2)
        if self.curve_loop:
            self.V2 = np.append(self.V2, np.flip(self.V2) )
        # save measurement settings and attributes
        self.active_sweep_group.attrs.create('description', self.description)
        self.active_sweep_group.attrs.create('measurement_mode', self.measurement_mode)
        for key, value in self.smu.get_settings().items():
            self.active_sweep_group.attrs.create('keithley_{}'.format(key), value)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()) )
        self.active_sweep_group.attrs.create('timestamp', timestamp )
    
    def initialise_datasets(self):
        self.data = {'time':[],
                     'measured_V1':[],
                     'measured_I1':[],
                     'measured_V2':[],
                     'measured_I2':[]  }
        
    def save_data(self):
        """ write data to hdf5 datafile """
        for dataset_name, data in self.data.items():
            dataset_name = dataset_name.replace('1', '_{}'.format(self.V1_label) )
            dataset_name = dataset_name.replace('2', '_{}'.format(self.V2_label) )
            if dataset_name == 'time':  # shift time to start from zero
                data = np.array(data)
                data -= data[0]
            self.active_curve_group.create_dataset(dataset_name, data=np.array(data) )
        self.datafile.flush()
    
    def set_measurement_mode(self):
        if self.output_mode_radiobutton.isChecked():
            self.measurement_mode = 'output'
        elif self.transfer_mode_radiobutton.isChecked():
            self.measurement_mode = 'transfer'
            
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
        self.V1_iv_plot = pg.PlotWidget()
        self.V1_time_plot = pg.PlotWidget()
        self.V2_iv_plot = pg.PlotWidget()
        self.V2_time_plot = pg.PlotWidget()
        self.plot_layout.replaceWidget(self.plot_placeholder_1, self.V1_iv_plot)
        self.plot_layout.replaceWidget(self.plot_placeholder_2, self.V1_time_plot)
        self.plot_layout.replaceWidget(self.plot_placeholder_3, self.V2_iv_plot)
        self.plot_layout.replaceWidget(self.plot_placeholder_4, self.V2_time_plot)
        self.V1_iv_plot.setBackground('w')
        self.V1_time_plot.setBackground('w')
        self.V2_iv_plot.setBackground('w')
        self.V2_time_plot.setBackground('w')
        
        
    def reset_plots(self):
        self.V1_iv_plot.clear()
        self.V1_time_plot.clear()
        self.V2_iv_plot.clear()
        self.V2_time_plot.clear()
        
    def create_new_plot_lines(self):
        color = pg.intColor(self.color_index, hues=self.V1.size)
        self.active_plot_lines = {
            'V1_iv': self.V1_iv_plot.plot(self.data['measured_V1'], self.data['measured_I1'], pen=pg.mkPen(color=color) ),
            'V1_time': self.V1_time_plot.plot(self.data['time'], self.data['measured_I1'], pen=pg.mkPen(color=color) ),
            'V2_iv': self.V2_iv_plot.plot(self.data['measured_V2'], self.data['measured_I2'], pen=pg.mkPen(color=color) ),
            'V2_time': self.V2_time_plot.plot(self.data['time'], self.data['measured_I2'], pen=pg.mkPen(color=color) )
            }
        
    def update_plots(self):
        self.active_plot_lines['V1_iv'].setData(self.data['measured_V1'], self.data['measured_I1'])
        self.active_plot_lines['V1_time'].setData(self.data['time'], self.data['measured_I1'])
        self.active_plot_lines['V2_iv'].setData(self.data['measured_V2'], self.data['measured_I2'])
        self.active_plot_lines['V2_time'].setData(self.data['time'], self.data['measured_I2'])
        
            
    def shutdown(self):
        self.datafile.close()
        self.smu.close()
    
        
if __name__ == '__main__' :
    
    datafile = hdf5_datafile(mode='x')
    smu = keithley_2600A('GPIB0::27::INSTR')
    
    experiment_app = QtWidgets.QApplication([])
    
    experiment = transistor_output_transfer(datafile, smu)
    datafile_viewer = hdf5_viewer(datafile)
    smu_ui = keithley_2600A_ui(smu)
    experiment.show()
    smu_ui.show()
    datafile_viewer.show()
    
    experiment_app.exec()
    