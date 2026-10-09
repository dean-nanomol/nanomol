# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 16:12:12 2026

@author: deankos

Available commands:

    on <pin_number>     Turn ON pin <pin_number>
    off <pin_number>    Turn OFF pin <pin_number>
    off all             Turn all pins OFF
    status?             Read the state of all 25 pins

"""

import os
import sys
from PyQt5 import QtWidgets, uic
from nanomol.instruments import serial_instrument
from nanomol.utils import interactive_ui

class arduino_multiplexer_3_to_12_12_1(serial_instrument):
    """
    Instrument class for the Arduino-controlled relay multiplexer.

    It translates Python method calls into Arduino serial commands:
    - on <pin_number>
    - off <pin_number>
    - off all
    - status
    """

    def __init__(self, port):
        settings = {'baudrate': 115200,
                    'timeout': 1 }
        termination = '\n'
        super().__init__(port=port, port_settings=settings, termination_character=termination)

    def set_pin_state(self, pin_number, state):
        """
        Turn one pin ON or OFF
        """
        if state:
            self.write('on {:d}'.format(pin_number))
        else:
            self.write('off {:d}'.format(pin_number))

    def off_all(self):
        """
        Turn all 25 pins OFF
        """
        self.write('off all')

    def status(self):
        """
        Returns
        status : string
            status (0: OFF, 1: ON) of each pin, as a string of 25 digits.

        Example: if only pins 1 and 4 are ON, returns:
        10010...0
        """
        return self.query('status?')


class arduino_multiplexer_3_to_12_12_1_ui(interactive_ui):
    def __init__(self, multiplexer):
        super().__init__()
        self.multiplexer = multiplexer

        ui_file_path = os.path.join(os.path.dirname(__file__), 'arduino_multiplexer_3_to_12_12_1.ui')
        uic.loadUi(ui_file_path, self)
        
        # Store the checkbox objects in their physical pin order.
        # Index 0 represents pin 1, index 1 represents pin 2, and so on.

        self.pin_checkboxes = []

        # Automatically connect the 25 pin checkboxes.
        # The object names in Qt Designer must be:
        # ch_1_pin_01_checkBox, ch_1_pin_02_checkBox...

        for pin_number in range(1, 26):
            checkbox_name = f"ch_1_pin_{pin_number:02d}_checkBox"
            checkbox = getattr(self, checkbox_name)

            checkbox.setText(f"ch_1_pin_{pin_number:02d}")
            checkbox.stateChanged.connect(self.pin_state_changed)

            self.pin_checkboxes.append(checkbox)

        self.all_off_pushButton.clicked.connect(self.turn_off_all_pins)
        self.read_status_pushButton.clicked.connect(self.read_status)

        self.status_lineEdit.setText("Connected")
        self.update_selected_pins_display()

    def pin_state_changed(self, checked):
        """
        Respond when the user checks or unchecks a pin checkbox.

        The function identifies which checkbox produced the signal,
        converts its position into a pin number, and sends the appropriate
        ON or OFF command to the Arduino.
        """

        checkbox = self.sender()
        pin_number = self.pin_checkboxes.index(checkbox) + 1

        state = checked == 2

        reply = self.multiplexer.set_pin_state(pin_number, state)
        self.status_lineEdit.setText(reply)

        self.update_selected_pins_display()

    def turn_off_all_pins(self):
        """
        Turn all multiplexer pins OFF and clear all checkboxes.

        The Arduino receives the command "off all". The interface then
        updates every checkbox so that it matches the Arduino state.
        """
        reply = self.multiplexer.turn_off_all_pins()

        for checkbox in self.pin_checkboxes:
            # Temporarily block signals while updating the checkboxes from code.
            # This avoids sending unnecessary serial commands when the UI is only being refreshed.
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)

        self.status_lineEdit.setText(reply)
        self.update_selected_pins_display()

    def read_status(self):
        """
        Read the pin states stored by the Arduino and update the interface.
    
        The Arduino returns 25 comma-separated values. Each value is:
    
         - "1" when the pin is ON;
         - "0" when the pin is OFF.
    
         The checkboxes are then checked or unchecked so that the interface
         matches the state stored by the Arduino.
         """
        states = self.multiplexer.read_pin_states()

        for index, state in enumerate(states):
            if index < len(self.pin_checkboxes):
                checkbox = self.pin_checkboxes[index]
                checkbox.blockSignals(True)
                checkbox.setChecked(state == "1")
                checkbox.blockSignals(False)

        self.status_lineEdit.setText("Status updated")
        self.update_selected_pins_display()

    def update_selected_pins_display(self):
        """
        Update the text area containing the currently selected pins.

        Every checked checkbox is added to the displayed list.
        """
        selected_pins = []

        for index, checkbox in enumerate(self.pin_checkboxes):
            if checkbox.isChecked():
                selected_pins.append(f"ch_1_pin_{index + 1:02d}")

        if selected_pins:
            text = "Selected pins:\n" + "\n".join(selected_pins)
        else:
            text = "No pins selected"

        self.selected_pins_plainTextEdit.setPlainText(text)


if __name__ == "__main__":
    multiplexer = ArduinoMultiplexer(port="COM6")

    app = QtWidgets.QApplication(sys.argv)
    window = ArduinoMultiplexerUI(multiplexer)
    window.show()
    app.exec_()

    multiplexer.close()