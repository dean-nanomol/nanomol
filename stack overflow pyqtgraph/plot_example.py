import random
import threading
import time
import os
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic

class plot_test(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        ui_file_path = os.path.join(os.path.dirname(__file__), 'current_vs_time.ui')
        uic.loadUi(ui_file_path, self)
        self.start_pushButton.clicked.connect(self.start_measurement)
        self.stop_pushButton.clicked.connect(self.stop_measurement)
        self.setup_plot_widgets()
        self.measurement_is_running = False
        
    def start_measurement(self):
        if not self.measurement_is_running:
            self.measurement_is_running = True
            measurement_thread = threading.Thread(target=self.run_measurement)
            measurement_thread.start()
            
    def stop_measurement(self):
        if self.measurement_is_running:
            self.measurement_is_running = False
            
    def run_measurement(self):
        self.data = {'time': [], 'voltage': []  }
        self.clear_plots()
        self.create_plot_lines()
        t0 = time.time()
        t = 0
        while self.measurement_is_running:
            v = random.randint(0,9)
            self.data['time'].append(t)
            self.data['voltage'].append(v)
            self.update_plots()
            t = time.time() - t0
            time.sleep(0.1)
    
    def setup_plot_widgets(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_layout.replaceWidget(self.placeholder_plot, self.plot_widget)
        # self.voltage_vs_time.setBackground('w')
        # self.voltage_vs_time.setLabel('bottom', 'time [s]', color='black')
        # self.voltage_vs_time.setLabel('left', 'voltage', color='black')

    def clear_plots(self):
        self.plot_widget.clear()
        
    def create_plot_lines(self):
        self.voltage_vs_time_line = self.plot_widget.plot(self.data['time'], self.data['voltage'] )
    
    def update_plots(self):
        self.voltage_vs_time_line.setData(self.data['time'], self.data['voltage'] )
        
if __name__ == '__main__' :
    experiment_app = QtWidgets.QApplication([])
    experiment = plot_test()
    experiment.show()
    experiment_app.exec()