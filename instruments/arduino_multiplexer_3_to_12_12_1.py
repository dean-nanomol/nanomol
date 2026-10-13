# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 16:12:12 2026

@author: deankos
"""

import os
import sys
from PyQt5 import QtWidgets, uic
from nanomol.instruments.serial_instrument import serial_instrument
from nanomol.utils.interactive_ui import interactive_ui

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
        pin_number : int
            pin number to address, 1 to 25
        state : int or bool
            state of the pin (0: OFF, 1: ON)
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
        # Index 0 is pin 1, index 1 is pin 2, ...
        # Connect all checkboxes to pin_state_changed. Checkbox names defined in Qt Designer.
        self.pin_checkboxes = []
        for pin_number in range(1, 26):
            checkbox_name = f'pin_{pin_number:02d}_checkBox'
            checkbox = self.findChild(QtWidgets.QCheckBox, checkbox_name)
            self.pin_checkboxes.append(checkbox)
            checkbox.stateChanged.connect(self.update_pin_state)

        self.off_all_pushButton.clicked.connect(self.off_all)
        self.read_state_pushButton.clicked.connect(self.read_state)

    def update_pin_state(self, checked):
        """
        Update pin state when checkbox is toggled.

        Identifies which checkbox produced the signal, converts its position into a pin number,
        and sends the appropriate ON or OFF command to the Arduino.
        """
        checkbox = self.sender()
        pin_number = self.pin_checkboxes.index(checkbox) + 1
        # checkbox.stateChanged emits 0 if unchecked, 2 if checked
        state = checked == 2
        if state:
            if self.exclusive_mode_checkBox.isChecked():
                self.off_group(checkbox)
        self.multiplexer.set_pin_state(pin_number, state)

    def off_all(self):
        """
        Turn all multiplexer pins OFF and uncheck all checkboxes.
        """
        self.multiplexer.off_all()
        for checkbox in self.pin_checkboxes:
            # Temporarily block signals while updating the checkboxes from code.
            # This avoids sending unnecessary serial commands when the UI is only being refreshed.
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)
            
    def off_group(self, checked_checkbox):
        """
        Uncheck all checkboxes that belong to the same group as checked_checkbox.
        Used to turn off active pins before switching ON a given pin in exclusive mode.
        """
        groupbox = checked_checkbox.parent()
        # turn off all checkboxes in the groupBox other than checked_checkbox
        checkboxes_to_uncheck = groupbox.findChildren(QtWidgets.QCheckBox)
        checkboxes_to_uncheck.remove(checked_checkbox)
        for checkbox in checkboxes_to_uncheck:
            checkbox.setChecked(False)

    def read_state(self):
        """
        Read pin states from Arduino and update state text box.
        Arduino returns a string of 25 digits, each 0 or 1 if pin is OFF or ON.
        """
        state = self.multiplexer.status()
        # add a space every 5 digits for readability
        state = ' '.join(state[i:i+5] for i in range(0, len(state), 5))
        self.state_lineEdit.setText(state)


if __name__ == "__main__":
    multiplexer = arduino_multiplexer_3_to_12_12_1('COM10')

    app = QtWidgets.QApplication(sys.argv)
    window = arduino_multiplexer_3_to_12_12_1_ui(multiplexer)
    window.show()
    app.exec_()

    multiplexer.close()