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
import time
import sys
import serial
from PyQt5 import QtWidgets, uic
from nanomol.instruments import serial_instrument


class SerialInstrument:
    """
    Generic serial communication class.

    It handles serial communication:
    - opening the serial port
    - sending text commands
    - reading Arduino replies
    - closing the connection
    """

    def __init__(self, port, baudrate=115200, timeout=1, termination_character="\n"):
        self.instrument = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )
        self.termination_character = termination_character

        # When Python opens the serial port, Arduino resets.
        # We wait and clear the startup messages from the Arduino.
        time.sleep(2)
        self.instrument.reset_input_buffer()

    def write(self, command):
        """
        Send one command to the Arduino.
    
        The termination character is automatically added because the Arduino
        waits for a newline before processing a complete command.
        """
        message = command + self.termination_character
        self.instrument.write(message.encode())
        self.instrument.flush()

    def read(self):
        """
        Read one complete line returned by the Arduino.
    
        Reading stops when the termination character is received.
    
        """  
        message = self.instrument.read_until(
            expected=self.termination_character.encode()
        )
        return message.decode().strip()

    def query(self, command):
        """
        Send a command and read the corresponding Arduino reply.

        """
        self.write(command)
        return self.read()

    def close(self):
        """
        Close the serial port.

        """
        self.instrument.close()


class ArduinoMultiplexer(SerialInstrument):
    """
    Instrument class for the Arduino-controlled relay multiplexer.

    This class separates the instrument functionality from the user interface.
    It translates Python method calls into Arduino serial commands:
    - on <pin_number>
    - off <pin_number>
    - off all
    - status
    """

    def __init__(self, port):
        super().__init__(
            port=port,
            baudrate=115200,
            timeout=1,
            termination_character="\n"
        )

    def set_pin_state(self, pin_number, state):
        """
        Turn one multiplexer pin ON or OFF
        
        """

        if state:
            command = f"on {pin_number}"
        else:
            command = f"off {pin_number}"

        print("Python sends:", command)

        reply = self.query(command)

        print("Arduino replied:", reply)

        return reply

    def turn_off_all_pins(self):
        """
        Turn all 25 multiplexer pins OFF

        """
        command = "off all"

        print("Python sends:", command)

        reply = self.query(command)

        print("Arduino replied:", reply)

        return reply

    def read_pin_states(self):
        """
        Request the stored state of all 25 pins from the Arduino.

        The Arduino returns one comma-separated value for every pin.

        Example response:

        1,0,0,1,0,...,0

        1 means ON and 0 means OFF.

       """
        command = "status"

        print("Python sends:", command)

        response = self.query(command)

        print("Arduino replied:", response)

        return response.split(",")


class ArduinoMultiplexerUI(QtWidgets.QMainWindow):
    """
    Qt graphical interface for controlling the multiplexer.

    The interface contains:

    - 25 checkboxes representing the 25 multiplexer pins;
    - an "All off" button;
    - a "Read status" button;
    - a status field showing the most recent Arduino reply;
    - a text field listing the currently selected pins.

    Any number of pins from 0 to 25 can remain ON simultaneously.
    """

    def __init__(self, multiplexer):
        super().__init__()
        self.multiplexer = multiplexer

        ui_file_path = os.path.join(
            os.path.dirname(__file__),
            "arduino_multiplexer.ui"
        )
        uic.loadUi(ui_file_path, self)

        self.setWindowTitle("Multiplexer")
        
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