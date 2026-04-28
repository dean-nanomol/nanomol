# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 11:59:27 2026

@author: reina
commands sent to arduino:
    on 
    off
    status
"""
import sys 
import time 
import serial

from PySide6.QtWidgets import(
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt
SERIAL_PORT = "COM5"
BAUD_RATE = 115200
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

def send_command(command):
    arduino.write((command + "\n").encode())
    
def turn_relay_on():
    send_command("on")
    status_label.setText("Command sent: ON")
    
def turn_relay_off():
    send_command("off")
    status_label.setText("Command sent: OFF")
    
    
def read_relay_status():
    send_command("status")
    time.sleep(0.2)
    response = arduino.readline().decode(errors="ignore").strip()
    if response == "":
        status_label.setText("No response received")
    else:
        status_label.setText(response)
        
def close_application():
    if arduino.is_open:
        arduino.close()
    
app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Relay Control")
window.setFixedSize(550, 500)

layout = QVBoxLayout()

on_button = QPushButton("ON")
on_button.setFixedSize(200, 35)
on_button.clicked.connect(turn_relay_on)
layout.addWidget(on_button, alignment=Qt.AlignCenter)

off_button = QPushButton("OFF")
off_button.setFixedSize(200, 35)
off_button.clicked.connect(turn_relay_off)
layout.addWidget(off_button, alignment=Qt.AlignCenter)

status_button = QPushButton("STATUS")
status_button.setFixedSize(200, 35)
status_button.clicked.connect(read_relay_status)
layout.addWidget(status_button, alignment=Qt.AlignCenter)

status_label = QLabel("Interface ready")
status_label.setAlignment(Qt.AlignCenter)
layout.addWidget(status_label)

window.setLayout(layout)
app.aboutToQuit.connect(close_application)
window.show()

sys.exit(app.exec())