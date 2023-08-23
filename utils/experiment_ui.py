# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 16:53:20 2023

@author: deankos
"""

from PyQt5 import QtWidgets

class experiment_ui(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
    
    def connect_widgets_by_name(self):
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
                elif widget_type in ['lineedit']:
                    attr_value = widget_item.text()
                elif widget_type in ['combobox']:
                    attr_value = widget_item.currentText()
                setattr(self, attr_name, attr_value)
                self.connected_widgets[widget_item] = attr_name
                widget_item.valueChanged.connect(self.update_attribute)
                
    def update_attribute(self):
        sending_widget = self.sender()
        attr_name = self.connected_widgets[sending_widget]
        if isinstance(sending_widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox) ):
            attr_value = sending_widget.value()
        elif 
        
        setattr(self, attr_name, attr_value)
        print(attr_name, attr_value)
            