# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 16:53:20 2023

@author: deankos
"""

from PyQt5 import QtWidgets

class interactive_ui(QtWidgets.QWidget):
    """
    Generic class for interactive ui containing (double)spinbox, lineedit, combobox.
    """
    
    def __init__(self):
        super().__init__()
    
    def connect_widgets_by_name(self):
        """
        Looks for doublespinbox, spinbox, lineedit, combobox, and connects them to attributes.
        Should be called after a ui has been created, for example through uic.loadUi().
        To be found and connected each item must end in: _QItemType. Case insensitive.
        Creates a class attribute with the same name and connects it to the ui item.
        Example: a spinbox called 'counter_spinbox' will create an attribute 'counter' connected to the spinbox.
        connected_widgets is a dictionary of all widget-attribute pairs connected by the method.
        """
        ui_items = {key:value for key, value in vars(self).items() }
        # .items() returns dict view object, so vars(self) needs copying to be modified while iterating
        self.connected_widgets = {}  # dict with widget_item:attr_name pairs to be connected
        for widget_name, widget_item in ui_items.items():
            # check variable names and find those that match QWidget types
            widget_name_parsed = widget_name.rsplit(sep='_', maxsplit=1)
            widget_type = widget_name_parsed[-1].lower()
            if widget_type in ['doublespinbox', 'spinbox', 'lineedit', 'combobox']:
                attr_name = widget_name_parsed[0]
                if widget_type in ['doublespinbox', 'spinbox']:
                    attr_value = widget_item.value()
                    widget_item.valueChanged.connect(self.update_attribute)
                elif widget_type in ['lineedit']:
                    attr_value = widget_item.text()
                    widget_item.textChanged.connect(self.update_attribute)
                elif widget_type in ['combobox']:
                    attr_value = widget_item.currentText()
                    widget_item.currentTextChanged.connect(self.update_attribute)
                setattr(self, attr_name, attr_value)
                self.connected_widgets[widget_item] = attr_name
                
    def update_attribute(self):
        """
        Check sending widget and update corresponding attribute.
        """
        sending_widget = self.sender()
        attr_name = self.connected_widgets[sending_widget]
        if isinstance(sending_widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox) ):
            attr_value = sending_widget.value()
        elif isinstance(sending_widget, QtWidgets.QLineEdit):
            attr_value = sending_widget.text()
        elif isinstance(sending_widget, QtWidgets.QComboBox):
            attr_value = sending_widget.currentText()
        setattr(self, attr_name, attr_value)
            